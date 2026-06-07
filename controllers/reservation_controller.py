# =====================================================================
# CONTROLADOR DE RESERVAS (reservation_controller.py)
# ---------------------------------------------------------------------
# Cada función aquí es el "puente" entre las rutas (HTTP) y el modelo
# (la base de datos). Recibe la petición del front, valida lo mínimo,
# llama al modelo y devuelve la respuesta JSON.
# =====================================================================

import logging
import traceback

from flask import g, request, jsonify

from controllers.auth_middleware import require_auth
from db import db
from models import reservation_model

logger = logging.getLogger(__name__)


def _role_of(user) -> str:
    try:
        return str(user.to_dict().get("id_rol", "")).lower()
    except Exception:
        return ""


def _estimate_price(data: dict):
    """Calcula el total desde la tarifa × duración cuando el front no lo manda."""
    from datetime import datetime
    from models import rate_model

    start = data.get("startDate") or data.get("hora_inicio")
    end = data.get("endDate") or data.get("hora_fin")
    if not start or not end:
        return None
    try:
        s = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        e = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        hours = max(0.0, (e - s).total_seconds() / 3600.0)
    except Exception:
        return None
    location_id = data.get("locationId") or data.get("id_ubicacion")
    vehicle_type = data.get("vehicleType") or "car"
    result = rate_model.quote(location_id, vehicle_type, hours)
    return result["total"] if result else None


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
@require_auth
def get_all():
    try:
        user = g.current_user
        # Un cliente sólo ve SUS reservas; admin/empleado ven todas.
        if _role_of(user) in {"admin", "empleado"}:
            return jsonify(reservation_model.list_all()), 200
        return jsonify(reservation_model.list_by_user(user.id_usuario)), 200
    except Exception as e:
        _handle_db_error("list_all", e)
        return jsonify({"error": f"Error listando reservas: {e}"}), 500


# ---------------------------------------------------------------------
# GET /api/reservations/<id> → una sola reserva
# ---------------------------------------------------------------------
@require_auth
def get_one(reservation_id):
    try:
        reserva = reservation_model.find_by_id(reservation_id)
        if not reserva:
            return jsonify({"error": "Reserva no encontrada"}), 404
        # Un cliente sólo puede ver su propia reserva.
        user = g.current_user
        if _role_of(user) not in {"admin", "empleado"} and reserva.id_usuario != user.id_usuario:
            return jsonify({"error": "Permiso denegado"}), 403
        return jsonify(reserva.to_dict()), 200
    except Exception as e:
        _handle_db_error("get_one", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# GET /api/reservations/user/<id> → reservas de UN usuario
# ---------------------------------------------------------------------
@require_auth
def get_by_user(user_id):
    try:
        return jsonify(reservation_model.list_by_user(user_id)), 200
    except Exception as e:
        _handle_db_error("get_by_user", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------
# POST /api/reservations → crear una reserva nueva
# ---------------------------------------------------------------------
@require_auth
def create_reservation():
    data = request.get_json() or {}
    # Un cliente sólo puede crear reservas a su propio nombre.
    user = g.current_user
    if _role_of(user) not in {"admin", "empleado"}:
        data["userId"] = user.id_usuario
    elif not data.get("userId"):
        data["userId"] = user.id_usuario

    # Si no llega el total, lo calculamos desde la tarifa (fuente de verdad).
    if not data.get("totalPrice") and not data.get("monto"):
        data["totalPrice"] = _estimate_price(data)

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
@require_auth
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
@require_auth
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
@require_auth
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
