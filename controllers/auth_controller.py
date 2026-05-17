# =====================================================================
# CONTROLADOR DE AUTENTICACIÓN (auth_controller.py)
# ---------------------------------------------------------------------
# Aquí está la lógica para:
#   - Registrar usuarios (signup)
#   - Iniciar sesión (signin) y devolver un TOKEN JWT
#   - Validar que un token JWT sea correcto (validate)
#
# JWT = JSON Web Token. Es un "carnet" digital firmado que el frontend
# guarda y manda en cada petición para demostrar quién es.
# =====================================================================

from datetime import datetime, timedelta

import jwt  # Librería para crear y leer tokens JWT
from flask import request, jsonify
from werkzeug.security import generate_password_hash

from config import JWT_SECRET_KEY  # Clave secreta para firmar los tokens
from db import db
from models.user_model import create_usuario, find_by_correo, find_by_id, verify_password


# ---------------------------------------------------------------------
# HELPERS PARA JWT
# ---------------------------------------------------------------------

def create_token(user):
    """
    Crea un token JWT para el usuario. Dentro va su id y una fecha de
    expiración (8 horas a partir de ahora).
    """
    payload = {
        "user_id": user.id_usuario,
        "exp": datetime.utcnow() + timedelta(hours=8),  # caduca en 8 horas
    }
    # Firmamos el token con la clave secreta y el algoritmo HS256
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")


def decode_token(token):
    """
    Lee y verifica un token. Si es válido, devuelve los datos que tiene
    adentro (payload). Si está vencido o adulterado, devuelve None.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        # Cualquier error de JWT (expirado, firma inválida, etc.) lo capturamos
        return None


# ---------------------------------------------------------------------
# SIGNUP: REGISTRO DE NUEVO USUARIO
# ---------------------------------------------------------------------
def signup():
    # request.get_json() lee el cuerpo JSON que mandó el frontend
    data = request.get_json() or {}

    # Verificamos que vengan los campos obligatorios
    required_fields = ["email", "password", "fullName"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"error": "Faltan datos obligatorios: email, password, fullName"}), 400

    # El front manda "fullName" todo junto ("Juan Pérez García") así que
    # lo dividimos en nombre y apellido (último token = apellido).
    full_name_parts = data["fullName"].strip().split()
    if len(full_name_parts) < 2:
        return jsonify({"error": "El nombre completo debe incluir nombre y apellido"}), 400

    nombre = " ".join(full_name_parts[:-1])  # todo menos el último
    apellido = full_name_parts[-1]           # solo el último

    try:
        # Llamamos a la función del modelo que ya hace todas las validaciones
        user = create_usuario(
            nombre=nombre,
            apellido=apellido,
            correo=data["email"],
            telefono=data.get("telefono", ""),  # opcional
            contrasena=data["password"],
            id_rol=data.get("role", "cliente")  # por defecto "cliente"
        )
        # 201 = Created (nuevo recurso creado correctamente)
        return jsonify(user), 201
    except ValueError as e:
        # Si las validaciones fallan, devolvemos 400 con el mensaje de error
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# SIGNIN: INICIO DE SESIÓN
# ---------------------------------------------------------------------
def signin():
    data = request.get_json() or {}

    # Debe venir email y password
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Faltan credenciales"}), 400

    # Buscamos al usuario por correo
    user = find_by_correo(data["email"])
    # Si no existe O la contraseña no coincide, devolvemos 401 (no autorizado)
    if not user or not verify_password(user.contrasena, data["password"]):
        return jsonify({"error": "Credenciales incorrectas"}), 401

    # Pequeño detalle: si el usuario tenía la contraseña SIN hashear en la BD
    # (por algún registro viejo), ahora aprovechamos para hashearla.
    if user.contrasena == data["password"]:
        user.contrasena = generate_password_hash(data["password"])
        db.session.commit()

    # Si todo OK, generamos el token y lo mandamos junto con la info del usuario
    token = create_token(user)
    user_safe = user.to_dict()  # to_dict ya excluye la contraseña
    user_safe["token"] = token
    return jsonify(user_safe), 200


# ---------------------------------------------------------------------
# VALIDATE: VERIFICAR QUE UN TOKEN ES VÁLIDO
# ---------------------------------------------------------------------
# Esta ruta se usa típicamente cuando el front quiere saber si la sesión
# del usuario sigue activa (por ejemplo, al refrescar la página).
def validate():
    # El token llega en la cabecera Authorization: "Bearer <token>"
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token no proporcionado"}), 401

    # Quitamos el prefijo "Bearer " para quedarnos solo con el token
    token = auth_header.split(" ", 1)[1]
    payload = decode_token(token)
    if payload is None:
        return jsonify({"error": "Token inválido o expirado"}), 401

    # Buscamos al usuario con el id que viene dentro del token
    user = find_by_id(payload.get("user_id"))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Devolvemos los datos actualizados del usuario (sin contraseña)
    user_safe = user.to_dict()
    return jsonify(user_safe), 200
