import uuid
from datetime import datetime, date
from sqlalchemy import text, ForeignKey

from db import db


# Estados válidos del pago (mismos que tipa el front en paymentService.ts)
PAGO_STATUSES = {"pending", "completed", "failed", "refunded"}


class Pago(db.Model):
    __tablename__ = "pago"

    id_pago = db.Column(db.Integer, primary_key=True)
    monto = db.Column(db.Float, nullable=False)
    fecha_pago = db.Column(db.Date, nullable=False, default=date.today)
    metodo_pago = db.Column(db.String(50), nullable=False)
    # Antes era id_registro; ahora apunta directo a la reserva.
    id_reserva = db.Column(db.Integer, ForeignKey("reserva.id_reserva"), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="completed")
    transaccion_id = db.Column(db.String(64), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """
        Devuelve el formato camelCase que el front ya tiene tipado en
        `Front_parking_final/src/services/paymentService.ts`.
        """
        return {
            "id": self.id_pago,
            "reservationId": self.id_reserva,
            "amount": self.monto,
            "status": self.estado,
            "method": self.metodo_pago,
            "transactionId": self.transaccion_id,
            "paymentDate": self.fecha_pago.isoformat() if self.fecha_pago else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


def next_pago_id() -> int:
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
    return [p.to_dict() for p in Pago.query.all()]


def list_by_reserva(id_reserva):
    return [p.to_dict() for p in Pago.query.filter_by(id_reserva=id_reserva).all()]


def list_by_metodo(metodo_pago):
    return [p.to_dict() for p in Pago.query.filter_by(metodo_pago=metodo_pago).all()]


def _generate_transaction_id():
    """Genera un identificador estilo PV-YYYYMMDDHHMMSS-XXXX."""
    today = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PV-{today}-{uuid.uuid4().hex[:6].upper()}"


def create_pago(
    monto,
    metodo_pago,
    id_reserva,
    fecha_pago=None,
    estado="completed",
    transaccion_id=None,
):
    if estado not in PAGO_STATUSES:
        raise ValueError(f"Estado de pago inválido: {estado}")
    if fecha_pago is None:
        fecha_pago = date.today()
    elif isinstance(fecha_pago, str):
        try:
            fecha_pago = date.fromisoformat(fecha_pago)
        except ValueError:
            fecha_pago = date.today()

    # Validamos que la reserva exista; sin esto la FK arroja un error
    # críptico de psycopg2 difícil de mostrar al usuario.
    reserva_pk = int(id_reserva)
    reserva_exists = db.session.execute(
        text("SELECT 1 FROM reserva WHERE id_reserva = :pk"),
        {"pk": reserva_pk},
    ).scalar()
    if not reserva_exists:
        raise ValueError(f"La reserva {reserva_pk} no existe")

    pago = Pago(
        id_pago=next_pago_id(),
        monto=float(monto),
        fecha_pago=fecha_pago,
        metodo_pago=metodo_pago,
        id_reserva=reserva_pk,
        estado=estado,
        transaccion_id=transaccion_id or _generate_transaction_id(),
    )
    try:
        db.session.add(pago)
        db.session.commit()
        db.session.refresh(pago)
    except Exception:
        db.session.rollback()
        raise
    return pago.to_dict()


def _first_present(payload: dict, *keys):
    """Primer valor != None entre los keys (no descarta 0/'')."""
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return None


def create_from_payload(payload: dict):
    """Acepta camelCase del front + nombres internos."""
    amount = _first_present(payload, "amount", "monto")
    method = _first_present(payload, "method", "metodo_pago")
    reservation_id = _first_present(
        payload, "reservationId", "id_reserva", "id_registro"
    )

    if amount is None:
        raise ValueError("amount es requerido")
    if not method:
        raise ValueError("method es requerido")
    if reservation_id is None:
        raise ValueError("reservationId es requerido")

    return create_pago(
        monto=amount,
        metodo_pago=method,
        id_reserva=reservation_id,
        fecha_pago=_first_present(payload, "paymentDate", "fecha_pago"),
        estado=payload.get("status") or "completed",
    )


def update_pago(id_pago, updates: dict):
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")

    field_map = {
        "amount": "monto",
        "monto": "monto",
        "method": "metodo_pago",
        "metodo_pago": "metodo_pago",
        "reservationId": "id_reserva",
        "id_reserva": "id_reserva",
        "status": "estado",
        "estado": "estado",
        "paymentDate": "fecha_pago",
        "fecha_pago": "fecha_pago",
        "transactionId": "transaccion_id",
        "transaccion_id": "transaccion_id",
    }
    for key, value in updates.items():
        column = field_map.get(key)
        if not column:
            continue
        if column == "estado" and value not in PAGO_STATUSES:
            raise ValueError(f"Estado inválido: {value}")
        if column == "fecha_pago" and isinstance(value, str):
            try:
                value = date.fromisoformat(value)
            except ValueError:
                continue
        if column == "monto" and isinstance(value, str):
            value = float(value) if value.strip() else 0.0
        setattr(pago, column, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pago.to_dict()


def refund_pago(id_pago):
    """Marca el pago como reembolsado."""
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")
    pago.estado = "refunded"
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pago.to_dict()


def delete_pago(id_pago):
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")
    try:
        db.session.delete(pago)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
