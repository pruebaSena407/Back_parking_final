import uuid
from datetime import datetime, date
from sqlalchemy import text, ForeignKey

from db import db


# Estados válidos del pago (mismos que tipa el front en paymentService.ts)
PAGO_STATUSES = {"pending", "completed", "failed", "refunded"}

# Métodos que requieren datos de tarjeta (para el mock gateway).
CARD_METHODS = {"credit_card", "debit_card"}


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
    # Datos del comprobante. Nunca se guarda el número completo de tarjeta ni el CVC:
    # sólo el nombre del titular y los últimos 4 dígitos (PCI-friendly).
    nombre_titular = db.Column(db.String(120))
    ultimos4 = db.Column(db.String(4))
    comprobante_emitido_at = db.Column(db.DateTime)
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
            "cardHolder": self.nombre_titular,
            "cardLast4": self.ultimos4,
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
    return [p.to_dict() for p in Pago.query.order_by(Pago.created_at.desc()).all()]


def list_by_reserva(id_reserva):
    return [p.to_dict() for p in Pago.query.filter_by(id_reserva=id_reserva).all()]


def list_by_user(id_usuario):
    """Pagos cuyas reservas pertenecen al usuario indicado (historial propio)."""
    rows = db.session.execute(text(
        """
        SELECT p.id_pago
        FROM pago p
        JOIN reserva r ON r.id_reserva = p.id_reserva
        WHERE r.id_usuario = :uid
        ORDER BY p.created_at DESC
        """
    ), {"uid": int(id_usuario)}).fetchall()
    ids = [row.id_pago for row in rows]
    if not ids:
        return []
    pagos = Pago.query.filter(Pago.id_pago.in_(ids)).all()
    # Reordenamos según el orden de la consulta (created_at desc).
    by_id = {p.id_pago: p.to_dict() for p in pagos}
    return [by_id[i] for i in ids if i in by_id]


def list_by_metodo(metodo_pago):
    return [p.to_dict() for p in Pago.query.filter_by(metodo_pago=metodo_pago).all()]


def _generate_transaction_id():
    """Genera un identificador estilo PV-YYYYMMDDHHMMSS-XXXX."""
    today = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"PV-{today}-{uuid.uuid4().hex[:6].upper()}"


def _luhn_valid(number: str) -> bool:
    """Validación de tarjeta por algoritmo de Luhn (sólo formato, mock)."""
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def create_pago(
    monto,
    metodo_pago,
    id_reserva,
    fecha_pago=None,
    estado="completed",
    transaccion_id=None,
    nombre_titular=None,
    ultimos4=None,
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
        nombre_titular=nombre_titular,
        ultimos4=ultimos4,
        comprobante_emitido_at=datetime.utcnow() if estado == "completed" else None,
    )
    try:
        db.session.add(pago)
        db.session.commit()
        db.session.refresh(pago)
    except Exception:
        db.session.rollback()
        raise

    # Si el pago quedó completado, confirmamos la reserva (estado 'activa').
    if estado == "completed":
        try:
            db.session.execute(
                text("UPDATE reserva SET estado = 'activa', updated_at = :now "
                     "WHERE id_reserva = :pk AND estado = 'pendiente'"),
                {"pk": reserva_pk, "now": datetime.utcnow()},
            )
            db.session.commit()
        except Exception:
            db.session.rollback()

    return pago.to_dict()


def _first_present(payload: dict, *keys):
    """Primer valor != None entre los keys (no descarta 0/'')."""
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return None


def process_payment(payload: dict):
    """
    Pasarela de pagos SIMULADA (mock gateway).

    - Valida monto, método y reserva.
    - Si el método es tarjeta, valida el número con Luhn y guarda sólo los
      últimos 4 dígitos y el nombre del titular (nunca el PAN ni el CVC).
    - Marca el pago como 'completed' y confirma la reserva.
    Devuelve el dict del pago.
    """
    amount = _first_present(payload, "amount", "monto")
    method = _first_present(payload, "method", "metodo_pago")
    reservation_id = _first_present(payload, "reservationId", "id_reserva", "id_registro")

    if amount is None:
        raise ValueError("amount es requerido")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValueError("amount debe ser numérico")
    if amount <= 0:
        raise ValueError("El monto debe ser positivo")
    if not method:
        raise ValueError("method es requerido")
    if reservation_id is None:
        raise ValueError("reservationId es requerido")

    nombre_titular = None
    ultimos4 = None
    estado = payload.get("status") or "completed"

    if method in CARD_METHODS:
        card_number = str(_first_present(payload, "cardNumber", "card_number") or "").replace(" ", "")
        if card_number:
            if not _luhn_valid(card_number):
                raise ValueError("Número de tarjeta inválido")
            ultimos4 = card_number[-4:]
        nombre_titular = _first_present(payload, "cardName", "nombre_titular")

    return create_pago(
        monto=amount,
        metodo_pago=method,
        id_reserva=reservation_id,
        fecha_pago=_first_present(payload, "paymentDate", "fecha_pago"),
        estado=estado,
        nombre_titular=nombre_titular,
        ultimos4=ultimos4,
    )


# Alias por compatibilidad: el controlador antiguo llamaba create_from_payload.
def create_from_payload(payload: dict):
    return process_payment(payload)


def build_receipt(id_pago):
    """
    Devuelve un comprobante de pago enriquecido con los datos de la reserva
    y del pagador, listo para pintar/imprimir en el front.
    """
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")

    row = db.session.execute(text(
        """
        SELECT r.id_reserva, r.hora_inicio, r.hora_fin, r.espacio_codigo,
               u.id_usuario, u.nombre, u.apellido, u.correo,
               ub.nombre AS ubicacion_nombre, ub.direccion AS ubicacion_direccion
        FROM reserva r
        LEFT JOIN usuario u  ON u.id_usuario  = r.id_usuario
        LEFT JOIN ubicacion ub ON ub.id_ubicacion = r.id_ubicacion
        WHERE r.id_reserva = :rid
        """
    ), {"rid": pago.id_reserva}).fetchone()

    payer = None
    reservation = None
    if row is not None:
        payer = {
            "id": row.id_usuario,
            "name": f"{row.nombre or ''} {row.apellido or ''}".strip(),
            "email": row.correo,
        }
        reservation = {
            "id": row.id_reserva,
            "locationName": row.ubicacion_nombre,
            "locationAddress": row.ubicacion_direccion,
            "spaceCode": row.espacio_codigo,
            "startDate": row.hora_inicio.isoformat() if row.hora_inicio else None,
            "endDate": row.hora_fin.isoformat() if row.hora_fin else None,
        }

    return {
        "receiptNumber": pago.transaccion_id,
        "issuedAt": pago.comprobante_emitido_at.isoformat() if pago.comprobante_emitido_at else (
            pago.created_at.isoformat() if pago.created_at else None
        ),
        "amount": pago.monto,
        "currency": "COP",
        "method": pago.metodo_pago,
        "status": pago.estado,
        "cardLast4": pago.ultimos4,
        "cardHolder": pago.nombre_titular,
        "payer": payer,
        "reservation": reservation,
    }


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
