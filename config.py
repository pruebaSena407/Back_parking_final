import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL DATABASE_URL de Render
# Formato: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy 2.x no registra el dialecto "postgres"; Render suele entregar postgres://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no configurado. Agrega DATABASE_URL en Render variables de entorno."
    )
