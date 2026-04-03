from flask import request, jsonify
from models.reservation_model import (
    list_all,
    list_by_user,
    create,
    update,
    delete
)

def get_all():
    return jsonify({"reservations": list_all()}), 200

def get_by_user(user_id):
    result = list_by_user(user_id)
    return jsonify({"reservations": result}), 200

def create_reservation():
    data = request.get_json()
    
    if not data or not data.get("userId") or not data.get("locationName") or not data.get("startTime") or not data.get("endTime"):
        return jsonify({"error": "Datos mínimos faltantes (userId, locationName, startTime, endTime)"}), 400
    
    try:
        reservation = create(
            user_id=data["userId"],
            location_name=data["locationName"],
            start_time=data["startTime"],
            end_time=data["endTime"],
            space_code=data.get("spaceCode"),
            amount=data.get("amount"),
            notes=data.get("notes")
        )
        return jsonify({"reservation": reservation}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def update_reservation(reservation_id):
    data = request.get_json()
    
    try:
        reservation = update(reservation_id, data)
        return jsonify({"reservation": reservation}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400

def delete_reservation(reservation_id):
    try:
        delete(reservation_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 400
