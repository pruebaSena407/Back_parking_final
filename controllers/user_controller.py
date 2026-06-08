# =====================================================================
# CONTROLADOR DE USUARIOS (user_controller.py)
# ---------------------------------------------------------------------
# Endpoints CRUD de /api/users. A diferencia de /api/auth (que mantiene
# el formato "legacy" con id_usuario/correo/etc para compatibilidad con
# el AuthService del front), aquí devolvemos el contrato camelCase que
# `Front_parking_final/src/services/userService.ts` ya tiene tipado.
# =====================================================================

import logging
import traceback

from flask import g, jsonify, request

from controllers.auth_middleware import require_auth, require_role
from db import db
from models.user_model import (
    create_usuario,
    delete_usuario,
    find_by_id,
    list_all,
    set_activo,
    update_usuario,
)

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en usuarios (%s): %s", action, exc)
    traceback.print_exc()


def _split_full_name(full_name: str):
    """Convierte 'Juan Pérez García' en (nombre='Juan Pérez', apellido='García')."""
    parts = (full_name or "").strip().split()
    if len(parts) < 2:
        raise ValueError("El nombre completo debe incluir nombre y apellido")
    return " ".join(parts[:-1]), parts[-1]


def _to_front(user_dict):
    """
    Adapta el dict legacy ({id_usuario, correo, nombre, apellido, ...})
    al contrato del front ({id, email, firstName, lastName, role, ...}).
    """
    if not user_dict:
        return None
    return {
        "id": str(user_dict.get("id_usuario")) if user_dict.get("id_usuario") is not None else None,
        "email": user_dict.get("correo"),
        "firstName": user_dict.get("nombre"),
        "lastName": user_dict.get("apellido"),
        "phone": user_dict.get("telefono"),
        "role": user_dict.get("id_rol"),  # to_dict() ya devuelve el NOMBRE del rol
        "active": user_dict.get("activo", True),
        "createdAt": user_dict.get("created_at"),
        "updatedAt": user_dict.get("updated_at"),
    }


# ---------------------------------------------------------------------
# GET /api/users → lista de usuarios (sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def get_all():
    try:
        return jsonify([_to_front(u) for u in list_all()]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# GET /api/users/profile → datos del usuario autenticado
# ---------------------------------------------------------------------
@require_auth
def get_profile():
    return jsonify(_to_front(g.current_user.to_dict())), 200


# ---------------------------------------------------------------------
# GET /api/users/<id> → un usuario (sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def get_by_id(user_id):
    user = find_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(_to_front(user.to_dict())), 200


# ---------------------------------------------------------------------
# POST /api/users → crear usuario (sólo admin) [empleados o nuevos clientes]
# ---------------------------------------------------------------------
@require_role("admin")
def create_user():
    data = request.get_json() or {}
    # Aceptamos camelCase del front y los nombres internos.
    full_name = data.get("fullName")
    email = data.get("email") or data.get("correo")
    password = data.get("password") or data.get("contrasena")
    role = data.get("role") or data.get("id_rol") or "cliente"
    phone = data.get("phone") or data.get("telefono") or ""
    nombre = data.get("firstName") or data.get("nombre")
    apellido = data.get("lastName") or data.get("apellido")

    try:
        if not nombre or not apellido:
            if not full_name:
                return jsonify({"error": "Faltan datos: fullName o firstName/lastName"}), 400
            nombre, apellido = _split_full_name(full_name)
        if not email or not password:
            return jsonify({"error": "Faltan datos: email, password"}), 400

        user = create_usuario(
            nombre=nombre,
            apellido=apellido,
            correo=email,
            telefono=phone,
            contrasena=password,
            id_rol=role,
        )
        return jsonify(_to_front(user)), 201
    except ValueError as e:
        _handle_db_error("create (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        _handle_db_error("create", e)
        return jsonify({"error": f"Error guardando usuario: {e}"}), 500


# ---------------------------------------------------------------------
# PUT /api/users/<id> → actualizar usuario (sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def update_user(user_id):
    data = request.get_json() or {}
    # Importante: NO se permite cambiar la contraseña por aquí; eso pasa
    # por un endpoint específico de auth. Esto evita guardar plaintext.
    field_map = {
        "firstName": "nombre",
        "nombre": "nombre",
        "lastName": "apellido",
        "apellido": "apellido",
        "email": "correo",
        "correo": "correo",
        "phone": "telefono",
        "telefono": "telefono",
        "role": "id_rol",
        "id_rol": "id_rol",
    }
    updates = {field_map[k]: v for k, v in data.items() if k in field_map}
    if not updates:
        return jsonify({"error": "No hay campos válidos para actualizar"}), 400

    try:
        user = update_usuario(user_id, updates)
        return jsonify(_to_front(user)), 200
    except ValueError as e:
        _handle_db_error("update (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update", e)
        return jsonify({"error": f"Error actualizando usuario: {e}"}), 500


# ---------------------------------------------------------------------
# PUT /api/users/<id>/role → cambia el rol (sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def update_user_role(user_id):
    data = request.get_json() or {}
    role = data.get("role") or data.get("id_rol")
    if not role:
        return jsonify({"error": "role es requerido"}), 400
    try:
        user = update_usuario(user_id, {"id_rol": role})
        return jsonify(_to_front(user)), 200
    except ValueError as e:
        _handle_db_error("update_role (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update_role", e)
        return jsonify({"error": f"Error actualizando rol: {e}"}), 500


# ---------------------------------------------------------------------
# DELETE /api/users/<id> → ELIMINACIÓN LÓGICA (desactiva, sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def delete_user(user_id):
    try:
        # No borra el registro: lo marca como inactivo.
        user = delete_usuario(user_id)
        return jsonify(_to_front(user)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("delete", e)
        return jsonify({"error": f"Error desactivando usuario: {e}"}), 500


# ---------------------------------------------------------------------
# PUT /api/users/<id>/status → activar/desactivar (sólo admin)
# ---------------------------------------------------------------------
@require_role("admin")
def update_user_status(user_id):
    data = request.get_json() or {}
    active = data.get("active")
    if active is None:
        return jsonify({"error": "Falta el campo 'active' (true/false)"}), 400

    # Evita que un admin se desactive a sí mismo y se quede fuera.
    if not active and str(g.current_user.id_usuario) == str(user_id):
        return jsonify({"error": "No puedes desactivar tu propia cuenta"}), 400

    try:
        user = set_activo(user_id, bool(active))
        return jsonify(_to_front(user)), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update_status", e)
        return jsonify({"error": f"Error actualizando estado: {e}"}), 500
