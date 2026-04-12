from datetime import datetime
from sqlalchemy import text

from db import db


class Permiso(db.Model):
    __tablename__ = "permiso"

    id_permiso = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_permiso": self.id_permiso,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_permiso_id() -> int:
    """Siguiente id entero acorde a la columna permiso.id_permiso"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_permiso), 0) + 1 FROM permiso")
    ).scalar()
    return int(row)


def find_by_id(id_permiso):
    if id_permiso is None:
        return None
    try:
        pk = int(id_permiso)
    except (TypeError, ValueError):
        return None
    return Permiso.query.get(pk)


def find_by_nombre(nombre):
    return Permiso.query.filter_by(nombre=nombre).first()


def list_all():
    permisos = Permiso.query.all()
    return [permiso.to_dict() for permiso in permisos]


def create_permiso(nombre, descripcion=None):
    if find_by_nombre(nombre):
        raise ValueError("Permiso ya existe")

    permiso = Permiso(
        id_permiso=next_permiso_id(),
        nombre=nombre,
        descripcion=descripcion,
    )
    db.session.add(permiso)
    db.session.commit()
    db.session.refresh(permiso)
    return permiso.to_dict()


def update_permiso(id_permiso, updates):
    permiso = find_by_id(id_permiso)
    if not permiso:
        raise ValueError("Permiso no encontrado")

    for key, value in updates.items():
        if hasattr(permiso, key) and key in ["nombre", "descripcion"]:
            setattr(permiso, key, value)

    db.session.commit()
    return permiso.to_dict()


def delete_permiso(id_permiso):
    permiso = find_by_id(id_permiso)
    if not permiso:
        raise ValueError("Permiso no encontrado")

    db.session.delete(permiso)
    db.session.commit()
