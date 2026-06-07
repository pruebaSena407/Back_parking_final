import logging
import traceback

from flask import request, jsonify

from controllers.auth_middleware import require_role
from db import db
from models import rate_model

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en tarifas (%s): %s", action, exc)
    traceback.print_exc()


def get_all():
    try:
        return jsonify(rate_model.list_all()), 200
    except Exception as e:
        _handle_db_error("list_all", e)
        return jsonify({"error": str(e)}), 500


def get_by_id(rate_id):
    try:
        rate = rate_model.find_by_id(rate_id)
        if not rate:
            return jsonify({"error": "Tarifa no encontrada"}), 404
        return jsonify(rate.to_dict()), 200
    except Exception as e:
        _handle_db_error("get_one", e)
        return jsonify({"error": str(e)}), 500


def get_by_location(location_id):
    try:
        rate = rate_model.find_by_location(location_id)
        if not rate:
            return jsonify({"error": "Tarifa no encontrada para la ubicación"}), 404
        return jsonify(rate), 200
    except Exception as e:
        _handle_db_error("get_by_location", e)
        return jsonify({"error": str(e)}), 500


def get_public():
    """Tarifas vigentes para la landing (público, sin auth)."""
    try:
        return jsonify(rate_model.list_public()), 200
    except Exception as e:
        _handle_db_error("public", e)
        return jsonify({"error": str(e)}), 500


def get_quote():
    """Estimado de cobro: ?locationId=&vehicleType=&hours="""
    try:
        location_id = request.args.get("locationId")
        vehicle_type = request.args.get("vehicleType", "car")
        hours = request.args.get("hours", "1")
        result = rate_model.quote(location_id, vehicle_type, hours)
        if result is None:
            return jsonify({"error": "No hay tarifas configuradas"}), 404
        return jsonify(result), 200
    except Exception as e:
        _handle_db_error("quote", e)
        return jsonify({"error": str(e)}), 500


@require_role("admin")
def create_rate():
    data = request.get_json() or {}
    try:
        rate = rate_model.create_from_payload(data)
        return jsonify(rate), 201
    except ValueError as e:
        _handle_db_error("create (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        _handle_db_error("create", e)
        return jsonify({"error": f"Error guardando tarifa: {e}"}), 500


@require_role("admin")
def update_rate(rate_id):
    data = request.get_json() or {}
    try:
        rate = rate_model.update(rate_id, data)
        return jsonify(rate), 200
    except ValueError as e:
        _handle_db_error("update (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update", e)
        return jsonify({"error": f"Error actualizando tarifa: {e}"}), 500


@require_role("admin")
def delete_rate(rate_id):
    try:
        rate_model.delete(rate_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("delete", e)
        return jsonify({"error": f"Error eliminando tarifa: {e}"}), 500
