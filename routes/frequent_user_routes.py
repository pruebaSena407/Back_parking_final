from flask import Blueprint
from controllers.frequent_user_controller import register_frequent_user

frequent_user_bp = Blueprint("frequent_users", __name__)


@frequent_user_bp.route("/", methods=["POST"])
def create_frequent_user():
    return register_frequent_user()
