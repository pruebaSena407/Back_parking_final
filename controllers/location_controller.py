from flask import request, jsonify
from models import location_model

def get_all():
    return jsonify({"locations": location_model.list_all()}), 200

def get_by_id(location_id):
    loc = location_model.find_by_id(location_id)
    if not loc:
        return jsonify({"error": "Ubicación no encontrada"}), 404
    return jsonify({"location": loc}), 200

def create_location():
    data = request.get_json()
    
    if not data or not data.get("name") or not data.get("address") or not data.get("capacity"):
        return jsonify({"error": "Faltan datos (name, address, capacity, latitude, longitude)"}), 400
    
    try:
        location = location_model.create(
            name=data["name"],
            address=data["address"],
            capacity=int(data["capacity"]),
            latitude=float(data.get("latitude", 4.71)),
            longitude=float(data.get("longitude", -74.01))
        )
        return jsonify({"location": location}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def update_location(location_id):
    data = request.get_json()
    
    try:
        location = location_model.update(location_id, data)
        return jsonify({"location": location}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def delete_location(location_id):
    try:
        location_model.delete(location_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
