# =====================================================================
# RUTAS DE AUTENTICACIÓN (auth_routes.py)
# ---------------------------------------------------------------------
# Aquí definimos las URLs del módulo de autenticación. Cada ruta llama
# a la función correspondiente del controlador.
#
# Como en app.py registramos este blueprint con prefix "/api/auth",
# las rutas finales son:
#   POST /api/auth/signup    → registrar
#   POST /api/auth/signin    → iniciar sesión
#   GET  /api/auth/validate  → verificar token
# =====================================================================

from flask import Blueprint
from controllers.auth_controller import signup, signin, validate

# Un Blueprint es como un "mini-app" que agrupa rutas relacionadas
auth_bp = Blueprint("auth", __name__)


# POST → Registro de usuario
@auth_bp.route("/signup", methods=["POST"])
def auth_signup():
    return signup()


# POST → Login. Devuelve token JWT si las credenciales son válidas.
@auth_bp.route("/signin", methods=["POST"])
def auth_signin():
    return signin()


# GET → Verifica que el token enviado en la cabecera siga siendo válido.
@auth_bp.route("/validate", methods=["GET"])
def auth_validate():
    return validate()
