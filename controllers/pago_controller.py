from flask import jsonify, request
from models.pago_model import list_all, find_by_id, create_pago, update_pago, delete_pago


def get_pagos():
    return jsonify(list_all()), 200


def get_pago(id_pago):
    pago = find_by_id(id_pago)
    if not pago:
        return jsonify({"error": "Pago no encontrado"}), 404
    return jsonify(pago), 200


def create_pago_handler():
    data = request.get_json() or {}
    required = ["monto", "fecha_pago", "metodo_pago", "id_registro"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} es requerido"}), 400

    pago = create_pago(data["monto"], data["fecha_pago"], data["metodo_pago"], data["id_registro"])
    return jsonify(pago), 201


def update_pago_handler(id_pago):
    data = request.get_json() or {}
    try:
        pago = update_pago(id_pago, data)
        return jsonify(pago), 200
    except ValueError:
        return jsonify({"error": "Pago no encontrado"}), 404


def delete_pago_handler(id_pago):
    try:
        delete_pago(id_pago)
        return jsonify({"success": True}), 200
    except ValueError:
        return jsonify({"error": "Pago no encontrado"}), 404
