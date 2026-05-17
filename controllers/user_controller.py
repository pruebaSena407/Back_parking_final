# =====================================================================
# CONTROLADOR DE USUARIOS (user_controller.py)
# ---------------------------------------------------------------------
# Funciones que el blueprint user_routes va a ejecutar. Cada una
# corresponde a una operación CRUD sobre los usuarios.
# =====================================================================

from flask import request, jsonify
from models.user_model import list_all, find_by_id, create_usuario, update_usuario, delete_usuario


# ---------------------------------------------------------------------
# GET /api/users → lista todos los usuarios
# ---------------------------------------------------------------------
def get_all():
    try:
        users = list_all()
        return jsonify(users), 200
    except Exception as e:
        # 500 = error interno del servidor (algo raro pasó con la BD)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# GET /api/users/<id> → un usuario específico
# ---------------------------------------------------------------------
def get_by_id(user_id):
    user = find_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    # to_dict() en el modelo ya quita la contraseña del JSON
    return jsonify(user), 200


# ---------------------------------------------------------------------
# POST /api/users → crear usuario (modo administrador, con todos los campos)
# ---------------------------------------------------------------------
def create_user():
    data = request.get_json() or {}
    # Listamos los campos obligatorios y buscamos cuáles faltan
    required = ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]
    missing = [field for field in required if field not in data]
    if missing:
        return jsonify({"error": f"Faltan datos: {', '.join(missing)}"}), 400

    try:
        user = create_usuario(
            nombre=data["nombre"],
            apellido=data["apellido"],
            correo=data["correo"],
            telefono=data["telefono"],
            contrasena=data["contrasena"],
            id_rol=data["id_rol"],
        )
        return jsonify(user), 201
    except ValueError as e:
        # Las validaciones del modelo lanzan ValueError
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# PUT /api/users/<id> → actualizar usuario
# ---------------------------------------------------------------------
def update_user(user_id):
    data = request.get_json() or {}
    # Solo dejamos pasar los campos permitidos (whitelist por seguridad)
    allowed = ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]
    updates = {k: v for k, v in data.items() if k in allowed}

    # Si después de filtrar no quedó nada, no hay nada que actualizar
    if not updates:
        return jsonify({"error": "No hay campos válidos para actualizar"}), 400

    try:
        user = update_usuario(user_id, updates)
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ---------------------------------------------------------------------
# DELETE /api/users/<id> → eliminar usuario
# ---------------------------------------------------------------------
def delete_user(user_id):
    try:
        delete_usuario(user_id)
        return "", 204  # 204 = OK sin contenido
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
