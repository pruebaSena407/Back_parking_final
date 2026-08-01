# =====================================================================
# MODELO DE RESERVA (reservation_model.py)
# ---------------------------------------------------------------------
# Define la tabla "reserva" y las funciones para crear, listar,
# actualizar y borrar reservas de parqueadero.
#
# Una reserva relaciona:
#   - Un USUARIO (quien reserva)
#   - Una UBICACIÓN (qué parqueadero)
#   - Un VEHÍCULO (con qué auto/moto)
#   - Un rango de horas (inicio y fin)
# =====================================================================

from datetime import datetime
from sqlalchemy import text, ForeignKey

from db import db
from models import location_model, vehiculo_model


# ---------------------------------------------------------------------
# MAPEO DE ESTADOS (BD ↔ contrato del front)
# ---------------------------------------------------------------------
# El frontend trabaja con: pending | confirmed | cancelled | completed
# La BD guarda en español: pendiente | activa | cancelada | completada
# Estas dos tablas hacen la traducción ida y vuelta.
DB_TO_FRONT_STATUS = {
    "pendiente": "pending",
    "activa": "confirmed",
    "cancelada": "cancelled",
    "completada": "completed",
}
FRONT_TO_DB_STATUS = {v: k for k, v in DB_TO_FRONT_STATUS.items()}


def to_front_status(db_status):
    return DB_TO_FRONT_STATUS.get(db_status, db_status)


def to_db_status(front_status):
    return FRONT_TO_DB_STATUS.get(front_status, front_status)


# ---------------------------------------------------------------------
# CLASE RESERVA: representa la tabla "reserva"
# ---------------------------------------------------------------------
class Reserva(db.Model):
    __tablename__ = "reserva"

    id_reserva = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_ubicacion = db.Column(db.Integer, ForeignKey("ubicacion.id_ubicacion"), nullable=False)
    # id_vehiculo es opcional: el front lo manda como string en
    # CreateReservationRequest, pero algunas reservas viejas no tienen vehículo.
    id_vehiculo = db.Column(db.Integer, ForeignKey("vehiculo.id_vehiculo"))
    espacio_codigo = db.Column(db.String(50))
    hora_inicio = db.Column(db.DateTime, nullable=False)
    hora_fin = db.Column(db.DateTime, nullable=False)
    # Estado en español: pendiente / activa / cancelada / completada.
    estado = db.Column(db.String(50), default="activa")
    monto = db.Column(db.Float)
    notas = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """
        Devuelve el formato camelCase que el frontend ya tiene tipado
        en `Front_parking_final/src/services/reservationService.ts`.
        """
        return {
            "id": self.id_reserva,
            "userId": str(self.id_usuario) if self.id_usuario is not None else None,
            "locationId": self.id_ubicacion,
            "vehicleId": str(self.id_vehiculo) if self.id_vehiculo is not None else None,
            "spaceCode": self.espacio_codigo,
            "startDate": self.hora_inicio.isoformat() if self.hora_inicio else None,
            "endDate": self.hora_fin.isoformat() if self.hora_fin else None,
            "status": to_front_status(self.estado),
            "totalPrice": self.monto,
            "notes": self.notas,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
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


def _list_expanded(where_sql="", params=None):
    """
    Lista reservas con nombre de ubicación, nombre del cliente y placa del
    vehículo resueltos en una sola consulta (evita N+1 y muestra datos
    legibles en la UI en vez de IDs crudos).
    """
    rows = db.session.execute(text(
        f"""
        SELECT r.id_reserva, r.id_usuario, r.id_ubicacion, r.id_vehiculo,
               r.espacio_codigo, r.hora_inicio, r.hora_fin, r.estado,
               r.monto, r.notas, r.created_at, r.updated_at,
               ub.nombre AS ubicacion_nombre,
               u.nombre AS usuario_nombre, u.apellido AS usuario_apellido,
               v.placa AS vehiculo_placa
        FROM reserva r
        LEFT JOIN ubicacion ub ON ub.id_ubicacion = r.id_ubicacion
        LEFT JOIN usuario u    ON u.id_usuario    = r.id_usuario
        LEFT JOIN vehiculo v   ON v.id_vehiculo   = r.id_vehiculo
        {where_sql}
        ORDER BY r.hora_inicio DESC
        """
    ), params or {}).fetchall()

    result = []
    for row in rows:
        nombre = f"{row.usuario_nombre or ''} {row.usuario_apellido or ''}".strip()
        result.append({
            "id": row.id_reserva,
            "userId": str(row.id_usuario) if row.id_usuario is not None else None,
            "userName": nombre or None,
            "locationId": row.id_ubicacion,
            "locationName": row.ubicacion_nombre,
            "vehicleId": str(row.id_vehiculo) if row.id_vehiculo is not None else None,
            "vehiclePlate": row.vehiculo_placa,
            "spaceCode": row.espacio_codigo,
            "startDate": row.hora_inicio.isoformat() if row.hora_inicio else None,
            "endDate": row.hora_fin.isoformat() if row.hora_fin else None,
            "status": to_front_status(row.estado),
            "totalPrice": row.monto,
            "notes": row.notas,
            "createdAt": row.created_at.isoformat() if row.created_at else None,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        })
    return result


def list_all():
    """Lista TODAS las reservas (uso para admin), con nombres resueltos."""
    return _list_expanded()


def list_by_user(user_id):
    """Lista las reservas de UN usuario específico (útil para su dashboard)."""
    return _list_expanded("WHERE r.id_usuario = :uid", {"uid": int(user_id)})


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


def _resolve_location_id(location_value):
    """
    Acepta:
      - int / str numérico → se interpreta como id_ubicacion directo.
      - string → se busca por nombre en la tabla ubicacion.
    Devuelve un id_ubicacion entero o lanza ValueError.
    """
    if location_value is None:
        raise ValueError("locationId/locationName es obligatorio")
    if isinstance(location_value, int) and not isinstance(location_value, bool):
        return location_value
    s = str(location_value).strip()
    if s.isdigit():
        return int(s)
    located = location_model.find_by_nombre(s)
    if not located:
        raise ValueError(f"Ubicación '{s}' no encontrada")
    return located.id_ubicacion


def _resolve_vehicle_id(vehicle_value):
    """
    Acepta:
      - int / str numérico → id_vehiculo directo.
      - string con placa → busca en la tabla vehiculo.
      - None / vacío → devuelve None.
    """
    if vehicle_value is None:
        return None
    if isinstance(vehicle_value, int) and not isinstance(vehicle_value, bool):
        return vehicle_value
    s = str(vehicle_value).strip()
    if not s:
        return None
    if s.isdigit():
        return int(s)
    vehicle = vehiculo_model.find_by_placa(s)
    return vehicle.id_vehiculo if vehicle else None


def _parse_datetime(value):
    """Convierte un string ISO o datetime al objeto datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    s = str(value).strip()
    if not s:
        return None
    # Aceptamos también el formato del input datetime-local ("YYYY-MM-DDTHH:MM")
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if "T" in s else datetime.fromisoformat(s)


def create_reserva(
    id_usuario,
    id_ubicacion,
    hora_inicio,
    hora_fin,
    id_vehiculo=None,
    espacio_codigo=None,
    monto=None,
    notas=None,
    estado="activa",
):
    """Inserta una reserva resolviendo IDs y parseando fechas."""
    location_pk = _resolve_location_id(id_ubicacion)
    vehicle_pk = _resolve_vehicle_id(id_vehiculo)

    # Convertimos el monto a float si llegó como string (el front a
    # veces manda los números como texto desde un input).
    if isinstance(monto, str):
        monto = float(monto) if monto.strip() else None

    reserva = Reserva(
        id_reserva=next_reserva_id(),
        id_usuario=int(id_usuario) if id_usuario is not None else None,
        id_ubicacion=location_pk,
        id_vehiculo=vehicle_pk,
        espacio_codigo=espacio_codigo,
        hora_inicio=_parse_datetime(hora_inicio),
        hora_fin=_parse_datetime(hora_fin),
        estado=to_db_status(estado),
        monto=monto,
        notas=notas,
    )
    try:
        db.session.add(reserva)
        db.session.commit()
        db.session.refresh(reserva)
    except Exception:
        db.session.rollback()
        raise
    return reserva.to_dict()


def _first_present(payload: dict, *keys):
    """
    Devuelve el PRIMER valor distinto de None entre los keys indicados.
    A diferencia de `a or b or c`, NO descarta valores "falsy" como 0,
    "" o False (importante para `totalPrice = 0`).
    """
    for k in keys:
        if k in payload and payload[k] is not None:
            return payload[k]
    return None


def create_from_payload(payload: dict):
    """
    Helper que usa el controlador. Acepta camelCase del front
    (`userId`, `locationId`, `locationName`, `vehicleId`, `startDate`,
    `endDate`, `totalPrice`, `notes`, `spaceCode`) y delega en
    `create_reserva`.
    """
    user_id = _first_present(payload, "userId", "id_usuario")
    location_value = _first_present(
        payload, "locationId", "locationName", "id_ubicacion", "location_name"
    )
    vehicle_value = _first_present(payload, "vehicleId", "id_vehiculo")
    start = _first_present(payload, "startDate", "hora_inicio", "start_time")
    end = _first_present(payload, "endDate", "hora_fin", "end_time")
    space = _first_present(payload, "spaceCode", "espacio_codigo", "space_code")
    amount = _first_present(payload, "totalPrice", "monto", "amount")
    notes = _first_present(payload, "notes", "notas")

    if user_id is None or user_id == "":
        raise ValueError("userId es obligatorio")
    if location_value is None or location_value == "":
        raise ValueError("locationId o locationName son obligatorios")
    if not start or not end:
        raise ValueError("startDate y endDate son obligatorios")

    return create_reserva(
        id_usuario=user_id,
        id_ubicacion=location_value,
        hora_inicio=start,
        hora_fin=end,
        id_vehiculo=vehicle_value,
        espacio_codigo=space,
        monto=amount,
        notas=notes,
        estado=payload.get("status") or "activa",
    )


# Alias por compatibilidad con código que aún llama `create(...)` con
# argumentos posicionales tipo (user_id, location_name, start, end, ...).
def create(user_id, location_name, start_time, end_time, space_code=None, amount=None, notes=None, vehicle_id=None):
    return create_reserva(
        id_usuario=user_id,
        id_ubicacion=location_name,
        hora_inicio=start_time,
        hora_fin=end_time,
        id_vehiculo=vehicle_id,
        espacio_codigo=space_code,
        monto=amount,
        notas=notes,
    )


def update_reserva(id_reserva, updates: dict):
    """
    Actualiza una reserva. Acepta tanto los nombres del front (`userId`,
    `locationId`, `vehicleId`, `startDate`, `endDate`, `status`,
    `totalPrice`, `notes`, `spaceCode`) como los nombres internos.
    """
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    field_map = {
        "userId": "id_usuario",
        "id_usuario": "id_usuario",
        "locationId": "id_ubicacion",
        "id_ubicacion": "id_ubicacion",
        "locationName": "id_ubicacion",
        "location_name": "id_ubicacion",
        "vehicleId": "id_vehiculo",
        "id_vehiculo": "id_vehiculo",
        "spaceCode": "espacio_codigo",
        "espacio_codigo": "espacio_codigo",
        "space_code": "espacio_codigo",
        "startDate": "hora_inicio",
        "hora_inicio": "hora_inicio",
        "start_time": "hora_inicio",
        "endDate": "hora_fin",
        "hora_fin": "hora_fin",
        "end_time": "hora_fin",
        "status": "estado",
        "estado": "estado",
        "totalPrice": "monto",
        "monto": "monto",
        "amount": "monto",
        "notes": "notas",
        "notas": "notas",
    }

    for key, value in updates.items():
        column = field_map.get(key)
        if not column:
            continue
        if column == "id_ubicacion":
            value = _resolve_location_id(value)
        elif column == "id_vehiculo":
            value = _resolve_vehicle_id(value)
        elif column in ("hora_inicio", "hora_fin"):
            value = _parse_datetime(value)
        elif column == "estado" and value:
            value = to_db_status(value)
        elif column == "monto" and isinstance(value, str):
            value = float(value) if value.strip() else None
        setattr(reserva, column, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return reserva.to_dict()


def update(reservation_id, updates):
    """Alias por compatibilidad."""
    return update_reserva(reservation_id, updates)


def cancel_reserva(id_reserva):
    """Marca la reserva como cancelada (no la borra)."""
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")
    reserva.estado = "cancelada"
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return reserva.to_dict()


def delete_reserva(id_reserva):
    """Elimina la reserva indicada de la BD."""
    reserva = find_by_id(id_reserva)
    if not reserva:
        raise ValueError("Reserva no encontrada")

    try:
        from models.pago_model import Pago
        from models.registro_model import Registro

        db.session.query(Pago).filter(Pago.id_reserva == id_reserva).delete(synchronize_session=False)
        db.session.query(Registro).filter_by(id_reserva=id_reserva).update({Registro.id_reserva: None})
        db.session.delete(reserva)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def delete(reservation_id):
    """Alias por compatibilidad."""
    return delete_reserva(reservation_id)
