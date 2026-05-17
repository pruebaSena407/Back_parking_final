from flask import request, jsonify
from models import rate_model


def get_all():
    return jsonify(rate_model.list_all()), 200


def get_by_id(rate_id):
    rate = rate_model.find_by_id(rate_id)
    if not rate:
        return jsonify({"error": "Tarifa no encontrada"}), 404
    return jsonify(rate.to_dict()), 200


def get_by_location(location_id):
    rate = rate_model.find_by_location(location_id)
    if not rate:
        return jsonify({"error": "Tarifa no encontrada para la ubicación"}), 404
    return jsonify(rate), 200


def create_rate():
    data = request.get_json() or {}
    try:
        rate = rate_model.create_from_payload(data)
        return jsonify(rate), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def update_rate(rate_id):
    data = request.get_json() or {}
    try:
        rate = rate_model.update(rate_id, data)
        return jsonify(rate), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def delete_rate(rate_id):
    try:
        rate_model.delete(rate_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
