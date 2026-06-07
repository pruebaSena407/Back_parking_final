# =====================================================================
# CONTROLADOR DE ESTADÍSTICAS (stats_controller.py)
# ---------------------------------------------------------------------
# Endpoints que alimentan el dashboard del front. Antes consumían
# atributos en memoria (`user_model.users`, etc.) que ya no existen
# porque migramos a SQLAlchemy. Ahora usamos consultas reales sobre
# Postgres.
# =====================================================================

from datetime import datetime
from flask import jsonify
from sqlalchemy import text

from controllers.auth_middleware import require_role
from db import db


def _scalar(query, params=None):
    """Helper para ejecutar una query escalar y devolver un valor o 0."""
    try:
        row = db.session.execute(text(query), params or {}).scalar()
        return row if row is not None else 0
    except Exception:
        db.session.rollback()
        return 0


@require_role("admin", "empleado")
def get_overview():
    """KPIs generales del dashboard."""
    active_clients = _scalar(
        """
        SELECT COUNT(*) FROM usuario u
        LEFT JOIN rol r ON r.id_rol = u.id_rol
        WHERE LOWER(COALESCE(r.nombre, '')) = 'cliente'
        """
    )
    active_reservations = _scalar(
        "SELECT COUNT(*) FROM reserva WHERE estado IN ('activa', 'pendiente')"
    )
    monthly_revenue = _scalar(
        """
        SELECT COALESCE(SUM(monto), 0) FROM pago
        WHERE estado = 'completed'
          AND date_trunc('month', fecha_pago) = date_trunc('month', CURRENT_DATE)
        """
    )
    location_count = _scalar("SELECT COUNT(*) FROM ubicacion")
    total_users = _scalar("SELECT COUNT(*) FROM usuario")

    return jsonify({
        "stats": {
            "activeClients": int(active_clients),
            "activeReservations": int(active_reservations),
            "monthlyRevenue": float(monthly_revenue or 0),
            "locationCount": int(location_count),
            "totalUsers": int(total_users),
        }
    }), 200


@require_role("admin", "empleado")
def get_occupancy():
    """Tasa de ocupación por ubicación basada en reservas activas ahora."""
    rows = db.session.execute(text(
        """
        SELECT u.id_ubicacion, u.nombre, u.capacidad,
            (
                SELECT COUNT(*) FROM reserva r
                WHERE r.id_ubicacion = u.id_ubicacion
                  AND r.estado = 'activa'
                  AND r.hora_inicio <= :now
                  AND r.hora_fin > :now
            ) AS occupied
        FROM ubicacion u
        ORDER BY u.id_ubicacion
        """
    ), {"now": datetime.utcnow()}).fetchall()

    occupancy_data = []
    total_rate = 0.0
    for row in rows:
        capacity = int(row.capacidad or 0)
        occupied = int(row.occupied or 0)
        rate = round((occupied / capacity) * 100, 2) if capacity > 0 else 0
        total_rate += rate
        occupancy_data.append({
            "locationId": row.id_ubicacion,
            "locationName": row.nombre,
            "capacity": capacity,
            "occupied": occupied,
            "rate": rate,
        })

    average = round(total_rate / len(occupancy_data), 2) if occupancy_data else 0
    return jsonify({
        "occupancy": occupancy_data,
        "averageRate": average,
    }), 200


@require_role("admin", "empleado")
def get_revenue():
    """Resumen de ingresos."""
    total = _scalar("SELECT COALESCE(SUM(monto), 0) FROM pago")
    completed = _scalar("SELECT COALESCE(SUM(monto), 0) FROM pago WHERE estado = 'completed'")
    pending = _scalar("SELECT COALESCE(SUM(monto), 0) FROM pago WHERE estado = 'pending'")
    refunded = _scalar("SELECT COALESCE(SUM(monto), 0) FROM pago WHERE estado = 'refunded'")
    payment_count = _scalar("SELECT COUNT(*) FROM pago")

    return jsonify({
        "revenue": {
            "total": float(total or 0),
            "completed": float(completed or 0),
            "pending": float(pending or 0),
            "refunded": float(refunded or 0),
            "paymentCount": int(payment_count),
        }
    }), 200
