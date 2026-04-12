from datetime import datetime, date
from sqlalchemy import text, ForeignKey

from db import db


class Incidente(db.Model):
    __tablename__ = "incidente"

    id_incidente = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(500), nullable=False)
    fecha_incidente = db.Column(db.Date, nullable=False, default=date.today)
    id_registro = db.Column(db.Integer, ForeignKey("registro.id_registro"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_incidente": self.id_incidente,
            "descripcion": self.descripcion,
            "fecha_incidente": self.fecha_incidente.isoformat() if self.fecha_incidente else None,
            "id_registro": self.id_registro,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_incidente_id() -> int:
    """Siguiente id entero acorde a la columna incidente.id_incidente"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_incidente), 0) + 1 FROM incidente")
    ).scalar()
    return int(row)


def find_by_id(id_incidente):
    if id_incidente is None:
        return None
    try:
        pk = int(id_incidente)
    except (TypeError, ValueError):
        return None
    return Incidente.query.get(pk)


def list_all():
    incidentes = Incidente.query.all()
    return [incidente.to_dict() for incidente in incidentes]


def list_by_registro(id_registro):
    incidentes = Incidente.query.filter_by(id_registro=id_registro).all()
    return [incidente.to_dict() for incidente in incidentes]


def list_by_fecha(fecha_incidente):
    incidentes = Incidente.query.filter_by(fecha_incidente=fecha_incidente).all()
    return [incidente.to_dict() for incidente in incidentes]


def create_incidente(descripcion, id_registro, fecha_incidente=None):
    if fecha_incidente is None:
        fecha_incidente = date.today()

    incidente = Incidente(
        id_incidente=next_incidente_id(),
        descripcion=descripcion,
        fecha_incidente=fecha_incidente,
        id_registro=id_registro,
    )
    db.session.add(incidente)
    db.session.commit()
    db.session.refresh(incidente)
    return incidente.to_dict()


def update_incidente(id_incidente, updates):
    incidente = find_by_id(id_incidente)
    if not incidente:
        raise ValueError("Incidente no encontrado")

    for key, value in updates.items():
        if hasattr(incidente, key) and key in ["descripcion", "fecha_incidente", "id_registro"]:
            setattr(incidente, key, value)

    db.session.commit()
    return incidente.to_dict()


def delete_incidente(id_incidente):
    incidente = find_by_id(id_incidente)
    if not incidente:
        raise ValueError("Incidente no encontrado")

    db.session.delete(incidente)
    db.session.commit()
