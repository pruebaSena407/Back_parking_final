from datetime import datetime, timedelta

import jwt
from flask import request, jsonify
from werkzeug.security import generate_password_hash

from config import JWT_SECRET_KEY
from db import db
from models.user_model import create_usuario, find_by_correo, find_by_id, verify_password


def create_token(user):
    payload = {
        "user_id": user.id_usuario,
        "exp": datetime.utcnow() + timedelta(hours=8),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


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

    # Si el usuario tenía la contraseña almacenada en texto plano,
    # actualizamos el registro a hash para mejorar la seguridad.
    if user.contrasena == data["password"]:
        user.contrasena = generate_password_hash(data["password"])
        db.session.commit()

    token = create_token(user)
    user_safe = user.to_dict()
    user_safe["token"] = token
    return jsonify(user_safe), 200


def validate():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload is None:
        return jsonify({"error": "Token inválido o expirado"}), 401

    user = find_by_id(payload.get("user_id"))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    user_safe = user.to_dict()
    return jsonify(user_safe), 200

