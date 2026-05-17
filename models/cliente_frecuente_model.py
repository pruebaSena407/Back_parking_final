# =====================================================================
# MODELO CLIENTE FRECUENTE (cliente_frecuente_model.py)
# ---------------------------------------------------------------------
# Tabla auxiliar para guardar los datos del formulario de "registro de
# usuario frecuente" del front. Vincula un usuario y un vehículo y
# añade campos extra (documento, dirección, sede preferida).
# =====================================================================

from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db


class ClienteFrecuente(db.Model):
    __tablename__ = "cliente_frecuente"

    id_cliente_frecuente = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_vehiculo = db.Column(db.Integer, ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    tipo_documento = db.Column(db.String(20))
    numero_documento = db.Column(db.String(40))
    direccion = db.Column(db.String(255))
    sede_preferida = db.Column(db.String(150))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id_cliente_frecuente,
            "userId": self.id_usuario,
            "vehicleId": self.id_vehiculo,
            "documentType": self.tipo_documento,
            "documentNumber": self.numero_documento,
            "address": self.direccion,
            "preferredLocation": self.sede_preferida,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_cliente_frecuente_id() -> int:
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_cliente_frecuente), 0) + 1 FROM cliente_frecuente")
    ).scalar()
    return int(row)


def find_by_usuario(id_usuario):
    return ClienteFrecuente.query.filter_by(id_usuario=id_usuario).first()


def list_all():
    return [c.to_dict() for c in ClienteFrecuente.query.all()]


def create_cliente_frecuente(
    id_usuario,
    id_vehiculo,
    tipo_documento=None,
    numero_documento=None,
    direccion=None,
    sede_preferida=None,
):
    record = ClienteFrecuente(
        id_cliente_frecuente=next_cliente_frecuente_id(),
        id_usuario=id_usuario,
        id_vehiculo=id_vehiculo,
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        direccion=direccion,
        sede_preferida=sede_preferida,
    )
    try:
        db.session.add(record)
        db.session.commit()
        db.session.refresh(record)
    except Exception:
        db.session.rollback()
        raise
    return record.to_dict()
