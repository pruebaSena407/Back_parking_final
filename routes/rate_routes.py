from flask import Blueprint
from controllers.rate_controller import (
    get_all,
    get_by_id,
    get_by_location,
    get_public,
    get_quote,
    create_rate,
    update_rate,
    delete_rate,
)

rate_bp = Blueprint("rates", __name__)


@rate_bp.route("/", methods=["GET"])
def list_rates():
    return get_all()


# Rutas específicas ANTES de /<rate_id> para que no se interpreten como id.
@rate_bp.route("/public", methods=["GET"])
def public_rates():
    return get_public()


@rate_bp.route("/quote", methods=["GET"])
def quote_rate():
    return get_quote()


@rate_bp.route("/location/<location_id>", methods=["GET"])
def get_rate_by_location(location_id):
    return get_by_location(location_id)


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
