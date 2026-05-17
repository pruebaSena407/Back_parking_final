# =====================================================================
# CONFIGURACIÓN DE VARIABLES DE ENTORNO (config.py)
# ---------------------------------------------------------------------
# Aquí leemos las "variables de entorno" (datos sensibles como
# contraseñas, URL de base de datos, claves secretas). Nunca se ponen
# directamente en el código, sino en un archivo .env que NO se sube a Git.
# =====================================================================

import os
# dotenv permite cargar variables desde el archivo .env automáticamente
from dotenv import load_dotenv

# Lee el archivo .env y mete sus variables en os.environ
load_dotenv()

# URL de conexión a PostgreSQL (la nos da Render cuando creamos la BD).
# Formato típico: postgresql://usuario:contraseña@host:puerto/nombreBD
DATABASE_URL = os.getenv("DATABASE_URL")

# Render entrega la URL con el prefijo legacy "postgres://", pero
# SQLAlchemy 2.x ya no registra ese dialecto y arranca con el error:
#   sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres
# Para evitarlo, normalizamos el esquema a "postgresql://".
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Clave secreta para firmar tokens JWT (autenticación).
# Si no existe JWT_SECRET_KEY, usa SECRET_KEY, y si tampoco, usa "changeme123"
# (esto último es un valor por defecto solo para desarrollo).
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "changeme123"))

# Si la URL de la base de datos no está configurada, detenemos la app
# inmediatamente con un error claro. Sin BD no podemos funcionar.
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no configurado. Agrega DATABASE_URL en Render variables de entorno."
    )
