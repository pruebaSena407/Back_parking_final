from flask import Blueprint
from controllers.objeto_olvidado_controller import get_objetos_olvidados, get_objeto_olvidado, create_objeto_olvidado_handler, update_objeto_olvidado_handler, delete_objeto_olvidado_handler

objeto_olvidado_bp = Blueprint("objeto_olvidado", __name__, url_prefix="/api/objetos-olvidados")

objeto_olvidado_bp.route("/", methods=["GET"])(get_objetos_olvidados)
objeto_olvidado_bp.route("/<id_objeto_olvidado>", methods=["GET"])(get_objeto_olvidado)
objeto_olvidado_bp.route("/", methods=["POST"])(create_objeto_olvidado_handler)
objeto_olvidado_bp.route("/<id_objeto_olvidado>", methods=["PUT"])(update_objeto_olvidado_handler)
objeto_olvidado_bp.route("/<id_objeto_olvidado>", methods=["DELETE"])(delete_objeto_olvidado_handler)
