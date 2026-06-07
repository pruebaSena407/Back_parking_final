import logging
import traceback
from datetime import datetime

from flask import request, jsonify
from sqlalchemy import text

from controllers.auth_middleware import require_role
from db import db
from models import location_model

logger = logging.getLogger(__name__)


def _handle_db_error(action: str, exc: Exception):
    try:
        db.session.rollback()
    except Exception:
        pass
    logger.error("Error en ubicaciones (%s): %s", action, exc)
    traceback.print_exc()


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
    try:
        return jsonify([_to_front(l) for l in location_model.list_all()]), 200
    except Exception as e:
        _handle_db_error("list_all", e)
        return jsonify({"error": str(e)}), 500


def get_by_id(location_id):
    try:
        loc = location_model.find_by_id(location_id)
        if not loc:
            return jsonify({"error": "Ubicación no encontrada"}), 404
        return jsonify(_to_front(loc.to_dict())), 200
    except Exception as e:
        _handle_db_error("get_one", e)
        return jsonify({"error": str(e)}), 500


def get_availability(location_id):
    """
    Cupos disponibles en un rango: capacidad - reservas activas que se solapan
    con [from, to]. Query params opcionales `from` y `to` (ISO). Sin rango,
    usa "ahora".
    """
    try:
        loc = location_model.find_by_id(location_id)
        if not loc:
            return jsonify({"error": "Ubicación no encontrada"}), 404

        now = datetime.utcnow()
        start_raw = request.args.get("from")
        end_raw = request.args.get("to")
        try:
            start = datetime.fromisoformat(start_raw.replace("Z", "+00:00")) if start_raw else now
            end = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else now
        except ValueError:
            start = end = now

        occupied = db.session.execute(text(
            """
            SELECT COUNT(*) FROM reserva
            WHERE id_ubicacion = :loc
              AND estado IN ('activa', 'pendiente')
              AND hora_inicio < :end
              AND hora_fin > :start
            """
        ), {"loc": int(location_id), "start": start, "end": end}).scalar() or 0

        capacity = int(loc.capacidad or 0)
        available = max(0, capacity - int(occupied))
        return jsonify({
            "locationId": int(location_id),
            "capacity": capacity,
            "occupied": int(occupied),
            "available": available,
            "full": available <= 0,
        }), 200
    except Exception as e:
        _handle_db_error("availability", e)
        return jsonify({"error": str(e)}), 500


@require_role("admin")
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
        _handle_db_error("create", e)
        return jsonify({"error": f"Error guardando ubicación: {e}"}), 500


@require_role("admin")
def update_location(location_id):
    data = request.get_json() or {}
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
        _handle_db_error("update (validación)", e)
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("update", e)
        return jsonify({"error": f"Error actualizando ubicación: {e}"}), 500


@require_role("admin")
def delete_location(location_id):
    try:
        location_model.delete(location_id)
        return "", 204
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        _handle_db_error("delete", e)
        return jsonify({"error": f"Error eliminando ubicación: {e}"}), 500
