# =====================================================================
# CONTROLADOR DE REGISTROS (registro_controller.py)
# ---------------------------------------------------------------------
# Operación del "parqueadero automatizado": entrada (check-in) y salida
# (check-out) de vehículos. Lo opera un empleado o admin. Alimenta la
# ocupación en tiempo real y los reportes de flujo de vehículos.
# =====================================================================

import logging
import traceback

from flask import g, jsonify, request

from controllers.auth_middleware import require_role
from db import db
from models import registro_model

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en registros (%s): %s", action, exc)
    traceback.print_exc()


@require_role("admin", "empleado")
def list_registros():
    try:
        return jsonify(registro_model.list_all()), 200
    except Exception as e:
        _handle_db_error("list", e)
        return jsonify({"error": str(e)}), 500


@require_role("admin", "empleado")
def list_activos():
    try:
        location_id = request.args.get("locationId")
        return jsonify(registro_model.list_active(location_id)), 200
    except Exception as e:
        _handle_db_error("list_activos", e)
        return jsonify({"error": str(e)}), 500


@require_role("admin", "empleado")
def checkin_handler():
    data = request.get_json() or {}
    vehiculo = data.get("plate") or data.get("placa") or data.get("vehicleId") or data.get("vehiculo")
    location_id = data.get("locationId") or data.get("id_ubicacion")
    reservation_id = data.get("reservationId") or data.get("id_reserva")
    tipo = data.get("vehicleType") or data.get("tipo") or "car"
    # El operador autenticado queda como responsable del registro.
    id_usuario = data.get("userId") or g.current_user.id_usuario
    try:
        registro = registro_model.checkin(
            id_usuario=id_usuario,
            vehiculo=vehiculo,
            id_ubicacion=location_id,
            tipo=tipo,
            id_reserva=reservation_id,
        )
        return jsonify(registro), 201
    except ValueError as e:
        _handle_db_error("checkin (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        _handle_db_error("checkin", e)
        return jsonify({"error": f"Error en check-in: {e}"}), 500


@require_role("admin", "empleado")
def checkout_handler(id_registro):
    try:
        registro = registro_model.checkout(id_registro)
        return jsonify(registro), 200
    except ValueError as e:
        _handle_db_error("checkout (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        _handle_db_error("checkout", e)
        return jsonify({"error": f"Error en check-out: {e}"}), 500
