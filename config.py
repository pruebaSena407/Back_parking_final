import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Si ya tienes el URI completo (recomendado):
# mysql://usuario:contraseña@host:puerto/dbname?ssl_ca=/path/to/ca.pem
# HOST AIVEN incluye ssl-mode=REQUIRED como en tu captura.

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    user = os.getenv("DB_USER", "avadmin")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "")
    port = os.getenv("DB_PORT", "")
    dbname = os.getenv("DB_NAME", "defaultdb")
    ssl_mode = os.getenv("DB_SSL_MODE", "REQUIRED")
    ca_path = os.getenv("DB_SSL_CA", "")

    passwd = quote_plus(password)
    parts = [f"mysql+pymysql://{user}:{passwd}@{host}:{port}/{dbname}"]
    params = []
    if ssl_mode:
        params.append(f"ssl_mode={ssl_mode}")
    if ca_path:
        params.append(f"ssl_ca={ca_path}")

    if params:
        DATABASE_URL = parts[0] + "?" + "&".join(params)

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL no configurado. Define DATABASE_URL o las variables DB_*")
