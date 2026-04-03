from flask import Blueprint
from controllers.pago_controller import get_pagos, get_pago, create_pago_handler, update_pago_handler, delete_pago_handler

pago_bp = Blueprint("pago", __name__, url_prefix="/api/pagos")

pago_bp.route("/", methods=["GET"])(get_pagos)
pago_bp.route("/<id_pago>", methods=["GET"])(get_pago)
pago_bp.route("/", methods=["POST"])(create_pago_handler)
pago_bp.route("/<id_pago>", methods=["PUT"])(update_pago_handler)
pago_bp.route("/<id_pago>", methods=["DELETE"])(delete_pago_handler)
