import os
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL DATABASE_URL de Render
# Formato: postgresql://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no configurado. Agrega DATABASE_URL en Render variables de entorno."
    )
