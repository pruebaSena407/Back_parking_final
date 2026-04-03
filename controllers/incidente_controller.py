from flask import jsonify, request
from models.incidente_model import list_all, find_by_id, create_incidente, update_incidente, delete_incidente


def get_incidentes():
    return jsonify(list_all()), 200


def get_incidente(id_incidente):
    incidente = find_by_id(id_incidente)
    if not incidente:
        return jsonify({"error": "Incidente no encontrado"}), 404
    return jsonify(incidente), 200


def create_incidente_handler():
    data = request.get_json() or {}
    required = ["descripcion", "fecha_incidente", "id_registro"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} es requerido"}), 400

    incidente = create_incidente(data["descripcion"], data["fecha_incidente"], data["id_registro"])
    return jsonify(incidente), 201


def update_incidente_handler(id_incidente):
    data = request.get_json() or {}
    try:
        incidente = update_incidente(id_incidente, data)
        return jsonify(incidente), 200
    except ValueError:
        return jsonify({"error": "Incidente no encontrado"}), 404


def delete_incidente_handler(id_incidente):
    try:
        delete_incidente(id_incidente)
        return jsonify({"success": True}), 200
    except ValueError:
        return jsonify({"error": "Incidente no encontrado"}), 404
