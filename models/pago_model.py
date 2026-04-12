from datetime import datetime, date
from sqlalchemy import text, ForeignKey

from db import db


class Pago(db.Model):
    __tablename__ = "pago"

    id_pago = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False, default=date.today)
    metodo_pago = db.Column(db.String(50), nullable=False)
    id_registro = db.Column(db.Integer, ForeignKey("registro.id_registro"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_pago": self.id_pago,
            "monto": self.monto,
            "fecha_pago": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "metodo_pago": self.metodo_pago,
            "id_registro": self.id_registro,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_pago_id() -> int:
    """Siguiente id entero acorde a la columna pago.id_pago"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_pago), 0) + 1 FROM pago")
    ).scalar()
    return int(row)


def find_by_id(id_pago):
    if id_pago is None:
        return None
    try:
        pk = int(id_pago)
    except (TypeError, ValueError):
        return None
    return Pago.query.get(pk)


def list_all():
    pagos = Pago.query.all()
    return [pago.to_dict() for pago in pagos]


def list_by_registro(id_registro):
    pagos = Pago.query.filter_by(id_registro=id_registro).all()
    return [pago.to_dict() for pago in pagos]


def list_by_metodo(metodo_pago):
    pagos = Pago.query.filter_by(metodo_pago=metodo_pago).all()
    return [pago.to_dict() for pago in pagos]


def create_pago(monto, metodo_pago, id_registro, fecha_pago=None):
    if fecha_pago is None:
        fecha_pago = date.today()

    pago = Pago(
        id_pago=next_pago_id(),
        monto=monto,
        fecha_pago=fecha_pago,
        metodo_pago=metodo_pago,
        id_registro=id_registro,
    )
    db.session.add(pago)
    db.session.commit()
    db.session.refresh(pago)
    return pago.to_dict()


def update_pago(id_pago, updates):
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")

    for key, value in updates.items():
        if hasattr(pago, key) and key in ["monto", "fecha_pago", "metodo_pago", "id_registro"]:
            setattr(pago, key, value)

    db.session.commit()
    return pago.to_dict()


def delete_pago(id_pago):
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")

    db.session.delete(pago)
    db.session.commit()
