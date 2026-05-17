# =====================================================================
# MODELO DE RESERVA (reservation_model.py)
# ---------------------------------------------------------------------
# Define la tabla "reserva" y las funciones para crear, listar,
# actualizar y borrar reservas de parqueadero.
#
# Una reserva relaciona:
#   - Un USUARIO (quien reserva)
#   - Una UBICACIÓN (qué parqueadero)
#   - Un rango de horas (inicio y fin)
# =====================================================================

from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db


# ---------------------------------------------------------------------
# CLASE RESERVA: representa la tabla "reserva"
# ---------------------------------------------------------------------
class Reserva(db.Model):
    __tablename__ = "reserva"

    id_reserva = db.Column(db.Integer, primary_key=True)
    # ForeignKey indica que esta columna apunta a otra tabla.
    # Esto crea una relación: cada reserva pertenece a UN usuario.
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    # Cada reserva también está asociada a UNA ubicación (parqueadero).
    id_ubicacion = db.Column(db.Integer, ForeignKey("ubicacion.id_ubicacion"), nullable=False)
    # Código del espacio (ejemplo: "A-12"). Es opcional.
    espacio_codigo = db.Column(db.String(50))
    hora_inicio = db.Column(db.DateTime, nullable=False)
    hora_fin = db.Column(db.DateTime, nullable=False)
    # Estado: activa, completada, cancelada, etc. Por defecto, "activa".
    estado = db.Column(db.String(50), default="activa")
    monto = db.Column(db.Float)  # cuánto cuesta la reserva
    notas = db.Column(db.String(500))  # observaciones opcionales
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convierte la reserva a un diccionario (para mandarla como JSON)."""
        return {
            "id_reserva": self.id_reserva,
            "id_usuario": self.id_usuario,
            "id_ubicacion": self.id_ubicacion,
            "espacio_codigo": self.espacio_codigo,
            # isoformat() vuelve las fechas en strings tipo "2026-05-17T12:00:00"
            "hora_inicio": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "hora_fin": self.hora_fin.isoformat() if self.hora_fin else None,
            "estado": self.estado,
            "monto": self.monto,
            "notas": self.notas,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES (CRUD de reservas)
# ---------------------------------------------------------------------

def next_reserva_id() -> int:
    """Calcula el siguiente id_reserva (max + 1)."""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_reserva), 0) + 1 FROM reserva")
    ).scalar()
    return int(row)


def find_by_id(reservation_id):
    """Busca una reserva por su id. Devuelve None si no existe o el id es inválido."""
    if reservation_id is None:
        return None
    try:
        pk = int(reservation_id)
    except (TypeError, ValueError):
        return None
    return Reserva.query.get(pk)


def list_all():
    """Lista TODAS las reservas (uso para admin)."""
    reservas = Reserva.query.all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_user(user_id):
    """Lista las reservas de UN usuario específico (útil para su dashboard)."""
    reservas = Reserva.query.filter_by(id_usuario=user_id).all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_usuario(id_usuario):
    """Mismo que list_by_user, mantenemos este nombre por compatibilidad con código viejo."""
    return list_by_user(id_usuario)


def list_by_ubicacion(id_ubicacion):
    """Lista las reservas hechas en una ubicación específica."""
    reservas = Reserva.query.filter_by(id_ubicacion=id_ubicacion).all()
    return [reserva.to_dict() for reserva in reservas]


def list_by_estado(estado):
    """Lista las reservas filtradas por su estado (activa/completada/cancelada)."""
    reservas = Reserva.query.filter_by(estado=estado).all()
    return [reserva.to_dict() for reserva in reservas]


def create_reserva(id_usuario, id_ubicacion, hora_inicio, hora_fin, espacio_codigo=None, monto=None, notas=None):
    """
    Crea una reserva nueva. El estado siempre arranca en "activa".
    Los parámetros con = significan que son opcionales.
    """
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
    """Alias en inglés por compatibilidad con código antiguo."""
    return create_reserva(user_id, location_name, start_time, end_time, space_code, amount, notes)


def update_reserva(id_reserva, updates):
    """
    Actualiza una reserva. Solo permite cambiar los campos seguros listados
    en el if (whitelist).
    """
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    for key, value in updates.items():
        # Solo dejamos modificar estos campos por seguridad
        if hasattr(reserva, key) and key in ["id_usuario", "id_ubicacion", "espacio_codigo", "hora_inicio", "hora_fin", "estado", "monto", "notas"]:
            setattr(reserva, key, value)

    db.session.commit()
    return reserva.to_dict()


def update(reservation_id, updates):
    """Alias por compatibilidad."""
    return update_reserva(reservation_id, updates)


def delete_reserva(id_reserva):
    """Elimina la reserva indicada de la BD."""
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    db.session.delete(reserva)
    db.session.commit()


def delete(reservation_id):
    """Alias por compatibilidad."""
    return delete_reserva(reservation_id)
