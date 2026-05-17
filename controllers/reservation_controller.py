# =====================================================================
# CONTROLADOR DE RESERVAS (reservation_controller.py)
# ---------------------------------------------------------------------
# Cada función aquí es el "puente" entre las rutas (HTTP) y el modelo
# (la base de datos). Recibe la petición del front, valida lo mínimo,
# llama al modelo y devuelve la respuesta JSON.
# =====================================================================

from flask import request, jsonify
# Importamos solo las funciones que vamos a usar del modelo
from models.reservation_model import (
    list_all,
    list_by_user,
    create,
    update,
    delete
)


# ---------------------------------------------------------------------
# GET /api/reservations → lista TODAS las reservas
# ---------------------------------------------------------------------
def get_all():
    # Devuelve { "reservations": [...] } con código 200 (OK)
    return jsonify({"reservations": list_all()}), 200


# ---------------------------------------------------------------------
# GET /api/reservations/user/<id> → reservas de UN usuario
# ---------------------------------------------------------------------
def get_by_user(user_id):
    result = list_by_user(user_id)
    return jsonify({"reservations": result}), 200


# ---------------------------------------------------------------------
# POST /api/reservations → crear una reserva nueva
# ---------------------------------------------------------------------
def create_reservation():
    # Leemos los datos JSON que mandó el frontend
    data = request.get_json()

    # Validación rápida: los 4 campos obligatorios deben venir
    if not data or not data.get("userId") or not data.get("locationName") or not data.get("startTime") or not data.get("endTime"):
        return jsonify({"error": "Datos mínimos faltantes (userId, locationName, startTime, endTime)"}), 400

    try:
        # Pasamos los datos al modelo. .get() con None por defecto evita
        # errores si los campos opcionales no vienen.
        reservation = create(
            user_id=data["userId"],
            location_name=data["locationName"],
            start_time=data["startTime"],
            end_time=data["endTime"],
            space_code=data.get("spaceCode"),
            amount=data.get("amount"),
            notes=data.get("notes")
        )
        # 201 = Created (recurso creado)
        return jsonify({"reservation": reservation}), 201
    except Exception as e:
        # Si algo salió mal, devolvemos 400 con el mensaje
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# PUT /api/reservations/<id> → actualizar una reserva
# ---------------------------------------------------------------------
def update_reservation(reservation_id):
    data = request.get_json()

    try:
        reservation = update(reservation_id, data)
        return jsonify({"reservation": reservation}), 200
    except ValueError as e:
        # ValueError lo lanza el modelo cuando NO encuentra la reserva → 404
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        # Cualquier otro error → 400
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# DELETE /api/reservations/<id> → eliminar reserva
# ---------------------------------------------------------------------
def delete_reservation(reservation_id):
    try:
        delete(reservation_id)
        # 204 = No Content. No devolvemos cuerpo, solo confirmamos el borrado.
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
