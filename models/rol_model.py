from datetime import datetime
from sqlalchemy import text

from db import db


class Rol(db.Model):
    __tablename__ = "rol"

    id_rol = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_rol": self.id_rol,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_rol_id() -> int:
    """Siguiente id entero acorde a la columna rol.id_rol"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_rol), 0) + 1 FROM rol")
    ).scalar()
    return int(row)


def find_by_id(id_rol):
    if id_rol is None:
        return None
    try:
        pk = int(id_rol)
    except (TypeError, ValueError):
        return None
    return Rol.query.get(pk)


def find_by_nombre(nombre):
    return Rol.query.filter_by(nombre=nombre).first()


def list_all():
    roles = Rol.query.all()
    return [rol.to_dict() for rol in roles]


def create_rol(nombre, descripcion=None):
    if find_by_nombre(nombre):
        raise ValueError("Rol ya existe")

    rol = Rol(
        id_rol=next_rol_id(),
        nombre=nombre,
        descripcion=descripcion,
    )
    db.session.add(rol)
    db.session.commit()
    db.session.refresh(rol)
    return rol.to_dict()


def update_rol(id_rol, updates):
    rol = find_by_id(id_rol)
    if not rol:
        raise ValueError("Rol no encontrado")

    for key, value in updates.items():
        if hasattr(rol, key) and key in ["nombre", "descripcion"]:
            setattr(rol, key, value)

    db.session.commit()
    return rol.to_dict()


def delete_rol(id_rol):
    rol = find_by_id(id_rol)
    if not rol:
        raise ValueError("Rol no encontrado")

    db.session.delete(rol)
    db.session.commit()
