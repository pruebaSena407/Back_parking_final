from flask import Blueprint
from controllers.auth_controller import signup, signin

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def auth_signup():
    return signup()

@auth_bp.route("/signin", methods=["POST"])
def auth_signin():
    return signin()
