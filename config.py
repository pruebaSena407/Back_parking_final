import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL DATABASE_URL de Render
# Formato: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy 2.x: dialecto "postgres" no existe; Render a veces usa postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Driver psycopg v3 (evita psycopg2-binary roto en Python 3.14+ en Render)
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    if not DATABASE_URL.startswith("postgresql+psycopg"):
        DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL.removeprefix("postgresql://")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no configurado. Agrega DATABASE_URL en Render variables de entorno."
    )
