import logging
import traceback

from flask import jsonify, request

from db import db
from models import pago_model

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    """Rollback + log con traceback para que el server NUNCA trague el error."""
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en pagos (%s): %s", action, exc)
    traceback.print_exc()


def get_pagos():
    try:
        return jsonify(pago_model.list_all()), 200
    except Exception as e:
        _handle_db_error("list_all", e)
        return jsonify({"error": str(e)}), 500


def get_pago(id_pago):
    try:
        pago = pago_model.find_by_id(id_pago)
        if not pago:
            return jsonify({"error": "Pago no encontrado"}), 404
        return jsonify(pago.to_dict()), 200
    except Exception as e:
        _handle_db_error("get_one", e)
        return jsonify({"error": str(e)}), 500


def create_pago_handler():
    data = request.get_json() or {}
    try:
        pago = pago_model.create_from_payload(data)
        return jsonify(pago), 201
    except ValueError as e:
        _handle_db_error("create (validación)", e)
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        _handle_db_error("create", e)
        return jsonify({"error": f"Error guardando pago: {e}"}), 500


def update_pago_handler(id_pago):
    data = request.get_json() or {}
    try:
        pago = pago_model.update_pago(id_pago, data)
        return jsonify(pago), 200
    except ValueError as e:
        _handle_db_error("update (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update", e)
        return jsonify({"error": f"Error actualizando pago: {e}"}), 500


def refund_pago_handler(id_pago):
    try:
        pago = pago_model.refund_pago(id_pago)
        return jsonify(pago), 200
    except ValueError as e:
        _handle_db_error("refund (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("refund", e)
        return jsonify({"error": f"Error reembolsando pago: {e}"}), 500


def delete_pago_handler(id_pago):
    try:
        pago_model.delete_pago(id_pago)
        return "", 204
    except ValueError:
        return jsonify({"error": "Pago no encontrado"}), 404
    except Exception as e:
        _handle_db_error("delete", e)
        return jsonify({"error": f"Error eliminando pago: {e}"}), 500
