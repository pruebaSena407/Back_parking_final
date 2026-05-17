# =====================================================================
# CONTROLADOR DE RESERVAS (reservation_controller.py)
# ---------------------------------------------------------------------
# Cada función aquí es el "puente" entre las rutas (HTTP) y el modelo
# (la base de datos). Recibe la petición del front, valida lo mínimo,
# llama al modelo y devuelve la respuesta JSON.
# =====================================================================

from flask import request, jsonify
from models import reservation_model


# ---------------------------------------------------------------------
# GET /api/reservations → lista TODAS las reservas (array plano)
# ---------------------------------------------------------------------
def get_all():
    return jsonify(reservation_model.list_all()), 200


# ---------------------------------------------------------------------
# GET /api/reservations/<id> → una sola reserva
# ---------------------------------------------------------------------
def get_one(reservation_id):
    reserva = reservation_model.find_by_id(reservation_id)
    if not reserva:
        return jsonify({"error": "Reserva no encontrada"}), 404
    return jsonify(reserva.to_dict()), 200


# ---------------------------------------------------------------------
# GET /api/reservations/user/<id> → reservas de UN usuario
# ---------------------------------------------------------------------
def get_by_user(user_id):
    return jsonify(reservation_model.list_by_user(user_id)), 200


# ---------------------------------------------------------------------
# POST /api/reservations → crear una reserva nueva
# ---------------------------------------------------------------------
def create_reservation():
    data = request.get_json() or {}
    try:
        reservation = reservation_model.create_from_payload(data)
        return jsonify(reservation), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# PUT /api/reservations/<id> → actualizar una reserva
# ---------------------------------------------------------------------
def update_reservation(reservation_id):
    data = request.get_json() or {}
    try:
        reservation = reservation_model.update(reservation_id, data)
        return jsonify(reservation), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# ---------------------------------------------------------------------
# POST /api/reservations/<id>/cancel → marcar como cancelada
# ---------------------------------------------------------------------
def cancel_reservation(reservation_id):
    try:
        reservation = reservation_model.cancel_reserva(reservation_id)
        return jsonify(reservation), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# ---------------------------------------------------------------------
# DELETE /api/reservations/<id> → eliminar reserva
# ---------------------------------------------------------------------
def delete_reservation(reservation_id):
    try:
        reservation_model.delete(reservation_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


# Aliases mantenidos por imports antiguos
get_one_by_id = get_one
