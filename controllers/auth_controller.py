from flask import request, jsonify
from models.user_model import create_usuario, find_by_correo


def signup():
    data = request.get_json() or {}

    if not data.get("email") or not data.get("password") or not data.get("fullName"):
        return jsonify({"error": "Faltan datos (email, password, fullName)"}), 400

    nombre = data["fullName"].split(" ")[0]
    apellido = " ".join(data["fullName"].split(" ")[1:]) or ""

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
    if not user or user.contrasena != data["password"]:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify(user.to_dict()), 200

