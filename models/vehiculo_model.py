# =====================================================================
# MODELO DE VEHÍCULO (vehiculo_model.py)
# ---------------------------------------------------------------------
# Define la tabla "vehiculo" y las funciones para administrar los
# vehículos registrados (placas, tipo, marca, color, etc).
# =====================================================================

from datetime import datetime
from sqlalchemy import text

from db import db


# ---------------------------------------------------------------------
# CLASE VEHICULO: representa la tabla "vehiculo" en la base de datos
# ---------------------------------------------------------------------
class Vehiculo(db.Model):
    __tablename__ = "vehiculo"

    id_vehiculo = db.Column(db.Integer, primary_key=True)
    # La placa es UNIQUE: no pueden existir dos vehículos con la misma placa
    placa = db.Column(db.String(20), unique=True, nullable=False)
    # Tipo: "carro", "moto", "camioneta", etc.
    tipo = db.Column(db.String(50), nullable=False)
    marca = db.Column(db.String(100))  # opcional
    color = db.Column(db.String(50))   # opcional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convierte el objeto a diccionario para mandar al frontend."""
        return {
            "id_vehiculo": self.id_vehiculo,
            "placa": self.placa,
            "tipo": self.tipo,
            "marca": self.marca,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES (CRUD de vehículos)
# ---------------------------------------------------------------------

def next_vehiculo_id() -> int:
    """Calcula el siguiente id_vehiculo disponible."""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_vehiculo), 0) + 1 FROM vehiculo")
    ).scalar()
    return int(row)


def find_by_id(id_vehiculo):
    """Busca un vehículo por id, devuelve None si no existe."""
    if id_vehiculo is None:
        return None
    try:
        pk = int(id_vehiculo)
    except (TypeError, ValueError):
        return None
    return Vehiculo.query.get(pk)


def find_by_placa(placa):
    """Busca un vehículo por su placa (útil para evitar duplicados)."""
    return Vehiculo.query.filter_by(placa=placa).first()


def list_all():
    """Lista todos los vehículos registrados."""
    vehiculos = Vehiculo.query.all()
    return [vehiculo.to_dict() for vehiculo in vehiculos]


def create_vehiculo(placa, tipo, marca=None, color=None):
    """
    Crea un nuevo vehículo. Primero verifica que la placa no exista,
    porque la placa es ÚNICA en la BD.
    """
    if find_by_placa(placa):
        raise ValueError("Placa ya registrada")

    vehiculo = Vehiculo(
        id_vehiculo=next_vehiculo_id(),
        placa=placa,
        tipo=tipo,
        marca=marca,
        color=color,
    )
    try:
        db.session.add(vehiculo)
        db.session.commit()
        db.session.refresh(vehiculo)
    except Exception:
        db.session.rollback()
        raise
    return vehiculo.to_dict()


def update_vehiculo(id_vehiculo, updates):
    """Actualiza un vehículo. Solo permite cambiar placa, tipo, marca o color."""
    vehiculo = find_by_id(id_vehiculo)
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")

    for key, value in updates.items():
        if hasattr(vehiculo, key) and key in ["placa", "tipo", "marca", "color"]:
            setattr(vehiculo, key, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return vehiculo.to_dict()


def delete_vehiculo(id_vehiculo):
    """Borra el vehículo si existe."""
    vehiculo = find_by_id(id_vehiculo)
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")

    try:
        db.session.delete(vehiculo)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
