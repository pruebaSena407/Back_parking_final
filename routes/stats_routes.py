from flask import Blueprint
from controllers.stats_controller import get_overview, get_occupancy, get_revenue

stats_bp = Blueprint("stats", __name__)

@stats_bp.route("/overview", methods=["GET"])
def overview():
    return get_overview()

@stats_bp.route("/occupancy", methods=["GET"])
def occupancy():
    return get_occupancy()

@stats_bp.route("/revenue", methods=["GET"])
def revenue():
    return get_revenue()
