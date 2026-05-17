"""
Datos mínimos si las tablas de catálogo están vacías (BD nueva en Render, etc.).

Cada función `ensure_*` es IDEMPOTENTE: solo inserta si la tabla está vacía.
Esto permite ejecutar el seed en cada arranque sin duplicar datos.
"""
import logging

from sqlalchemy import text
from werkzeug.security import generate_password_hash

from db import db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# ROLES (admin / cliente / empleado)
# ---------------------------------------------------------------------
def ensure_default_roles() -> bool:
    """
    Si `rol` no tiene filas, inserta admin / cliente / empleado.
    Prueba varias formas según columnas de tu esquema (nombre, descripcion, id fijo).
    """
    try:
        count = db.session.execute(text("SELECT COUNT(*) FROM rol")).scalar()
    except Exception as e:
        logger.warning("No se pudo leer la tabla rol (¿existe?): %s", e)
        return False

    if count is not None and int(count) > 0:
        return True

    attempts = [
        """
        INSERT INTO rol (id_rol, nombre, descripcion) VALUES
        (1, 'admin', 'Administrador'),
        (2, 'cliente', 'Cliente'),
        (3, 'empleado', 'Empleado')
        ON CONFLICT (id_rol) DO NOTHING
        """,
        """
        INSERT INTO rol (id_rol, nombre) VALUES
        (1, 'admin'),
        (2, 'cliente'),
        (3, 'empleado')
        ON CONFLICT (id_rol) DO NOTHING
        """,
        """
        INSERT INTO rol (nombre, descripcion) VALUES
        ('admin', 'Administrador'),
        ('cliente', 'Cliente'),
        ('empleado', 'Empleado')
        """,
        """
        INSERT INTO rol (nombre) VALUES
        ('admin'),
        ('cliente'),
        ('empleado')
        """,
    ]

    for sql in attempts:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            logger.info("Tabla rol estaba vacía: se insertaron roles por defecto.")
            _sync_sequence("rol", "id_rol")
            return True
        except Exception:
            db.session.rollback()

    logger.error(
        "No se pudieron crear roles por defecto. Revisa columnas NOT NULL de public.rol."
    )
    return False


# ---------------------------------------------------------------------
# UTILIDAD: sincroniza la secuencia SERIAL de una tabla tras un INSERT con id fijo
# ---------------------------------------------------------------------
def _sync_sequence(table: str, pk_column: str) -> None:
    try:
        db.session.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', '{pk_column}'), "
            f"(SELECT COALESCE(MAX({pk_column}), 1) FROM {table}))"
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()


# Mantenemos el nombre antiguo por compatibilidad con cualquier import externo.
def _sync_rol_sequence() -> None:
    _sync_sequence("rol", "id_rol")


def _table_is_empty(table: str) -> bool:
    """Devuelve True si la tabla existe y está vacía."""
    try:
        count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        return count is None or int(count) == 0
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudo leer la tabla %s: %s", table, e)
        return False


# ---------------------------------------------------------------------
# UBICACIONES (parqueaderos demo en Bogotá)
# ---------------------------------------------------------------------
def ensure_default_locations() -> None:
    if not _table_is_empty("ubicacion"):
        return
    try:
        db.session.execute(text("""
            INSERT INTO ubicacion (id_ubicacion, nombre, direccion, capacidad, latitud, longitud) VALUES
            (1, 'ParkVista Centro',    'Calle 26 #59-51, Bogotá',     120, 4.6584, -74.0935),
            (2, 'ParkVista Norte',     'Cra 11 #93-46, Bogotá',        80, 4.6760, -74.0480),
            (3, 'ParkVista Salitre',   'Av. El Dorado #68B-31',       150, 4.6586, -74.1057),
            (4, 'ParkVista Chapinero', 'Cra 13 #53-39',                60, 4.6444, -74.0639)
        """))
        db.session.commit()
        _sync_sequence("ubicacion", "id_ubicacion")
        logger.info("Ubicaciones de demo insertadas.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar ubicaciones demo: %s", e)


# ---------------------------------------------------------------------
# TARIFAS
# ---------------------------------------------------------------------
def ensure_default_rates() -> None:
    if not _table_is_empty("tarifa"):
        return
    try:
        db.session.execute(text("""
            INSERT INTO tarifa (id_tarifa, nombre, tarifa_horaria, tarifa_diaria,
                                tarifa_mensual, moneda, tipo_vehiculo, id_ubicacion) VALUES
            (1, 'Estándar Auto',  5000, 25000, 350000, 'COP', 'car',        1),
            (2, 'Estándar Moto',  2500, 12000, 180000, 'COP', 'motorcycle', 1),
            (3, 'Premium Auto',   7000, 35000, 450000, 'COP', 'car',        2),
            (4, 'Camión',        12000, 60000, 800000, 'COP', 'truck',      3),
            (5, 'Bicicleta',      1000,  5000,  60000, 'COP', 'bicycle',    1)
        """))
        db.session.commit()
        _sync_sequence("tarifa", "id_tarifa")
        logger.info("Tarifas de demo insertadas.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar tarifas demo: %s", e)


# ---------------------------------------------------------------------
# USUARIOS (admin + cliente demo)
# ---------------------------------------------------------------------
def _ensure_user(id_usuario, nombre, apellido, correo, telefono, password_plano, rol_nombre):
    """Crea un usuario solo si su correo aún no existe."""
    try:
        existing = db.session.execute(
            text("SELECT 1 FROM usuario WHERE correo = :correo"),
            {"correo": correo},
        ).scalar()
        if existing:
            return
        db.session.execute(
            text("""
                INSERT INTO usuario (id_usuario, nombre, apellido, correo, telefono, contrasena, id_rol)
                VALUES (:id, :nombre, :apellido, :correo, :telefono, :pwd,
                        (SELECT id_rol FROM rol WHERE LOWER(nombre) = LOWER(:rol)))
            """),
            {
                "id": id_usuario,
                "nombre": nombre,
                "apellido": apellido,
                "correo": correo,
                "telefono": telefono,
                "pwd": generate_password_hash(password_plano),
                "rol": rol_nombre,
            },
        )
        db.session.commit()
        logger.info("Usuario demo creado: %s (%s)", correo, rol_nombre)
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudo crear usuario demo %s: %s", correo, e)


def ensure_default_users() -> None:
    """Inserta un admin y un cliente para poder probar la app."""
    _ensure_user(
        id_usuario=1,
        nombre="Admin",
        apellido="ParkVista",
        correo="admin@parkvista.com",
        telefono="3001112222",
        password_plano="Admin123!",
        rol_nombre="admin",
    )
    _ensure_user(
        id_usuario=2,
        nombre="Cliente",
        apellido="Demo",
        correo="cliente@demo.com",
        telefono="3009998888",
        password_plano="Cliente123!",
        rol_nombre="cliente",
    )
    _ensure_user(
        id_usuario=3,
        nombre="Empleado",
        apellido="Demo",
        correo="empleado@parkvista.com",
        telefono="3007776666",
        password_plano="Empleado123!",
        rol_nombre="empleado",
    )
    _sync_sequence("usuario", "id_usuario")


# ---------------------------------------------------------------------
# VEHÍCULOS DEMO (asociables a reservas)
# ---------------------------------------------------------------------
def ensure_default_vehicles() -> None:
    if not _table_is_empty("vehiculo"):
        return
    try:
        db.session.execute(text("""
            INSERT INTO vehiculo (id_vehiculo, placa, tipo, marca, color) VALUES
            (1, 'ABC123', 'car',        'Chevrolet', 'Rojo'),
            (2, 'MOT456', 'motorcycle', 'Yamaha',    'Negro'),
            (3, 'XYZ789', 'car',        'Renault',   'Blanco')
        """))
        db.session.commit()
        _sync_sequence("vehiculo", "id_vehiculo")
        logger.info("Vehículos demo insertados.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar vehículos demo: %s", e)


# ---------------------------------------------------------------------
# PUNTO DE ENTRADA
# ---------------------------------------------------------------------
def ensure_seed_data() -> None:
    """Ejecutar al arrancar la app. Cada paso es independiente y tolerante a fallos."""
    ensure_default_roles()
    ensure_default_locations()
    ensure_default_rates()
    ensure_default_users()
    ensure_default_vehicles()
