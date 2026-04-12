from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db


class Reserva(db.Model):
    __tablename__ = "reserva"

    id_reserva = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_ubicacion = db.Column(db.Integer, ForeignKey("ubicacion.id_ubicacion"), nullable=False)
    espacio_codigo = db.Column(db.String(50))
    hora_inicio = db.Column(db.DateTime, nullable=False)
    hora_fin = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.String(50), default="activa")
    monto = db.Column(db.Float)
    notas = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id_reserva": self.id_reserva,
            "id_usuario": self.id_usuario,
            "id_ubicacion": self.id_ubicacion,
            "espacio_codigo": self.espacio_codigo,
            "hora_inicio": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "hora_fin": self.hora_fin.isoformat() if self.hora_fin else None,
            "estado": self.estado,
            "monto": self.monto,
            "notas": self.notas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_reserva_id() -> int:
    """Siguiente id entero acorde a la columna reserva.id_reserva"""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_reserva), 0) + 1 FROM reserva")
    ).scalar()
    return int(row)


def find_by_id(reservation_id):
    if reservation_id is None:
        return None
    try:
        pk = int(reservation_id)
    except (TypeError, ValueError):
        return None
    return Reserva.query.get(pk)


def list_all():
    reservas = Reserva.query.all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_user(user_id):
    reservas = Reserva.query.filter_by(id_usuario=user_id).all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_usuario(id_usuario):
    """Alias para compatibilidad"""
    return list_by_user(id_usuario)


def list_by_ubicacion(id_ubicacion):
    reservas = Reserva.query.filter_by(id_ubicacion=id_ubicacion).all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_estado(estado):
    reservas = Reserva.query.filter_by(estado=estado).all()
    return [reserva.to_dict() for reserva in reservas]


def create_reserva(id_usuario, id_ubicacion, hora_inicio, hora_fin, espacio_codigo=None, monto=None, notas=None):
    reserva = Reserva(
        id_reserva=next_reserva_id(),
        id_usuario=id_usuario,
        id_ubicacion=id_ubicacion,
        espacio_codigo=espacio_codigo,
        hora_inicio=hora_inicio,
        hora_fin=hora_fin,
        estado="activa",
        monto=monto,
        notas=notas,
    )
    db.session.add(reserva)
    db.session.commit()
    db.session.refresh(reserva)
    return reserva.to_dict()


def create(user_id, location_name, start_time, end_time, space_code=None, amount=None, notes=None):
    """Alias para compatibilidad"""
    return create_reserva(user_id, location_name, start_time, end_time, space_code, amount, notes)


def update_reserva(id_reserva, updates):
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    for key, value in updates.items():
        if hasattr(reserva, key) and key in ["id_usuario", "id_ubicacion", "espacio_codigo", "hora_inicio", "hora_fin", "estado", "monto", "notas"]:
            setattr(reserva, key, value)

    db.session.commit()
    return reserva.to_dict()


def update(reservation_id, updates):
    """Alias para compatibilidad"""
    return update_reserva(reservation_id, updates)


def delete_reserva(id_reserva):
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    db.session.delete(reserva)
    db.session.commit()


def delete(reservation_id):
    """Alias para compatibilidad"""
    return delete_reserva(reservation_id)
