from flask import jsonify, request
from models import pago_model


def get_pagos():
    return jsonify(pago_model.list_all()), 200


def get_pago(id_pago):
    pago = pago_model.find_by_id(id_pago)
    if not pago:
        return jsonify({"error": "Pago no encontrado"}), 404
    return jsonify(pago.to_dict()), 200


def create_pago_handler():
    data = request.get_json() or {}
    try:
        pago = pago_model.create_from_payload(data)
        return jsonify(pago), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


def update_pago_handler(id_pago):
    data = request.get_json() or {}
    try:
        pago = pago_model.update_pago(id_pago, data)
        return jsonify(pago), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


def refund_pago_handler(id_pago):
    try:
        pago = pago_model.refund_pago(id_pago)
        return jsonify(pago), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


def delete_pago_handler(id_pago):
    try:
        pago_model.delete_pago(id_pago)
        return "", 204
    except ValueError:
        return jsonify({"error": "Pago no encontrado"}), 404
