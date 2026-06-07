# =====================================================================
# SCRIPT PARA CREAR / ASCENDER UN ADMINISTRADOR (create_admin.py)
# ---------------------------------------------------------------------
# Resuelve el problema "huevo-gallina": POST /api/users exige ser admin,
# y signup siempre crea clientes. Este script crea (o asciende) un usuario
# con rol 'admin' directamente contra la base de datos.
#
# USO:
#   python create_admin.py correo contraseña "Nombre Apellido" [telefono]
#
# Ejemplo:
#   python create_admin.py jefe@parkvista.com Clave123! "Ana Gómez" 3001234567
# =====================================================================

import sys

from flask import Flask

from config import DATABASE_URL
from db import db


def _build_app() -> Flask:
    """Crea una app mínima de Flask sólo para tener contexto de BD."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}
    db.init_app(app)
    return app


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        print("ERROR: faltan argumentos. Uso: "
              'python create_admin.py correo contraseña "Nombre Apellido" [telefono]')
        sys.exit(1)

    correo = sys.argv[1].strip()
    contrasena = sys.argv[2]
    full_name = sys.argv[3].strip()
    telefono = sys.argv[4].strip() if len(sys.argv) > 4 else ""

    parts = full_name.split()
    if len(parts) < 2:
        print('ERROR: el nombre completo debe incluir nombre y apellido, ej: "Ana Gómez"')
        sys.exit(1)
    nombre = " ".join(parts[:-1])
    apellido = parts[-1]

    app = _build_app()
    with app.app_context():
        # Importamos aquí para que los modelos se registren con la app ya creada.
        from models.user_model import (
            create_usuario,
            find_by_correo,
            resolve_id_rol_db,
            update_usuario,
        )

        existing = find_by_correo(correo)
        if existing:
            # Ya existe: lo ascendemos a admin.
            update_usuario(existing.id_usuario, {"id_rol": "admin"})
            print(f"OK: el usuario {correo} ahora tiene rol 'admin'.")
            return

        try:
            user = create_usuario(
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                telefono=telefono,
                contrasena=contrasena,
                id_rol="admin",
            )
            print(f"OK: administrador creado -> {user['correo']} (id {user['id_usuario']}).")
        except ValueError as e:
            print(f"ERROR: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
