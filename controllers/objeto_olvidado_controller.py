from flask import jsonify, request
from models.objeto_olvidado_model import list_all, find_by_id, create_objeto, update_objeto, delete_objeto


def get_objetos_olvidados():
    return jsonify(list_all()), 200


def get_objeto_olvidado(id_objeto_olvidado):
    objeto = find_by_id(id_objeto_olvidado)
    if not objeto:
        return jsonify({"error": "Objeto olvidado no encontrado"}), 404
    return jsonify(objeto), 200


def create_objeto_olvidado_handler():
    data = request.get_json() or {}
    required = ["descripcion", "fecha_encontrado", "id_registro"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} es requerido"}), 400

    objeto = create_objeto(data["descripcion"], data["fecha_encontrado"], data["id_registro"])
    return jsonify(objeto), 201


def update_objeto_olvidado_handler(id_objeto_olvidado):
    data = request.get_json() or {}
    try:
        objeto = update_objeto(id_objeto_olvidado, data)
        return jsonify(objeto), 200
    except ValueError:
        return jsonify({"error": "Objeto olvidado no encontrado"}), 404


def delete_objeto_olvidado_handler(id_objeto_olvidado):
    try:
        delete_objeto(id_objeto_olvidado)
        return jsonify({"success": True}), 200
    except ValueError:
        return jsonify({"error": "Objeto olvidado no encontrado"}), 404
