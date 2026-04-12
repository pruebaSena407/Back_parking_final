from datetime import datetime
from sqlalchemy import text

from db import db


class Rate(db.Model):
    __tablename__ = "tarifa"

    id_tarifa = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    tarifa_horaria = db.Column(db.Float, nullable=False)
    tarifa_diaria = db.Column(db.Float, nullable=False)
    tipo_vehiculo = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_tarifa": self.id_tarifa,
            "nombre": self.nombre,
            "tarifa_horaria": self.tarifa_horaria,
            "tarifa_diaria": self.tarifa_diaria,
            "tipo_vehiculo": self.tipo_vehiculo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_tarifa_id() -> int:
    """Siguiente id entero acorde a la columna tarifa.id_tarifa"""
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
    rates = Rate.query.all()
    return [rate.to_dict() for rate in rates]


def list_by_tipo_vehiculo(tipo_vehiculo):
    rates = Rate.query.filter_by(tipo_vehiculo=tipo_vehiculo).all()
    return [rate.to_dict() for rate in rates]


def create_rate(nombre, tarifa_horaria, tarifa_diaria, tipo_vehiculo):
    rate = Rate(
        id_tarifa=next_tarifa_id(),
        nombre=nombre,
        tarifa_horaria=tarifa_horaria,
        tarifa_diaria=tarifa_diaria,
        tipo_vehiculo=tipo_vehiculo,
    )
    db.session.add(rate)
    db.session.commit()
    db.session.refresh(rate)
    return rate.to_dict()


def create(name, hourly_rate, daily_rate, vehicle_type):
    """Alias para compatibilidad"""
    return create_rate(name, hourly_rate, daily_rate, vehicle_type)


def update_rate(rate_id, updates):
    rate = find_by_id(rate_id)
    if not rate:
        raise ValueError("Tarifa no encontrada")

    for key, value in updates.items():
        if hasattr(rate, key) and key in ["nombre", "tarifa_horaria", "tarifa_diaria", "tipo_vehiculo"]:
            setattr(rate, key, value)

    db.session.commit()
    return rate.to_dict()


def update(rate_id, updates):
    """Alias para compatibilidad"""
    return update_rate(rate_id, updates)


def delete_rate(rate_id):
    rate = find_by_id(rate_id)
    if not rate:
        raise ValueError("Tarifa no encontrada")

    db.session.delete(rate)
    db.session.commit()


def delete(rate_id):
    """Alias para compatibilidad"""
    return delete_rate(rate_id)
