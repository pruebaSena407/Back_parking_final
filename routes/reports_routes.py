from flask import Blueprint
from controllers.reports_controller import (
    get_vehicle_flow,
    get_revenue_report,
    get_client_types,
    get_daily_summary,
)

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/vehicle-flow", methods=["GET"])
def vehicle_flow():
    return get_vehicle_flow()


@reports_bp.route("/revenue", methods=["GET"])
def revenue_report():
    return get_revenue_report()


@reports_bp.route("/client-types", methods=["GET"])
def client_types():
    return get_client_types()


@reports_bp.route("/daily-summary", methods=["GET"])
def daily_summary():
    return get_daily_summary()
