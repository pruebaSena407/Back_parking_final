from flask import request, jsonify
from models.user_model import create_usuario, find_by_correo, verify_password


def signup():
    data = request.get_json() or {}

    required_fields = ["email", "password", "fullName"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "Faltan datos obligatorios: email, password, fullName"}), 400

    # Validate fullName has at least two parts
    full_name_parts = data["fullName"].strip().split()
    if len(full_name_parts) < 2:
        return jsonify({"error": "El nombre completo debe incluir nombre y apellido"}), 400

    nombre = " ".join(full_name_parts[:-1])
    apellido = full_name_parts[-1]

    try:
        user = create_usuario(
            nombre=nombre,
            apellido=apellido,
            correo=data["email"],
            telefono=data.get("telefono", ""),
            contrasena=data["password"],
            id_rol=data.get("role", "cliente")
        )
        return jsonify(user), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def signin():
    data = request.get_json() or {}

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Faltan credenciales"}), 400

    user = find_by_correo(data["email"])
    if not user or not verify_password(user.contrasena, data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    user_safe = user.to_dict()
    return jsonify(user_safe), 200

