from datetime import datetime, date
from sqlalchemy import text, ForeignKey, Time

from db import db


class Registro(db.Model):
    __tablename__ = "registro"

    id_registro = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida = db.Column(db.Time)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_vehiculo = db.Column(db.Integer, ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_registro": self.id_registro,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "hora_entrada": str(self.hora_entrada) if self.hora_entrada else None,
            "hora_salida": str(self.hora_salida) if self.hora_salida else None,
            "id_usuario": self.id_usuario,
            "id_vehiculo": self.id_vehiculo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_registro_id() -> int:
    """Siguiente id entero acorde a la columna registro.id_registro"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_registro), 0) + 1 FROM registro")
    ).scalar()
    return int(row)


def find_by_id(id_registro):
    if id_registro is None:
        return None
    try:
        pk = int(id_registro)
    except (TypeError, ValueError):
        return None
    return Registro.query.get(pk)


def list_all():
    registros = Registro.query.all()
    return [registro.to_dict() for registro in registros]


def list_by_usuario(id_usuario):
    registros = Registro.query.filter_by(id_usuario=id_usuario).all()
    return [registro.to_dict() for registro in registros]


def list_by_vehiculo(id_vehiculo):
    registros = Registro.query.filter_by(id_vehiculo=id_vehiculo).all()
    return [registro.to_dict() for registro in registros]


def list_by_fecha(fecha):
    registros = Registro.query.filter_by(fecha=fecha).all()
    return [registro.to_dict() for registro in registros]


def create_registro(hora_entrada, id_usuario, id_vehiculo, fecha=None, hora_salida=None):
    if fecha is None:
        fecha = date.today()

    registro = Registro(
        id_registro=next_registro_id(),
        fecha=fecha,
        hora_entrada=hora_entrada,
        hora_salida=hora_salida,
        id_usuario=id_usuario,
        id_vehiculo=id_vehiculo,
    )
    db.session.add(registro)
    db.session.commit()
    db.session.refresh(registro)
    return registro.to_dict()


def update_registro(id_registro, updates):
    registro = find_by_id(id_registro)
    if not registro:
        raise ValueError("Registro no encontrado")

    for key, value in updates.items():
        if hasattr(registro, key) and key in ["fecha", "hora_entrada", "hora_salida", "id_usuario", "id_vehiculo"]:
            setattr(registro, key, value)

    db.session.commit()
    return registro.to_dict()


def delete_registro(id_registro):
    registro = find_by_id(id_registro)
    if not registro:
        raise ValueError("Registro no encontrado")

    db.session.delete(registro)
    db.session.commit()
