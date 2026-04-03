"""
Datos mínimos si las tablas de catálogo están vacías (BD nueva en Render, etc.).
"""
import logging

from sqlalchemy import text

from db import db

logger = logging.getLogger(__name__)


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
            _sync_rol_sequence()
            return True
        except Exception:
            db.session.rollback()

    logger.error(
        "No se pudieron crear roles por defecto. Revisa columnas NOT NULL de public.rol."
    )
    return False


def _sync_rol_sequence() -> None:
    """Tras INSERT con id_rol fijos, ajusta la secuencia SERIAL en PostgreSQL."""
    try:
        db.session.execute(
            text(
                "SELECT setval(pg_get_serial_sequence('rol', 'id_rol'), "
                "(SELECT COALESCE(MAX(id_rol), 1) FROM rol))"
            )
        )
        db.session.commit()
    except Exception:
        db.session.rollback()


def ensure_seed_data() -> None:
    """Ejecutar al arrancar la app."""
    ensure_default_roles()
