# =====================================================================
# MIDDLEWARE DE AUTENTICACIÓN (auth_middleware.py)
# ---------------------------------------------------------------------
# Decoradores reutilizables para proteger endpoints HTTP. Lee el header
# `Authorization: Bearer <token>`, valida el JWT (o el token legacy en
# base64) reusando la lógica de `auth_controller.decode_token` y deja el
# usuario actual disponible en `flask.g.current_user`.
# =====================================================================

from functools import wraps

from flask import request, jsonify, g

from controllers.auth_controller import decode_token
from models.user_model import find_by_id, find_by_correo


def _extract_user():
    """Lee Authorization, decodifica el token y devuelve el User o None."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload:
        return None
    if payload.get("user_id") is not None:
        return find_by_id(payload["user_id"])
    if payload.get("correo"):
        return find_by_correo(payload["correo"])
    return None


def require_auth(view):
    """Sólo deja pasar si hay un usuario válido detrás del token."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = _extract_user()
        if not user:
            return jsonify({"error": "No autorizado"}), 401
        g.current_user = user
        return view(*args, **kwargs)

    return wrapper


def require_role(*roles):
    """
    Sólo deja pasar si el usuario autenticado tiene uno de los roles
    indicados. Acepta el rol como nombre (`'admin'`, `'empleado'`, …) y
    también como `id_rol` numérico.
    """
    role_set = {str(r).lower() for r in roles}

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = _extract_user()
            if not user:
                return jsonify({"error": "No autorizado"}), 401
            # to_dict() devuelve "id_rol" como nombre (cliente/admin/...).
            user_role = str(user.to_dict().get("id_rol", "")).lower()
            if user_role not in role_set and str(user.id_rol) not in role_set:
                return jsonify({"error": "Permiso denegado"}), 403
            g.current_user = user
            return view(*args, **kwargs)

        return wrapper

    return decorator
