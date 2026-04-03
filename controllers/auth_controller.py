import base64
from typing import Optional

from flask import request, jsonify
from sqlalchemy.exc import IntegrityError

from db import db
from models.user_model import create_usuario, find_by_correo


def _decode_browser_token(raw: str) -> Optional[str]:
    """Decodifica el token que el front genera con btoa('correo:timestamp')."""
    if not raw:
        return None
    try:
        pad = "=" * (-len(raw) % 4)
        return base64.b64decode(raw + pad).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None


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
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Correo ya registrado o datos que no cumplen la base de datos"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


def signin():
    data = request.get_json() or {}

    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Faltan credenciales"}), 400

    user = find_by_correo(data["email"])
    if not user or user.contrasena != data["password"]:
        return jsonify({"error": "Credenciales incorrectas"}), 401

    return jsonify(user.to_dict()), 200


def validate():
    """Valida Authorization: Bearer <base64(correo:timestamp)> generado en el cliente."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token requerido"}), 401

    token = auth_header[7:].strip()
    payload = _decode_browser_token(token)
    if not payload or ":" not in payload:
        return jsonify({"error": "Token inválido"}), 401

    email, _ = payload.split(":", 1)
    user = find_by_correo(email.strip())
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 401

    return jsonify(
        {"ok": True, "correo": user.correo, "id_rol": user.to_dict()["id_rol"]}
    ), 200

