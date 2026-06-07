from flask import Blueprint
from controllers.registro_controller import (
    list_registros,
    list_activos,
    checkin_handler,
    checkout_handler,
)

# El prefix lo aplica app.py al registrar el blueprint (/api/registros).
registro_bp = Blueprint("registros", __name__)

registro_bp.route("/", methods=["GET"])(list_registros)
registro_bp.route("/activos", methods=["GET"])(list_activos)
registro_bp.route("/checkin", methods=["POST"])(checkin_handler)
registro_bp.route("/<id_registro>/checkout", methods=["POST"])(checkout_handler)
