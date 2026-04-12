from datetime import datetime, date
from sqlalchemy import text, ForeignKey

from db import db


class ObjetoOlvidado(db.Model):
    __tablename__ = "objeto_olvidado"

    id_objeto_olvidado = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(500), nullable=False)
    fecha_encontrado = db.Column(db.Date, nullable=False, default=date.today)
    id_registro = db.Column(db.Integer, ForeignKey("registro.id_registro"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_objeto_olvidado": self.id_objeto_olvidado,
            "descripcion": self.descripcion,
            "fecha_encontrado": self.fecha_encontrado.isoformat() if self.fecha_encontrado else None,
            "id_registro": self.id_registro,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_objeto_id() -> int:
    """Siguiente id entero acorde a la columna objeto_olvidado.id_objeto_olvidado"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_objeto_olvidado), 0) + 1 FROM objeto_olvidado")
    ).scalar()
    return int(row)


def find_by_id(id_objeto_olvidado):
    if id_objeto_olvidado is None:
        return None
    try:
        pk = int(id_objeto_olvidado)
    except (TypeError, ValueError):
        return None
    return ObjetoOlvidado.query.get(pk)


def list_all():
    objetos = ObjetoOlvidado.query.all()
    return [objeto.to_dict() for objeto in objetos]


def list_by_registro(id_registro):
    objetos = ObjetoOlvidado.query.filter_by(id_registro=id_registro).all()
    return [objeto.to_dict() for objeto in objetos]


def list_by_fecha(fecha_encontrado):
    objetos = ObjetoOlvidado.query.filter_by(fecha_encontrado=fecha_encontrado).all()
    return [objeto.to_dict() for objeto in objetos]


def create_objeto(descripcion, id_registro, fecha_encontrado=None):
    if fecha_encontrado is None:
        fecha_encontrado = date.today()

    objeto = ObjetoOlvidado(
        id_objeto_olvidado=next_objeto_id(),
        descripcion=descripcion,
        fecha_encontrado=fecha_encontrado,
        id_registro=id_registro,
    )
    db.session.add(objeto)
    db.session.commit()
    db.session.refresh(objeto)
    return objeto.to_dict()


def update_objeto(id_objeto_olvidado, updates):
    objeto = find_by_id(id_objeto_olvidado)
    if not objeto:
        raise ValueError("Objeto olvidado no encontrado")

    for key, value in updates.items():
        if hasattr(objeto, key) and key in ["descripcion", "fecha_encontrado", "id_registro"]:
            setattr(objeto, key, value)

    db.session.commit()
    return objeto.to_dict()


def delete_objeto(id_objeto_olvidado):
    objeto = find_by_id(id_objeto_olvidado)
    if not objeto:
        raise ValueError("Objeto olvidado no encontrado")

    db.session.delete(objeto)
    db.session.commit()
