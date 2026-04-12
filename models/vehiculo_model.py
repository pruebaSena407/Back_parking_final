from datetime import datetime
from sqlalchemy import text

from db import db


class Vehiculo(db.Model):
    __tablename__ = "vehiculo"

    id_vehiculo = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(20), unique=True, nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(100))
    color = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_vehiculo": self.id_vehiculo,
            "placa": self.placa,
            "tipo": self.tipo,
            "marca": self.marca,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_vehiculo_id() -> int:
    """Siguiente id entero acorde a la columna vehiculo.id_vehiculo"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_vehiculo), 0) + 1 FROM vehiculo")
    ).scalar()
    return int(row)


def find_by_id(id_vehiculo):
    if id_vehiculo is None:
        return None
    try:
        pk = int(id_vehiculo)
    except (TypeError, ValueError):
        return None
    return Vehiculo.query.get(pk)


def find_by_placa(placa):
    return Vehiculo.query.filter_by(placa=placa).first()


def list_all():
    vehiculos = Vehiculo.query.all()
    return [vehiculo.to_dict() for vehiculo in vehiculos]


def create_vehiculo(placa, tipo, marca=None, color=None):
    if find_by_placa(placa):
        raise ValueError("Placa ya registrada")

    vehiculo = Vehiculo(
        id_vehiculo=next_vehiculo_id(),
        placa=placa,
        tipo=tipo,
        marca=marca,
        color=color,
    )
    db.session.add(vehiculo)
    db.session.commit()
    db.session.refresh(vehiculo)
    return vehiculo.to_dict()


def update_vehiculo(id_vehiculo, updates):
    vehiculo = find_by_id(id_vehiculo)
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")

    for key, value in updates.items():
        if hasattr(vehiculo, key) and key in ["placa", "tipo", "marca", "color"]:
            setattr(vehiculo, key, value)

    db.session.commit()
    return vehiculo.to_dict()


def delete_vehiculo(id_vehiculo):
    vehiculo = find_by_id(id_vehiculo)
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")

    db.session.delete(vehiculo)
    db.session.commit()
