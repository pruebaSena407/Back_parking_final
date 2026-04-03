from datetime import datetime
from typing import Union

from sqlalchemy import text

from db import db


class User(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    contrasena = db.Column(db.String(255), nullable=False)
    # En PostgreSQL suele ser INTEGER → rol(id_rol), no el texto "cliente"
    id_rol = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def _nombre_rol(self) -> str:
        try:
            row = db.session.execute(
                text("SELECT nombre FROM rol WHERE id_rol = :i LIMIT 1"),
                {"i": self.id_rol},
            ).scalar()
            return row if row else str(self.id_rol)
        except Exception:
            return str(self.id_rol)

    def to_dict(self, exclude_password=True):
        data = {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "correo": self.correo,
            "telefono": self.telefono,
            "id_rol": self._nombre_rol(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if not exclude_password:
            data["contrasena"] = self.contrasena
        return data


def generate_id(prefix=""):
    import time
    import random

    return f"{prefix}{int(time.time())}{random.randint(100, 999)}"


def resolve_id_rol_db(rol_input: Union[str, int, None]) -> int:
    """
    Convierte lo que manda el front (p. ej. 'cliente') al id_rol entero de la tabla rol.
    """
    if rol_input is None:
        rol_input = "cliente"
    if isinstance(rol_input, int) and not isinstance(rol_input, bool):
        return int(rol_input)
    s = str(rol_input).strip()
    if s.isdigit():
        return int(s)
    row = db.session.execute(
        text("SELECT id_rol FROM rol WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(:n)) LIMIT 1"),
        {"n": s},
    ).scalar()
    if row is not None:
        return int(row)
    # Respaldo típico (ajusta si tu tabla rol usa otros ids)
    defaults = {"cliente": 2, "admin": 1, "empleado": 3}
    if s.lower() in defaults:
        return defaults[s.lower()]
    raise ValueError(f"Rol no válido: {rol_input}")


def find_by_id(id_usuario):
    return User.query.get(id_usuario)


def find_by_correo(correo):
    return User.query.filter_by(correo=correo).first()


def list_all():
    users = User.query.all()
    return [user.to_dict() for user in users]


def create_usuario(nombre, apellido, correo, telefono, contrasena, id_rol):
    if find_by_correo(correo):
        raise ValueError("Correo ya registrado")

    id_rol_int = resolve_id_rol_db(id_rol)
    user = User(
        id_usuario=generate_id("U"),
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        telefono=telefono or None,
        contrasena=contrasena,
        id_rol=id_rol_int,
    )
    db.session.add(user)
    db.session.commit()
    db.session.refresh(user)
    return user.to_dict()


def update_usuario(id_usuario, updates):
    user = find_by_id(id_usuario)
    if not user:
        raise ValueError("Usuario no encontrado")

    for key, value in updates.items():
        if hasattr(user, key) and key in ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]:
            if key == "id_rol":
                value = resolve_id_rol_db(value)
            setattr(user, key, value)

    db.session.commit()
    return user.to_dict()


def delete_usuario(id_usuario):
    user = find_by_id(id_usuario)
    if not user:
        raise ValueError("Usuario no encontrado")

    db.session.delete(user)
    db.session.commit()
