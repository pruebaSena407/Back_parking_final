# =====================================================================
# RUTAS DE RESERVAS (reservation_routes.py)
# ---------------------------------------------------------------------
# Define las URLs del CRUD de reservas. Con el prefix "/api/reservations"
# (configurado en app.py), las URLs finales son:
#
#   GET    /api/reservations/             → listar todas
#   GET    /api/reservations/user/<id>    → reservas de un usuario
#   POST   /api/reservations/             → crear reserva
#   PUT    /api/reservations/<id>         → actualizar reserva
#   DELETE /api/reservations/<id>         → borrar reserva
# =====================================================================

from flask import Blueprint
from controllers.reservation_controller import (
    get_all,
    get_by_user,
    create_reservation,
    update_reservation,
    delete_reservation
)

reservation_bp = Blueprint("reservations", __name__)


# Listar TODAS las reservas (sirve para admin)
@reservation_bp.route("/", methods=["GET"])
def list_all_reservations():
    return get_all()


# Listar reservas de un usuario específico. <user_id> es un parámetro
# que se reemplaza con el id real en la URL (ej: /user/5).
@reservation_bp.route("/user/<user_id>", methods=["GET"])
def list_user_reservations(user_id):
    return get_by_user(user_id)


# Crear una nueva reserva con datos JSON del body
@reservation_bp.route("/", methods=["POST"])
def create_new_reservation():
    return create_reservation()


# Actualizar (modificar) una reserva existente
@reservation_bp.route("/<reservation_id>", methods=["PUT"])
def update_res(reservation_id):
    return update_reservation(reservation_id)


# Eliminar una reserva
@reservation_bp.route("/<reservation_id>", methods=["DELETE"])
def delete_res(reservation_id):
    return delete_reservation(reservation_id)
