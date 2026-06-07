from datetime import datetime, date, time, timedelta
from sqlalchemy import text, ForeignKey

from db import db
from models import vehiculo_model


# Colombia no usa horario de verano: siempre UTC-5. Calculamos la hora local
# restando el offset a la hora UTC del servidor (válido en Render/Linux y local).
COLOMBIA_OFFSET = timedelta(hours=5)


def _now_co() -> datetime:
    """Fecha y hora actuales en hora de Colombia (UTC-5)."""
    return datetime.utcnow() - COLOMBIA_OFFSET


class Registro(db.Model):
    __tablename__ = "registro"

    id_registro = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    hora_entrada = db.Column(db.Time, nullable=False)
    hora_salida = db.Column(db.Time)
    id_usuario = db.Column(db.Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_vehiculo = db.Column(db.Integer, ForeignKey("vehiculo.id_vehiculo"), nullable=False)
    # Ubicación donde entró/salió el vehículo (núcleo de ocupación por sede).
    id_ubicacion = db.Column(db.Integer, ForeignKey("ubicacion.id_ubicacion"))
    # Reserva asociada (opcional): permite enlazar el movimiento con su cobro.
    id_reserva = db.Column(db.Integer, ForeignKey("reserva.id_reserva"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id_registro,
            "date": self.fecha.isoformat() if self.fecha else None,
            "checkIn": str(self.hora_entrada) if self.hora_entrada else None,
            "checkOut": str(self.hora_salida) if self.hora_salida else None,
            "userId": self.id_usuario,
            "vehicleId": self.id_vehiculo,
            "locationId": self.id_ubicacion,
            "reservationId": self.id_reserva,
            "active": self.hora_salida is None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_front(self):
        """Versión enriquecida con placa y nombre de ubicación para la UI."""
        data = self.to_dict()
        try:
            veh = db.session.execute(
                text("SELECT placa, tipo FROM vehiculo WHERE id_vehiculo = :v"),
                {"v": self.id_vehiculo},
            ).fetchone()
            if veh:
                data["plate"] = veh.placa
                data["vehicleType"] = veh.tipo
        except Exception:
            db.session.rollback()
        try:
            if self.id_ubicacion is not None:
                ub = db.session.execute(
                    text("SELECT nombre FROM ubicacion WHERE id_ubicacion = :u"),
                    {"u": self.id_ubicacion},
                ).fetchone()
                if ub:
                    data["locationName"] = ub.nombre
        except Exception:
            db.session.rollback()
        return data


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
    registros = Registro.query.order_by(Registro.created_at.desc()).all()
    return [registro.to_front() for registro in registros]


def list_active(id_ubicacion=None):
    """Vehículos actualmente dentro (sin hora de salida)."""
    query = Registro.query.filter(Registro.hora_salida.is_(None))
    if id_ubicacion is not None:
        query = query.filter_by(id_ubicacion=int(id_ubicacion))
    return [r.to_front() for r in query.order_by(Registro.created_at.desc()).all()]


def list_by_usuario(id_usuario):
    registros = Registro.query.filter_by(id_usuario=id_usuario).all()
    return [registro.to_dict() for registro in registros]


def list_by_vehiculo(id_vehiculo):
    registros = Registro.query.filter_by(id_vehiculo=id_vehiculo).all()
    return [registro.to_dict() for registro in registros]


def list_by_fecha(fecha):
    registros = Registro.query.filter_by(fecha=fecha).all()
    return [registro.to_dict() for registro in registros]


def _resolve_vehiculo(value, tipo="car"):
    """Acepta id, placa existente o crea el vehículo si la placa es nueva."""
    if value is None:
        raise ValueError("Vehículo (placa o id) es requerido")
    s = str(value).strip()
    if not s:
        raise ValueError("Vehículo (placa o id) es requerido")
    if s.isdigit():
        veh = vehiculo_model.find_by_id(int(s))
        if veh:
            return veh.id_vehiculo
    placa = s.upper()
    veh = vehiculo_model.find_by_placa(placa)
    if veh:
        return veh.id_vehiculo
    created = vehiculo_model.create_vehiculo(placa=placa, tipo=tipo or "car")
    return created["id_vehiculo"]


def _capacity_left(id_ubicacion):
    """Cupos libres en la ubicación según vehículos dentro (registro activo)."""
    if id_ubicacion is None:
        return None
    capacity = db.session.execute(
        text("SELECT capacidad FROM ubicacion WHERE id_ubicacion = :u"),
        {"u": int(id_ubicacion)},
    ).scalar()
    if capacity is None:
        return None
    occupied = db.session.execute(
        text("SELECT COUNT(*) FROM registro WHERE id_ubicacion = :u AND hora_salida IS NULL"),
        {"u": int(id_ubicacion)},
    ).scalar() or 0
    return int(capacity) - int(occupied)


def checkin(id_usuario, vehiculo, id_ubicacion=None, tipo="car", id_reserva=None):
    """Registra la ENTRADA de un vehículo (hora_entrada = ahora)."""
    id_vehiculo = _resolve_vehiculo(vehiculo, tipo)

    # Evitar doble check-in del mismo vehículo sin salida.
    open_reg = Registro.query.filter_by(id_vehiculo=id_vehiculo, hora_salida=None).first()
    if open_reg:
        raise ValueError("El vehículo ya tiene un ingreso activo sin salida")

    if id_ubicacion is not None:
        left = _capacity_left(id_ubicacion)
        if left is not None and left <= 0:
            raise ValueError("La ubicación está llena (sin cupos disponibles)")

    now = _now_co()
    registro = Registro(
        id_registro=next_registro_id(),
        fecha=now.date(),
        hora_entrada=now.time().replace(microsecond=0),
        hora_salida=None,
        id_usuario=int(id_usuario),
        id_vehiculo=id_vehiculo,
        id_ubicacion=int(id_ubicacion) if id_ubicacion is not None else None,
        id_reserva=int(id_reserva) if id_reserva is not None else None,
    )
    try:
        db.session.add(registro)
        db.session.commit()
        db.session.refresh(registro)
    except Exception:
        db.session.rollback()
        raise
    return registro.to_front()


def checkout(id_registro):
    """Registra la SALIDA (hora_salida = ahora) y devuelve duración en minutos."""
    registro = find_by_id(id_registro)
    if not registro:
        raise ValueError("Registro no encontrado")
    if registro.hora_salida is not None:
        raise ValueError("Este registro ya tiene salida")

    now = _now_co()
    registro.hora_salida = now.time().replace(microsecond=0)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    data = registro.to_front()
    # Calculamos la duración (minutos) combinando fecha + horas.
    try:
        entrada = datetime.combine(registro.fecha, registro.hora_entrada)
        salida = datetime.combine(registro.fecha, registro.hora_salida)
        minutes = max(0, int((salida - entrada).total_seconds() // 60))
        data["durationMinutes"] = minutes
    except Exception:
        data["durationMinutes"] = None
    return data


def create_registro(hora_entrada, id_usuario, id_vehiculo, fecha=None, hora_salida=None):
    """API antigua de bajo nivel (se conserva por compatibilidad)."""
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
        if hasattr(registro, key) and key in [
            "fecha", "hora_entrada", "hora_salida", "id_usuario", "id_vehiculo",
            "id_ubicacion", "id_reserva",
        ]:
            setattr(registro, key, value)

    db.session.commit()
    return registro.to_dict()


def delete_registro(id_registro):
    registro = find_by_id(id_registro)
    if not registro:
        raise ValueError("Registro no encontrado")

    db.session.delete(registro)
    db.session.commit()
