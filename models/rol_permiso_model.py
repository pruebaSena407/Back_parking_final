from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db


class RolPermiso(db.Model):
    __tablename__ = "rol_permiso"

    id_rol_permiso = db.Column(db.Integer, primary_key=True)
    id_rol = db.Column(db.Integer, ForeignKey("rol.id_rol"), nullable=False)
    id_permiso = db.Column(db.Integer, ForeignKey("permiso.id_permiso"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_rol_permiso": self.id_rol_permiso,
            "id_rol": self.id_rol,
            "id_permiso": self.id_permiso,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_rol_permiso_id() -> int:
    """Siguiente id entero acorde a la columna rol_permiso.id_rol_permiso"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_rol_permiso), 0) + 1 FROM rol_permiso")
    ).scalar()
    return int(row)


def find_by_id(id_rol_permiso):
    if id_rol_permiso is None:
        return None
    try:
        pk = int(id_rol_permiso)
    except (TypeError, ValueError):
        return None
    return RolPermiso.query.get(pk)


def find_by_rol_permiso(id_rol, id_permiso):
    return RolPermiso.query.filter_by(id_rol=id_rol, id_permiso=id_permiso).first()


def list_all():
    links = RolPermiso.query.all()
    return [link.to_dict() for link in links]


def list_by_rol(id_rol):
    links = RolPermiso.query.filter_by(id_rol=id_rol).all()
    return [link.to_dict() for link in links]


def list_by_permiso(id_permiso):
    links = RolPermiso.query.filter_by(id_permiso=id_permiso).all()
    return [link.to_dict() for link in links]


def create_rol_permiso(id_rol, id_permiso):
    if find_by_rol_permiso(id_rol, id_permiso):
        raise ValueError("Vinculación ya existe")

    rol_permiso = RolPermiso(
        id_rol_permiso=next_rol_permiso_id(),
        id_rol=id_rol,
        id_permiso=id_permiso,
    )
    db.session.add(rol_permiso)
    db.session.commit()
    db.session.refresh(rol_permiso)
    return rol_permiso.to_dict()


def update_rol_permiso(id_rol_permiso, updates):
    rol_permiso = find_by_id(id_rol_permiso)
    if not rol_permiso:
        raise ValueError("Vinculación rol-permiso no encontrada")

    for key, value in updates.items():
        if hasattr(rol_permiso, key) and key in ["id_rol", "id_permiso"]:
            setattr(rol_permiso, key, value)

    db.session.commit()
    return rol_permiso.to_dict()


def delete_rol_permiso(id_rol_permiso):
    rol_permiso = find_by_id(id_rol_permiso)
    if not rol_permiso:
        raise ValueError("Vinculación rol-permiso no encontrada")

    db.session.delete(rol_permiso)
    db.session.commit()


def delete_link(id_rol, id_permiso):
    """Elimina vinculación específica entre rol y permiso"""
    rol_permiso = find_by_rol_permiso(id_rol, id_permiso)
    if rol_permiso:
        db.session.delete(rol_permiso)
        db.session.commit()
