from flask import Blueprint
from controllers.rate_controller import get_all, get_by_id, create_rate, update_rate, delete_rate

rate_bp = Blueprint("rates", __name__)

@rate_bp.route("/", methods=["GET"])
def list_rates():
    return get_all()

@rate_bp.route("/<rate_id>", methods=["GET"])
def get_rate(rate_id):
    return get_by_id(rate_id)

@rate_bp.route("/", methods=["POST"])
def create_new_rate():
    return create_rate()

@rate_bp.route("/<rate_id>", methods=["PUT"])
def update_r(rate_id):
    return update_rate(rate_id)

@rate_bp.route("/<rate_id>", methods=["DELETE"])
def delete_r(rate_id):
    return delete_rate(rate_id)
