from flask import Blueprint
from controllers.user_controller import (
    create_user,
    delete_user,
    get_all,
    get_by_id,
    get_profile,
    update_user,
    update_user_role,
)

user_bp = Blueprint("users", __name__)


@user_bp.route("/", methods=["GET"])
def list_users():
    return get_all()


# Importante: /profile debe ir ANTES de /<user_id> para que Flask no
# interprete "profile" como un id.
@user_bp.route("/profile", methods=["GET"])
def my_profile():
    return get_profile()


@user_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    return get_by_id(user_id)


@user_bp.route("/", methods=["POST"])
def create_new_user():
    return create_user()


@user_bp.route("/<user_id>", methods=["PUT"])
def update_u(user_id):
    return update_user(user_id)


@user_bp.route("/<user_id>/role", methods=["PUT"])
def update_role(user_id):
    return update_user_role(user_id)


@user_bp.route("/<user_id>", methods=["DELETE"])
def delete_u(user_id):
    return delete_user(user_id)
