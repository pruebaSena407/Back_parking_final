from flask import Blueprint
from controllers.user_controller import get_all, get_by_id, create_user, update_user, delete_user

user_bp = Blueprint("users", __name__)

@user_bp.route("/", methods=["GET"])
def list_users():
    return get_all()

@user_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    return get_by_id(user_id)

@user_bp.route("/", methods=["POST"])
def create_new_user():
    return create_user()

@user_bp.route("/<user_id>", methods=["PUT"])
def update_u(user_id):
    return update_user(user_id)

@user_bp.route("/<user_id>", methods=["DELETE"])
def delete_u(user_id):
    return delete_user(user_id)
