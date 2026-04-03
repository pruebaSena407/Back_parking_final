from flask import Blueprint
from controllers.incidente_controller import get_incidentes, get_incidente, create_incidente_handler, update_incidente_handler, delete_incidente_handler

incidente_bp = Blueprint("incidente", __name__, url_prefix="/api/incidentes")

incidente_bp.route("/", methods=["GET"])(get_incidentes)
incidente_bp.route("/<id_incidente>", methods=["GET"])(get_incidente)
incidente_bp.route("/", methods=["POST"])(create_incidente_handler)
incidente_bp.route("/<id_incidente>", methods=["PUT"])(update_incidente_handler)
incidente_bp.route("/<id_incidente>", methods=["DELETE"])(delete_incidente_handler)
