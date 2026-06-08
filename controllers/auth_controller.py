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

import base64
import logging
from datetime import datetime, timedelta

import jwt  # Librería para crear y leer tokens JWT
from flask import request, jsonify
from werkzeug.security import generate_password_hash

from config import JWT_SECRET_KEY  # Clave secreta para firmar los tokens
from db import db
from models.user_model import (
    create_usuario,
    find_by_correo,
    find_by_id,
    validate_password,
    verify_password,
)

logger = logging.getLogger(__name__)


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


def _decode_legacy_browser_token(raw: str):
    """
    Soporte para el token "viejo" que genera el frontend con
        btoa(correo + ':' + Date.now())
    Devuelve un dict tipo payload {"correo": "..."} si se puede decodificar,
    o None si no parece ese formato.

    Se mantiene por compatibilidad con la versión anterior del frontend.
    """
    if not raw:
        return None
    try:
        # Padding por si el base64 viene sin "=" al final (lo típico de btoa).
        pad = "=" * (-len(raw) % 4)
        decoded = base64.b64decode(raw + pad).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None

    if ":" not in decoded:
        return None
    correo, _ts = decoded.split(":", 1)
    correo = correo.strip()
    if "@" not in correo:
        return None
    return {"correo": correo}


def decode_token(token):
    """
    Lee y verifica un token. Si es válido, devuelve los datos que tiene
    adentro (payload). Si está vencido o adulterado, devuelve None.

    Acepta dos formatos por compatibilidad:
      1) JWT firmado con JWT_SECRET_KEY (formato actual).
      2) base64(correo:timestamp) que genera el frontend antiguo.
    """
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        # Si no es JWT válido, probamos el formato legacy del frontend.
        return _decode_legacy_browser_token(token)


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

    # Eliminación lógica: un usuario desactivado no puede iniciar sesión.
    if getattr(user, "activo", True) is False:
        return jsonify({"error": "Tu cuenta está desactivada. Contacta al administrador."}), 403

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
    token = auth_header.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if payload is None:
        return jsonify({"error": "Token inválido o expirado"}), 401

    # El payload puede traer "user_id" (JWT nuevo) o "correo" (token viejo).
    user = None
    if payload.get("user_id") is not None:
        user = find_by_id(payload["user_id"])
    elif payload.get("correo"):
        user = find_by_correo(payload["correo"])

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    # Devolvemos los datos actualizados del usuario (sin contraseña)
    user_safe = user.to_dict()
    return jsonify(user_safe), 200


# ---------------------------------------------------------------------
# FORGOT: SOLICITAR RECUPERACIÓN DE CONTRASEÑA
# ---------------------------------------------------------------------
# En un MVP sin servicio de correo, devolvemos el token de restablecimiento
# en la respuesta (y lo dejamos en los logs). En producción se enviaría por
# email y NUNCA se devolvería en la respuesta.
def forgot_password():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip()
    if not email:
        return jsonify({"error": "email es requerido"}), 400

    user = find_by_correo(email)
    # Respuesta genérica para no revelar si el correo existe (anti-enumeración).
    generic = {"message": "Si el correo existe, se enviaron instrucciones de recuperación."}

    if not user:
        return jsonify(generic), 200

    reset_token = jwt.encode(
        {
            "user_id": user.id_usuario,
            "purpose": "reset",
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        JWT_SECRET_KEY,
        algorithm="HS256",
    )
    logger.info("Token de reseteo para %s: %s", email, reset_token)
    # MVP/dev: incluimos el token para poder probar el flujo sin email real.
    return jsonify({**generic, "resetToken": reset_token}), 200


# ---------------------------------------------------------------------
# RESET: ESTABLECER NUEVA CONTRASEÑA CON EL TOKEN
# ---------------------------------------------------------------------
def reset_password():
    data = request.get_json() or {}
    token = data.get("token") or ""
    new_password = data.get("password") or ""
    if not token or not new_password:
        return jsonify({"error": "token y password son requeridos"}), 400

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        return jsonify({"error": "Token inválido o expirado"}), 401

    if payload.get("purpose") != "reset":
        return jsonify({"error": "Token no válido para esta operación"}), 401

    user = find_by_id(payload.get("user_id"))
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    try:
        # Reutilizamos la validación de fortaleza del modelo (devuelve el hash).
        user.contrasena = validate_password(new_password)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception:
        db.session.rollback()
        return jsonify({"error": "No se pudo actualizar la contraseña"}), 500

    return jsonify({"message": "Contraseña actualizada correctamente"}), 200
