from datetime import datetime
from sqlalchemy import text

from db import db


class Location(db.Model):
    __tablename__ = "ubicacion"

    id_ubicacion = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    direccion = db.Column(db.String(255), nullable=False)
    capacidad = db.Column(db.Integer, nullable=False)
    latitud = db.Column(db.Float)
    longitud = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_ubicacion": self.id_ubicacion,
            "nombre": self.nombre,
            "direccion": self.direccion,
            "capacidad": self.capacidad,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_ubicacion_id() -> int:
    """Siguiente id entero acorde a la columna ubicacion.id_ubicacion"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_ubicacion), 0) + 1 FROM ubicacion")
    ).scalar()
    return int(row)


def find_by_id(id_ubicacion):
    if id_ubicacion is None:
        return None
    try:
        pk = int(id_ubicacion)
    except (TypeError, ValueError):
        return None
    return Location.query.get(pk)


def find_by_nombre(nombre):
    return Location.query.filter_by(nombre=nombre).first()


def list_all():
    locations = Location.query.all()
    return [location.to_dict() for location in locations]


def create_location(nombre, direccion, capacidad, latitud=None, longitud=None):
    location = Location(
        id_ubicacion=next_ubicacion_id(),
        nombre=nombre,
        direccion=direccion,
        capacidad=capacidad,
        latitud=latitud,
        longitud=longitud,
    )
    db.session.add(location)
    db.session.commit()
    db.session.refresh(location)
    return location.to_dict()


def create(name, address, capacity, latitude, longitude):
    """Alias para compatibilidad"""
    return create_location(name, address, capacity, latitude, longitude)


def update_location(id_ubicacion, updates):
    location = find_by_id(id_ubicacion)
    if not location:
        raise ValueError("Ubicación no encontrada")

    for key, value in updates.items():
        if hasattr(location, key) and key in ["nombre", "direccion", "capacidad", "latitud", "longitud"]:
            setattr(location, key, value)

    db.session.commit()
    return location.to_dict()


def update(location_id, updates):
    """Alias para compatibilidad"""
    return update_location(location_id, updates)


def delete_location(id_ubicacion):
    location = find_by_id(id_ubicacion)
    if not location:
        raise ValueError("Ubicación no encontrada")

    db.session.delete(location)
    db.session.commit()


def delete(location_id):
    """Alias para compatibilidad"""
    return delete_location(location_id)
