"""
Datos mínimos si las tablas de catálogo están vacías (BD nueva en Render, etc.).

Cada función `ensure_*` es IDEMPOTENTE: solo inserta si la tabla está vacía.
Esto permite ejecutar el seed en cada arranque sin duplicar datos.
"""
import logging
from datetime import date, datetime, time, timedelta

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
def _ensure_user(nombre, apellido, correo, telefono, password_plano, rol_nombre):
    """
    Garantiza que el usuario demo exista y tenga la contraseña/rol esperados.
    - Si no existe: lo crea con id = MAX(id)+1 (evita choques de llave primaria
      cuando la tabla ya tenía filas con id 1, 2, 3 de otro esquema).
    - Si existe: re-sincroniza su contraseña y su rol con los valores demo, para
      que las credenciales documentadas siempre sirvan para entrar.
    """
    try:
        existing_id = db.session.execute(
            text("SELECT id_usuario FROM usuario WHERE correo = :correo"),
            {"correo": correo},
        ).scalar()

        if existing_id:
            db.session.execute(
                text("""
                    UPDATE usuario
                    SET contrasena = :pwd,
                        id_rol = (SELECT id_rol FROM rol WHERE LOWER(nombre) = LOWER(:rol))
                    WHERE id_usuario = :id
                """),
                {"pwd": generate_password_hash(password_plano), "rol": rol_nombre, "id": existing_id},
            )
            db.session.commit()
            logger.info("Usuario demo sincronizado: %s (%s)", correo, rol_nombre)
            return

        next_id = db.session.execute(
            text("SELECT COALESCE(MAX(id_usuario), 0) + 1 FROM usuario")
        ).scalar()
        db.session.execute(
            text("""
                INSERT INTO usuario (id_usuario, nombre, apellido, correo, telefono, contrasena, id_rol)
                VALUES (:id, :nombre, :apellido, :correo, :telefono, :pwd,
                        (SELECT id_rol FROM rol WHERE LOWER(nombre) = LOWER(:rol)))
            """),
            {
                "id": int(next_id),
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
        logger.warning("No se pudo crear/sincronizar usuario demo %s: %s", correo, e)


def ensure_default_users() -> None:
    """Inserta (o re-sincroniza) un admin, un cliente y un empleado demo."""
    _ensure_user(
        nombre="Admin",
        apellido="ParkVista",
        correo="admin@parkvista.com",
        telefono="3001112222",
        password_plano="Admin123!",
        rol_nombre="admin",
    )
    _ensure_user(
        nombre="Cliente",
        apellido="Demo",
        correo="cliente@demo.com",
        telefono="3009998888",
        password_plano="Cliente123!",
        rol_nombre="cliente",
    )
    _ensure_user(
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
# RESERVAS DEMO
# ---------------------------------------------------------------------
def ensure_default_reservations() -> None:
    """Crea reservas variadas (activas, completadas, pendientes) si no hay."""
    if not _table_is_empty("reserva"):
        return
    today = date.today()
    # (offset_dias, id_usuario, id_ubicacion, id_vehiculo, estado, monto, espacio)
    plan = [
        (-20, 2, 1, 1, "completada", 25000, "A-12"),
        (-15, 2, 2, 2, "completada", 12000, "B-03"),
        (-10, 2, 1, 1, "completada", 5000, "A-05"),
        (-7, 2, 3, 3, "completada", 35000, "C-21"),
        (-3, 2, 1, 1, "activa", 5000, "A-08"),
        (-1, 2, 2, 2, "activa", 2500, "B-10"),
        (1, 2, 1, 1, "pendiente", 5000, "A-14"),
        (2, 2, 3, 3, "pendiente", 35000, "C-02"),
    ]
    try:
        for i, (off, u, ub, v, estado, monto, espacio) in enumerate(plan, start=1):
            inicio = datetime.combine(today + timedelta(days=off), time(8, 0))
            fin = inicio + timedelta(hours=4)
            db.session.execute(text(
                """
                INSERT INTO reserva (id_reserva, id_usuario, id_ubicacion, id_vehiculo,
                                     espacio_codigo, hora_inicio, hora_fin, estado, monto)
                VALUES (:id, :u, :ub, :v, :esp, :ini, :fin, :estado, :monto)
                """
            ), {"id": i, "u": u, "ub": ub, "v": v, "esp": espacio,
                "ini": inicio, "fin": fin, "estado": estado, "monto": monto})
        db.session.commit()
        _sync_sequence("reserva", "id_reserva")
        logger.info("Reservas demo insertadas.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar reservas demo: %s", e)


# ---------------------------------------------------------------------
# PAGOS DEMO
# ---------------------------------------------------------------------
def ensure_default_pagos() -> None:
    """Crea pagos completados (incluyendo este mes) para alimentar ingresos."""
    if not _table_is_empty("pago"):
        return
    today = date.today()
    metodos = ["credit_card", "debit_card", "cash", "app"]
    # Pagamos las reservas completadas/activas (ids 1..6).
    plan = [
        (1, 25000, -20), (2, 12000, -15), (3, 5000, -10),
        (4, 35000, -7), (5, 5000, -3), (6, 2500, -1),
    ]
    try:
        for i, (id_reserva, monto, off) in enumerate(plan, start=1):
            fecha_pago = today + timedelta(days=off)
            txid = f"PV-SEED-{i:04d}"
            db.session.execute(text(
                """
                INSERT INTO pago (id_pago, monto, fecha_pago, metodo_pago, id_reserva,
                                  estado, transaccion_id, comprobante_emitido_at)
                VALUES (:id, :monto, :fecha, :metodo, :res, 'completed', :tx, :emit)
                """
            ), {"id": i, "monto": monto, "fecha": fecha_pago,
                "metodo": metodos[i % len(metodos)], "res": id_reserva,
                "tx": txid, "emit": datetime.combine(fecha_pago, time(9, 0))})
        db.session.commit()
        _sync_sequence("pago", "id_pago")
        logger.info("Pagos demo insertados.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar pagos demo: %s", e)


# ---------------------------------------------------------------------
# REGISTROS DEMO (entradas/salidas de vehículos para reportes)
# ---------------------------------------------------------------------
def ensure_default_registros() -> None:
    """Crea entradas/salidas en los últimos 14 días para flujo de vehículos."""
    if not _table_is_empty("registro"):
        return
    today = date.today()
    vehiculos = [1, 2, 3]
    ubicaciones = [1, 2, 3]
    try:
        rid = 1
        for d in range(14, -1, -1):  # de hace 14 días hasta hoy
            fecha = today - timedelta(days=d)
            # 1 a 3 movimientos por día
            for k in range((d % 3) + 1):
                veh = vehiculos[(d + k) % len(vehiculos)]
                ub = ubicaciones[(d + k) % len(ubicaciones)]
                entrada = time(8 + (k * 3) % 10, 0)
                # El último día algunos quedan dentro (sin salida).
                salida = None if (d == 0 and k == 0) else time(min(8 + (k * 3) % 10 + 3, 22), 0)
                db.session.execute(text(
                    """
                    INSERT INTO registro (id_registro, fecha, hora_entrada, hora_salida,
                                          id_usuario, id_vehiculo, id_ubicacion)
                    VALUES (:id, :fecha, :ent, :sal, 2, :veh, :ub)
                    """
                ), {"id": rid, "fecha": fecha, "ent": entrada, "sal": salida,
                    "veh": veh, "ub": ub})
                rid += 1
        db.session.commit()
        _sync_sequence("registro", "id_registro")
        logger.info("Registros demo insertados.")
    except Exception as e:
        db.session.rollback()
        logger.warning("No se pudieron insertar registros demo: %s", e)


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
    ensure_default_reservations()
    ensure_default_pagos()
    ensure_default_registros()
