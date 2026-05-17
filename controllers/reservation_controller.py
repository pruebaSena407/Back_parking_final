# =====================================================================
# CONTROLADOR DE RESERVAS (reservation_controller.py)
# ---------------------------------------------------------------------
# Cada función aquí es el "puente" entre las rutas (HTTP) y el modelo
# (la base de datos). Recibe la petición del front, valida lo mínimo,
# llama al modelo y devuelve la respuesta JSON.
# =====================================================================

import logging
import traceback

from flask import request, jsonify

from db import db
from models import reservation_model

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    """
    Hace rollback de la sesión y loguea el traceback completo para que
    el motivo del fallo aparezca SIEMPRE en la consola del servidor.
    """
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en reservas (%s): %s", action, exc)
    traceback.print_exc()


# ---------------------------------------------------------------------
# GET /api/reservations → lista TODAS las reservas (array plano)
# ---------------------------------------------------------------------
def get_all():
    try:
        return jsonify(reservation_model.list_all()), 200
    except Exception as e:
        _handle_db_error("list_all", e)
        return jsonify({"error": f"Error listando reservas: {e}"}), 500


# ---------------------------------------------------------------------
# GET /api/reservations/<id> → una sola reserva
# ---------------------------------------------------------------------
def get_one(reservation_id):
    try:
        reserva = reservation_model.find_by_id(reservation_id)
        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404
        return jsonify(reserva.to_dict()), 200
    except Exception as e:
        _handle_db_error("get_one", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# GET /api/reservations/user/<id> → reservas de UN usuario
# ---------------------------------------------------------------------
def get_by_user(user_id):
    try:
        return jsonify(reservation_model.list_by_user(user_id)), 200
    except Exception as e:
        _handle_db_error("get_by_user", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# POST /api/reservations → crear una reserva nueva
# ---------------------------------------------------------------------
def create_reservation():
    data = request.get_json() or {}
    try:
        reservation = reservation_model.create_from_payload(data)
        return jsonify(reservation), 201
    except ValueError as e:
        # Datos inválidos del cliente: 400 Bad Request.
        _handle_db_error("create (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Error de DB / SQL: 500 con el mensaje real para depurar.
        _handle_db_error("create", e)
        return jsonify({"error": f"Error guardando reserva: {e}"}), 500


# ---------------------------------------------------------------------
# PUT /api/reservations/<id> → actualizar una reserva
# ---------------------------------------------------------------------
def update_reservation(reservation_id):
    data = request.get_json() or {}
    try:
        reservation = reservation_model.update(reservation_id, data)
        return jsonify(reservation), 200
    except ValueError as e:
        _handle_db_error("update (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update", e)
        return jsonify({"error": f"Error actualizando reserva: {e}"}), 500


# ---------------------------------------------------------------------
# POST /api/reservations/<id>/cancel → marcar como cancelada
# ---------------------------------------------------------------------
def cancel_reservation(reservation_id):
    try:
        reservation = reservation_model.cancel_reserva(reservation_id)
        return jsonify(reservation), 200
    except ValueError as e:
        _handle_db_error("cancel (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("cancel", e)
        return jsonify({"error": f"Error cancelando reserva: {e}"}), 500


# ---------------------------------------------------------------------
# DELETE /api/reservations/<id> → eliminar reserva
# ---------------------------------------------------------------------
def delete_reservation(reservation_id):
    try:
        reservation_model.delete(reservation_id)
        return "", 204
    except ValueError as e:
        _handle_db_error("delete (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("delete", e)
        return jsonify({"error": f"Error eliminando reserva: {e}"}), 500


# Aliases mantenidos por imports antiguos
get_one_by_id = get_one
