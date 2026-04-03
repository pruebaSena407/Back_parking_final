from flask import Blueprint
from controllers.reservation_controller import (
    get_all,
    get_by_user,
    create_reservation,
    update_reservation,
    delete_reservation
)

reservation_bp = Blueprint("reservations", __name__)

@reservation_bp.route("/", methods=["GET"])
def list_all_reservations():
    return get_all()

@reservation_bp.route("/user/<user_id>", methods=["GET"])
def list_user_reservations(user_id):
    return get_by_user(user_id)

@reservation_bp.route("/", methods=["POST"])
def create_new_reservation():
    return create_reservation()

@reservation_bp.route("/<reservation_id>", methods=["PUT"])
def update_res(reservation_id):
    return update_reservation(reservation_id)

@reservation_bp.route("/<reservation_id>", methods=["DELETE"])
def delete_res(reservation_id):
    return delete_reservation(reservation_id)
