from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db


class Rate(db.Model):
    __tablename__ = "tarifa"

    id_tarifa = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tarifa_horaria = db.Column(db.Float, nullable=False)
    tarifa_diaria = db.Column(db.Float, nullable=False)
    # Nuevas columnas pedidas por el contrato del front (rateService.ts):
    tarifa_mensual = db.Column(db.Float)
    moneda = db.Column(db.String(10), default="COP")
    tipo_vehiculo = db.Column(db.String(50), nullable=False)
    # Permite asociar una tarifa a una ubicación específica (opcional).
    id_ubicacion = db.Column(db.Integer, ForeignKey("ubicacion.id_ubicacion"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """
        Devuelve el dict en el formato camelCase que el front ya tiene
        tipado en `Front_parking_final/src/services/rateService.ts`.
        """
        return {
            "id": self.id_tarifa,
            "name": self.nombre,
            "hourlyRate": self.tarifa_horaria,
            "dailyRate": self.tarifa_diaria,
            "monthlyRate": self.tarifa_mensual,
            "currency": self.moneda or "COP",
            "vehicleType": self.tipo_vehiculo,
            "locationId": self.id_ubicacion,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_tarifa_id() -> int:
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_tarifa), 0) + 1 FROM tarifa")
    ).scalar()
    return int(row)


def find_by_id(rate_id):
    if rate_id is None:
        return None
    try:
        pk = int(rate_id)
    except (TypeError, ValueError):
        return None
    return Rate.query.get(pk)


def find_by_nombre(nombre):
    return Rate.query.filter_by(nombre=nombre).first()


def list_all():
    return [r.to_dict() for r in Rate.query.all()]


def list_by_tipo_vehiculo(tipo_vehiculo):
    return [r.to_dict() for r in Rate.query.filter_by(tipo_vehiculo=tipo_vehiculo).all()]


def find_by_location(location_id):
    """Devuelve la primera tarifa asociada a una ubicación o None."""
    if location_id is None:
        return None
    try:
        loc_pk = int(location_id)
    except (TypeError, ValueError):
        return None
    rate = Rate.query.filter_by(id_ubicacion=loc_pk).first()
    return rate.to_dict() if rate else None


def create_rate(
    nombre,
    tarifa_horaria,
    tarifa_diaria,
    tipo_vehiculo,
    tarifa_mensual=None,
    moneda="COP",
    id_ubicacion=None,
):
    rate = Rate(
        id_tarifa=next_tarifa_id(),
        nombre=nombre,
        tarifa_horaria=tarifa_horaria,
        tarifa_diaria=tarifa_diaria,
        tarifa_mensual=tarifa_mensual,
        moneda=moneda,
        tipo_vehiculo=tipo_vehiculo,
        id_ubicacion=id_ubicacion,
    )
    db.session.add(rate)
    db.session.commit()
    db.session.refresh(rate)
    return rate.to_dict()


def create_from_payload(payload: dict):
    """Acepta camelCase del front + nombres internos."""
    name = payload.get("name") or payload.get("nombre")
    hourly = payload.get("hourlyRate") or payload.get("tarifa_horaria")
    daily = payload.get("dailyRate") or payload.get("tarifa_diaria")
    monthly = payload.get("monthlyRate") or payload.get("tarifa_mensual")
    currency = payload.get("currency") or payload.get("moneda") or "COP"
    vehicle_type = payload.get("vehicleType") or payload.get("tipo_vehiculo")
    location_id = payload.get("locationId") or payload.get("id_ubicacion")

    if not name or hourly is None or daily is None or not vehicle_type:
        raise ValueError("Faltan datos (name, hourlyRate, dailyRate, vehicleType)")

    return create_rate(
        nombre=name,
        tarifa_horaria=float(hourly),
        tarifa_diaria=float(daily),
        tipo_vehiculo=vehicle_type,
        tarifa_mensual=float(monthly) if monthly is not None else None,
        moneda=currency,
        id_ubicacion=int(location_id) if location_id is not None else None,
    )


# Alias mantenido para código antiguo (no se usa en los controladores nuevos).
def create(name, hourly_rate, daily_rate, vehicle_type, monthly_rate=None, currency="COP", location_id=None):
    return create_rate(
        name,
        hourly_rate,
        daily_rate,
        vehicle_type,
        tarifa_mensual=monthly_rate,
        moneda=currency,
        id_ubicacion=location_id,
    )


def update_rate(rate_id, updates: dict):
    rate = find_by_id(rate_id)
    if not rate:
        raise ValueError("Tarifa no encontrada")

    field_map = {
        "name": "nombre",
        "nombre": "nombre",
        "hourlyRate": "tarifa_horaria",
        "tarifa_horaria": "tarifa_horaria",
        "dailyRate": "tarifa_diaria",
        "tarifa_diaria": "tarifa_diaria",
        "monthlyRate": "tarifa_mensual",
        "tarifa_mensual": "tarifa_mensual",
        "currency": "moneda",
        "moneda": "moneda",
        "vehicleType": "tipo_vehiculo",
        "tipo_vehiculo": "tipo_vehiculo",
        "locationId": "id_ubicacion",
        "id_ubicacion": "id_ubicacion",
    }
    for key, value in updates.items():
        column = field_map.get(key)
        if not column:
            continue
        setattr(rate, column, value)

    db.session.commit()
    return rate.to_dict()


def update(rate_id, updates):
    return update_rate(rate_id, updates)


def delete_rate(rate_id):
    rate = find_by_id(rate_id)
    if not rate:
        raise ValueError("Tarifa no encontrada")
    db.session.delete(rate)
    db.session.commit()


def delete(rate_id):
    return delete_rate(rate_id)
