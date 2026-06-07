# =====================================================================
# CONTROLADOR DE REPORTES (reports_controller.py)
# ---------------------------------------------------------------------
# Endpoints de /api/reports que alimentan los gráficos de la página de
# reportes en el front. Las consultas se hacen sobre las tablas
# `registro` (entradas/salidas) y `pago` (ingresos).
# =====================================================================

from datetime import date, datetime, timedelta
from flask import jsonify, request
from sqlalchemy import text

from controllers.auth_middleware import require_role
from db import db


VALID_PERIODS = {"weekly", "monthly", "yearly"}


def _resolve_period(period: str):
    """
    Devuelve (fecha_desde, granularidad_sql, etiquetas_dia, intervalo_dias).
    """
    if period not in VALID_PERIODS:
        period = "weekly"
    today = date.today()
    if period == "weekly":
        return today - timedelta(days=6), "day", 7
    if period == "monthly":
        return today - timedelta(days=29), "day", 30
    return today - timedelta(days=365), "month", 12


def _short_label(d: date, granularity: str):
    if granularity == "month":
        return d.strftime("%b").capitalize()
    return d.strftime("%a").capitalize()  # Mon, Tue, ...


def _as_date(value):
    """
    Normaliza a `date`. Algunas columnas de fecha en la BD son en realidad
    TIMESTAMP, así que llegan como datetime; al agrupar por día comparábamos
    datetime contra date y nunca coincidía (gráficas en cero). Convertimos.
    """
    if isinstance(value, datetime):
        return value.date()
    return value


@require_role("admin", "empleado")
def get_vehicle_flow():
    period = request.args.get("period", "weekly")
    start, granularity, buckets = _resolve_period(period)

    rows = db.session.execute(text(
        """
        SELECT fecha,
               SUM(CASE WHEN hora_entrada IS NOT NULL THEN 1 ELSE 0 END) AS entradas,
               SUM(CASE WHEN hora_salida IS NOT NULL THEN 1 ELSE 0 END) AS salidas
        FROM registro
        WHERE fecha >= :start
        GROUP BY fecha
        ORDER BY fecha
        """
    ), {"start": start}).fetchall()

    by_date = {_as_date(row.fecha): (int(row.entradas or 0), int(row.salidas or 0)) for row in rows}

    data = []
    for i in range(buckets):
        if granularity == "month":
            cursor = (start + timedelta(days=i * 30))
        else:
            cursor = start + timedelta(days=i)
        entradas, salidas = by_date.get(cursor, (0, 0))
        data.append({
            "name": _short_label(cursor, granularity),
            "date": cursor.isoformat(),
            "entradas": entradas,
            "salidas": salidas,
        })
    return jsonify(data), 200


@require_role("admin", "empleado")
def get_revenue_report():
    period = request.args.get("period", "weekly")
    start, granularity, buckets = _resolve_period(period)

    rows = db.session.execute(text(
        """
        SELECT fecha_pago, COALESCE(SUM(monto), 0) AS total
        FROM pago
        WHERE estado = 'completed' AND fecha_pago >= :start
        GROUP BY fecha_pago
        ORDER BY fecha_pago
        """
    ), {"start": start}).fetchall()

    by_date = {_as_date(row.fecha_pago): float(row.total or 0) for row in rows}

    data = []
    for i in range(buckets):
        cursor = start + timedelta(days=i if granularity != "month" else i * 30)
        data.append({
            "name": _short_label(cursor, granularity),
            "date": cursor.isoformat(),
            "ingresos": by_date.get(cursor, 0),
        })
    return jsonify(data), 200


@require_role("admin", "empleado")
def get_client_types():
    """Distribución de usuarios por rol."""
    rows = db.session.execute(text(
        """
        SELECT COALESCE(r.nombre, 'desconocido') AS nombre, COUNT(u.id_usuario) AS cantidad
        FROM usuario u
        LEFT JOIN rol r ON r.id_rol = u.id_rol
        GROUP BY r.nombre
        ORDER BY cantidad DESC
        """
    )).fetchall()

    label_map = {
        "cliente": "Regulares",
        "empleado": "Empleados",
        "admin": "Administradores",
    }
    data = [
        {
            "name": label_map.get((row.nombre or "").lower(), (row.nombre or "Sin rol").capitalize()),
            "value": int(row.cantidad or 0),
        }
        for row in rows
    ]
    return jsonify(data), 200


@require_role("admin", "empleado")
def get_daily_summary():
    period = request.args.get("period", "weekly")
    start, _, buckets = _resolve_period(period)

    rows = db.session.execute(text(
        """
        SELECT
          r.fecha,
          COUNT(r.id_registro) AS entradas,
          SUM(CASE WHEN r.hora_salida IS NOT NULL THEN 1 ELSE 0 END) AS salidas,
          (
            SELECT COALESCE(SUM(p.monto), 0)
            FROM pago p
            WHERE p.fecha_pago = r.fecha AND p.estado = 'completed'
          ) AS ingresos,
          AVG(
            CASE
              WHEN r.hora_salida IS NOT NULL THEN
                EXTRACT(EPOCH FROM (r.hora_salida - r.hora_entrada))
              ELSE NULL
            END
          ) AS promedio_segundos
        FROM registro r
        WHERE r.fecha >= :start
        GROUP BY r.fecha
        ORDER BY r.fecha DESC
        """
    ), {"start": start}).fetchall()

    def _format_seconds(seconds):
        if not seconds:
            return "0h 0m"
        seconds = int(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        return f"{h}h {m}m"

    data = []
    for row in rows:
        data.append({
            "fecha": row.fecha.isoformat() if row.fecha else None,
            "entradas": int(row.entradas or 0),
            "salidas": int(row.salidas or 0),
            "ingresos": float(row.ingresos or 0),
            "tiempoPromedio": _format_seconds(row.promedio_segundos),
        })
    return jsonify(data), 200
