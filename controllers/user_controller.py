from flask import request, jsonify
from models.user_model import list_all, find_by_id, create_usuario, update_usuario, delete_usuario


def get_all():
    try:
        users = list_all()
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_by_id(user_id):
    user = find_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200


def create_user():
    data = request.get_json() or {}
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
        return jsonify({"error": str(e)}), 400


def update_user(user_id):
    data = request.get_json() or {}
    allowed = ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]
    updates = {k: v for k, v in data.items() if k in allowed}

    if not updates:
        return jsonify({"error": "No hay campos válidos para actualizar"}), 400

    try:
        user = update_usuario(user_id, updates)
        return jsonify(user), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


def delete_user(user_id):
    try:
        delete_usuario(user_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

