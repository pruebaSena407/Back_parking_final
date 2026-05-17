# =====================================================================
# ARCHIVO PRINCIPAL DEL BACKEND (app.py)
# ---------------------------------------------------------------------
# Este es el "punto de entrada" de la aplicación. Cuando se ejecuta este
# archivo (python app.py), se crea el servidor Flask, se conecta con la
# base de datos y se registran todas las rutas (endpoints) que el front
# va a consumir.
# =====================================================================

import logging
import sys
import traceback

# Importamos Flask (para crear el servidor) y jsonify (para devolver
# respuestas en formato JSON, que es lo que entiende el frontend).
from flask import Flask, jsonify
# CORS permite que el frontend (que corre en otro puerto/dominio)
# pueda hacer peticiones a este backend sin que el navegador lo bloquee.
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

# En Render, si la app revienta en el arranque, gunicorn solo dice
# "Exited with status 1" sin mostrar el traceback de Python. Forzamos
# el logging al stdout para que la traza salga en los logs del servicio.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

# Traemos la URL de la base de datos desde config.py (donde se lee del .env)
from config import DATABASE_URL
# db es la instancia de SQLAlchemy (el ORM que usamos para hablar con Postgres)
from db import db

# Importamos los "blueprints" (grupos de rutas). Cada blueprint agrupa los
# endpoints de un tema: autenticación, reservas, ubicaciones, etc.
from routes.auth_routes import auth_bp
from routes.reservation_routes import reservation_bp
from routes.location_routes import location_bp
from routes.rate_routes import rate_bp
from routes.user_routes import user_bp
from routes.stats_routes import stats_bp
from routes.pago_routes import pago_bp
from routes.incidente_routes import incidente_bp
from routes.objeto_olvidado_routes import objeto_olvidado_bp
from routes.reports_routes import reports_bp
from routes.frequent_user_routes import frequent_user_bp

# ---------------------------------------------------------------------
# CONFIGURACIÓN DEL SERVIDOR FLASK
# ---------------------------------------------------------------------
app = Flask(__name__)  # Creamos la app de Flask

# Le decimos a SQLAlchemy qué base de datos usar (postgres en Render).
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
# Desactivamos el "track modifications" porque consume recursos y no lo necesitamos.
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# pool_pre_ping evita errores cuando la conexión a la BD se queda "dormida"
# (muy útil en servicios gratuitos tipo Render).
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

# Inicializamos la base de datos con la app de Flask.
db.init_app(app)

# ---------------------------------------------------------------------
# CREAR TABLAS Y SEMBRAR DATOS INICIALES
# ---------------------------------------------------------------------
# app_context() es necesario para poder usar db.create_all() fuera de una ruta.
# Envolvemos en try/except para que, si la conexión a la BD falla en el
# arranque, gunicorn imprima el traceback en los logs en vez de morir mudo.
with app.app_context():
    try:
        db.create_all()  # Crea las tablas que aún no existan en la BD

        # ----- Migraciones idempotentes (ALTER TABLE) -----
        # Estas líneas añaden columnas nuevas que el código actual usa
        # pero que pueden no existir en bases de datos antiguas. Si la
        # columna ya existe, IF NOT EXISTS la ignora silenciosamente.
        # Lista exhaustiva: cada columna que el ORM declara ahora se
        # asegura por medio de un ADD COLUMN IF NOT EXISTS. Si la tabla
        # vieja no la tenía, queda añadida; si ya existía, no pasa nada.
        # Esto cubre el caso de bases de datos creadas con esquemas
        # anteriores donde p.ej. la tabla reserva no tenía id_usuario.
        migrations = [
            # -------- reserva --------
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS id_usuario INTEGER",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS id_ubicacion INTEGER",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS id_vehiculo INTEGER",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS espacio_codigo VARCHAR(50)",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS hora_inicio TIMESTAMP",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS hora_fin TIMESTAMP",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS estado VARCHAR(50) DEFAULT 'activa'",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS monto DOUBLE PRECISION",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS notas VARCHAR(500)",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            # FKs (se intentan crear, ignoramos si ya existen)
            "ALTER TABLE reserva ADD CONSTRAINT reserva_id_usuario_fk FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)",
            "ALTER TABLE reserva ADD CONSTRAINT reserva_id_ubicacion_fk FOREIGN KEY (id_ubicacion) REFERENCES ubicacion(id_ubicacion)",
            "ALTER TABLE reserva ADD CONSTRAINT reserva_id_vehiculo_fk FOREIGN KEY (id_vehiculo) REFERENCES vehiculo(id_vehiculo)",
            # Relajamos NOT NULL por si la tabla vieja los tenía
            "ALTER TABLE reserva ALTER COLUMN id_vehiculo DROP NOT NULL",
            # -------- tarifa --------
            "ALTER TABLE tarifa ADD COLUMN IF NOT EXISTS tarifa_mensual DOUBLE PRECISION",
            "ALTER TABLE tarifa ADD COLUMN IF NOT EXISTS moneda VARCHAR(10) DEFAULT 'COP'",
            "ALTER TABLE tarifa ADD COLUMN IF NOT EXISTS id_ubicacion INTEGER",
            "ALTER TABLE tarifa ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE tarifa ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE tarifa ADD CONSTRAINT tarifa_id_ubicacion_fk FOREIGN KEY (id_ubicacion) REFERENCES ubicacion(id_ubicacion)",
            # -------- pago --------
            "ALTER TABLE pago ADD COLUMN IF NOT EXISTS estado VARCHAR(20) DEFAULT 'completed'",
            "ALTER TABLE pago ADD COLUMN IF NOT EXISTS transaccion_id VARCHAR(64)",
            "ALTER TABLE pago ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE pago ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE pago ADD COLUMN IF NOT EXISTS id_reserva INTEGER",
            "ALTER TABLE pago ADD CONSTRAINT pago_id_reserva_fk FOREIGN KEY (id_reserva) REFERENCES reserva(id_reserva)",
            "ALTER TABLE pago ALTER COLUMN id_registro DROP NOT NULL",
            # -------- vehiculo --------
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS marca VARCHAR(100)",
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS color VARCHAR(50)",
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE vehiculo ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            # -------- ubicacion --------
            "ALTER TABLE ubicacion ADD COLUMN IF NOT EXISTS latitud DOUBLE PRECISION",
            "ALTER TABLE ubicacion ADD COLUMN IF NOT EXISTS longitud DOUBLE PRECISION",
            "ALTER TABLE ubicacion ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE ubicacion ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            # -------- usuario --------
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS telefono VARCHAR(20)",
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ]
        for stmt in migrations:
            try:
                db.session.execute(db.text(stmt))
                db.session.commit()
            except Exception as alter_exc:
                db.session.rollback()
                logging.warning("Migración idempotente falló (%s): %s", stmt, alter_exc)

        from seed_db import ensure_seed_data

        # Esta función inserta datos iniciales (roles, permisos, etc.)
        # solo si todavía no están en la BD.
        ensure_seed_data()
    except Exception as exc:
        logging.error("Fallo al inicializar la base de datos: %s", exc)
        traceback.print_exc()
        raise

# Habilitamos CORS para que el frontend pueda llamar a este backend.
CORS(app)

# ---------------------------------------------------------------------
# REGISTRO DE BLUEPRINTS (RUTAS DEL API)
# ---------------------------------------------------------------------
# Cada blueprint se registra con un prefijo de URL. Por ejemplo,
# /api/auth/login será atendida por el blueprint auth_bp.
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(reservation_bp, url_prefix="/api/reservations")
app.register_blueprint(location_bp, url_prefix="/api/locations")
app.register_blueprint(rate_bp, url_prefix="/api/rates")
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(stats_bp, url_prefix="/api/stats")
app.register_blueprint(pago_bp, url_prefix="/api/pagos")
app.register_blueprint(incidente_bp, url_prefix="/api/incidentes")
app.register_blueprint(objeto_olvidado_bp, url_prefix="/api/objetos-olvidados")
app.register_blueprint(reports_bp, url_prefix="/api/reports")
app.register_blueprint(frequent_user_bp, url_prefix="/api/frequent-users")

# ---------------------------------------------------------------------
# RUTA DE PRUEBA: VERIFICA QUE LA BASE DE DATOS RESPONDE
# ---------------------------------------------------------------------
# Esta ruta sirve para diagnosticar si la conexión con Postgres está OK.
# Hace un SELECT 1 (consulta básica) y cuenta los usuarios.
@app.route('/api/db-test', methods=['GET'])
def db_test():
    try:
        # Abrimos una conexión directa al motor de SQLAlchemy
        with db.engine.connect() as conn:
            ping = conn.execute(db.text("SELECT 1")).scalar()  # Debería devolver 1
            db_name = conn.execute(db.text("SELECT current_database()")).scalar()
            user_count = conn.execute(db.text("SELECT COUNT(*) FROM usuario")).scalar()
        # Si todo sale bien devolvemos un JSON con la info
        return jsonify(
            {
                "ok": True,
                "select_1": ping,
                "current_database": db_name,
                "usuario_count": int(user_count),
                "hint": "Tabla de usuarios: public.usuario (singular). Si antes existía public.usuarios, era otra tabla; migra datos con SQL si hace falta.",
            }
        ), 200
    except Exception as e:
        # Si algo falla, devolvemos el error en formato JSON con código 500
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------
# RUTA DE DIAGNÓSTICO DEL ESQUEMA
# ---------------------------------------------------------------------
# Devuelve para cada tabla relevante:
#   - Cuántas filas tiene
#   - Qué columnas existen físicamente (con su tipo y si admite NULL)
# Útil para confirmar que las migraciones idempotentes se aplicaron.
@app.route('/api/db-schema', methods=['GET'])
def db_schema():
    tables = ["usuario", "rol", "ubicacion", "tarifa", "vehiculo", "reserva", "pago", "cliente_frecuente"]
    result = {}
    try:
        with db.engine.connect() as conn:
            for table in tables:
                try:
                    cols = conn.execute(db.text(
                        """
                        SELECT column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :t
                        ORDER BY ordinal_position
                        """
                    ), {"t": table}).fetchall()
                    if not cols:
                        result[table] = {"exists": False}
                        continue
                    count = conn.execute(db.text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    result[table] = {
                        "exists": True,
                        "rowCount": int(count or 0),
                        "columns": [
                            {"name": c.column_name, "type": c.data_type, "nullable": c.is_nullable == "YES"}
                            for c in cols
                        ],
                    }
                except Exception as inner:
                    result[table] = {"exists": False, "error": str(inner)}
        return jsonify({"ok": True, "schema": result}), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ---------------------------------------------------------------------
# RUTA HOME ("/"): solo muestra un mensaje de bienvenida del API
# ---------------------------------------------------------------------
@app.route("/", methods=["GET"])
def home():
    return {
        "title": "ParkVista Backend MVC",
        "version": "0.1.0",
        "message": "API disponible en /api/auth, /api/reservations, /api/locations, /api/rates, /api/users, /api/stats"
    }

# ---------------------------------------------------------------------
# MANEJADOR DE ERROR 404
# ---------------------------------------------------------------------
# Si alguien pide una ruta que no existe, en vez de la página fea de
# Flask, devolvemos un JSON limpio con el mensaje de error.
@app.errorhandler(404)
def not_found(error):
    return {"error": "Ruta no encontrada"}, 404

# ---------------------------------------------------------------------
# ARRANQUE DEL SERVIDOR
# ---------------------------------------------------------------------
# Solo corre el servidor si ejecutamos este archivo directamente.
# debug=True recarga automáticamente cuando cambiamos el código.
# port=4000 es el puerto donde escuchará las peticiones.
if __name__ == "__main__":
    app.run(debug=True, port=4000)
