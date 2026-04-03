from flask import Blueprint
from controllers.location_controller import get_all, get_by_id, create_location, update_location, delete_location

location_bp = Blueprint("locations", __name__)

@location_bp.route("/", methods=["GET"])
def list_locations():
    return get_all()

@location_bp.route("/<location_id>", methods=["GET"])
def get_location(location_id):
    return get_by_id(location_id)

@location_bp.route("/", methods=["POST"])
def create_new_location():
    return create_location()

@location_bp.route("/<location_id>", methods=["PUT"])
def update_loc(location_id):
    return update_location(location_id)

@location_bp.route("/<location_id>", methods=["DELETE"])
def delete_loc(location_id):
    return delete_location(location_id)
