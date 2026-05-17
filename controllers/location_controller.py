from flask import request, jsonify
from models import location_model


def _to_front(loc_dict):
    """
    Adapta el dict del modelo (snake_case en español) al contrato camelCase
    que el front ya tiene tipado en `locationService.ts`:
      { id, name, address, capacity, latitude, longitude }
    """
    if not loc_dict:
        return None
    return {
        "id": loc_dict.get("id_ubicacion"),
        "name": loc_dict.get("nombre"),
        "address": loc_dict.get("direccion"),
        "capacity": loc_dict.get("capacidad"),
        "latitude": loc_dict.get("latitud"),
        "longitude": loc_dict.get("longitud"),
        "createdAt": loc_dict.get("created_at"),
        "updatedAt": loc_dict.get("updated_at"),
    }


def get_all():
    return jsonify([_to_front(l) for l in location_model.list_all()]), 200


def get_by_id(location_id):
    loc = location_model.find_by_id(location_id)
    if not loc:
        return jsonify({"error": "Ubicación no encontrada"}), 404
    return jsonify(_to_front(loc.to_dict())), 200


def create_location():
    data = request.get_json() or {}
    name = data.get("name") or data.get("nombre")
    address = data.get("address") or data.get("direccion")
    capacity = data.get("capacity") or data.get("capacidad")
    latitude = data.get("latitude") or data.get("latitud")
    longitude = data.get("longitude") or data.get("longitud")

    if not name or not address or capacity is None:
        return jsonify({"error": "Faltan datos (name, address, capacity, latitude, longitude)"}), 400

    try:
        location = location_model.create_location(
            nombre=name,
            direccion=address,
            capacidad=int(capacity),
            latitud=float(latitude) if latitude is not None else 4.71,
            longitud=float(longitude) if longitude is not None else -74.01,
        )
        return jsonify(_to_front(location)), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def update_location(location_id):
    data = request.get_json() or {}
    # Aceptamos tanto camelCase del front como los nombres internos.
    field_map = {
        "name": "nombre",
        "address": "direccion",
        "capacity": "capacidad",
        "latitude": "latitud",
        "longitude": "longitud",
    }
    updates = {field_map.get(k, k): v for k, v in data.items()}
    try:
        location = location_model.update_location(location_id, updates)
        return jsonify(_to_front(location)), 200
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
