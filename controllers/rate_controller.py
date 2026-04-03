from flask import request, jsonify
from models import rate_model

def get_all():
    return jsonify({"rates": rate_model.list_all()}), 200

def get_by_id(rate_id):
    rate = rate_model.find_by_id(rate_id)
    if not rate:
        return jsonify({"error": "Tarifa no encontrada"}), 404
    return jsonify({"rate": rate}), 200

def create_rate():
    data = request.get_json()
    
    if not data or not data.get("name") or not data.get("hourlyRate") or not data.get("dailyRate") or not data.get("vehicleType"):
        return jsonify({"error": "Faltan datos (name, hourlyRate, dailyRate, vehicleType)"}), 400
    
    try:
        rate = rate_model.create(
            name=data["name"],
            hourly_rate=int(data["hourlyRate"]),
            daily_rate=int(data["dailyRate"]),
            vehicle_type=data["vehicleType"]
        )
        return jsonify({"rate": rate}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def update_rate(rate_id):
    data = request.get_json()
    
    try:
        rate = rate_model.update(rate_id, data)
        return jsonify({"rate": rate}), 200
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
