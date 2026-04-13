from datetime import datetime
from typing import Union
import re
from werkzeug.security import generate_password_hash, check_password_hash
from email_validator import validate_email, EmailNotValidError

from sqlalchemy import text

from db import db


def validate_name(name: str) -> str:
    """Validate and clean name field."""
    if not name or not name.strip():
        raise ValueError("El nombre es obligatorio")
    if len(name) > 100:
        raise ValueError("El nombre no puede exceder 100 caracteres")
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", name):
        raise ValueError("El nombre solo puede contener letras y espacios")
    return name.strip()


def validate_email_format(email: str) -> str:
    """Validate email format and check if it's deliverable."""
    if not email or not email.strip():
        raise ValueError("El correo es obligatorio")
    try:
        # Validate format and check deliverability
        valid = validate_email(email, check_deliverability=True)
        return valid.email
    except EmailNotValidError as e:
        raise ValueError(f"Correo inválido: {str(e)}")


def validate_phone(telefono: str) -> str:
    """Validate an optional phone number and normalize whitespace."""
    if telefono is None:
        return ""
    telefono_str = str(telefono).strip()
    if not telefono_str:
        return ""
    if len(telefono_str) > 20:
        raise ValueError("El teléfono no puede exceder 20 caracteres")
    if not re.match(r"^[0-9\s\-+()]+$", telefono_str):
        raise ValueError("El teléfono solo puede contener números, espacios, +, -, y paréntesis")
    return telefono_str


def validate_password(password: str) -> str:
    """Validate password strength and hash it."""
    if not password:
        raise ValueError("La contraseña es obligatoria")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("La contraseña debe contener al menos un carácter especial")
    return generate_password_hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """Verify a password against its hash."""
    return check_password_hash(hashed_password, password)


class User(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.Integer, primary_key=True)
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


def next_usuario_id() -> int:
    """Siguiente id entero acorde a la columna usuario.id_usuario (INTEGER en PostgreSQL)."""
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_usuario), 0) + 1 FROM usuario")
    ).scalar()
    return int(row)


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
    if id_usuario is None:
        return None
    try:
        pk = int(id_usuario)
    except (TypeError, ValueError):
        return None
    return User.query.get(pk)


def find_by_correo(correo):
    return User.query.filter_by(correo=correo).first()


def list_all():
    users = User.query.all()
    return [user.to_dict() for user in users]


def create_usuario(nombre, apellido, correo, telefono, contrasena, id_rol):
    # Validate inputs
    nombre = validate_name(nombre)
    apellido = validate_name(apellido)
    correo = validate_email_format(correo)
    telefono = validate_phone(telefono)
    contrasena_hashed = validate_password(contrasena)

    if find_by_correo(correo):
        raise ValueError("Correo ya registrado")

    id_rol_int = resolve_id_rol_db(id_rol)
    user = User(
        id_usuario=next_usuario_id(),
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        telefono=telefono or None,
        contrasena=contrasena_hashed,
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
