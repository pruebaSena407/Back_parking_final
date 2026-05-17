# =====================================================================
# MODELO DE USUARIO (user_model.py)
# ---------------------------------------------------------------------
# Aquí está la "definición" de un usuario en la base de datos: qué
# columnas tiene, qué validaciones aplicamos, y las funciones que sirven
# para crear, buscar, actualizar y borrar usuarios.
#
# IMPORTANTE: este archivo se llama "model" porque trabaja directamente
# con la tabla "usuario" de la base de datos.
# =====================================================================

from datetime import datetime
from typing import Union
import re  # Para usar expresiones regulares (validar formatos)
# werkzeug nos ayuda a guardar las contraseñas de forma SEGURA (hasheadas)
# en vez de guardarlas en texto plano.
from werkzeug.security import generate_password_hash, check_password_hash
# email_validator valida que el correo tenga formato real y dominio existente
from email_validator import validate_email, EmailNotValidError

from sqlalchemy import text  # Para escribir SQL en bruto cuando hace falta

from db import db


# ---------------------------------------------------------------------
# FUNCIONES DE VALIDACIÓN
# ---------------------------------------------------------------------
# Cada función revisa que el dato que llega del front sea válido.
# Si no lo es, lanza un ValueError con un mensaje claro para el usuario.

def validate_name(name: str) -> str:
    """Valida y limpia un nombre (o apellido)."""
    # Si viene vacío o solo con espacios, no sirve
    if not name or not name.strip():
        raise ValueError("El nombre es obligatorio")
    if len(name) > 100:
        raise ValueError("El nombre no puede exceder 100 caracteres")
    # Solo permitimos letras (incluyendo acentos y ñ) y espacios
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", name):
        raise ValueError("El nombre solo puede contener letras y espacios")
    return name.strip()  # Quitamos espacios al inicio y final


def validate_email_format(email: str) -> str:
    """Valida que el correo tenga formato correcto y que el dominio exista."""
    if not email or not email.strip():
        raise ValueError("El correo es obligatorio")
    try:
        # check_deliverability=True intenta verificar que el dominio responda
        valid = validate_email(email, check_deliverability=True)
        return valid.email  # Devuelve el correo "normalizado"
    except EmailNotValidError as e:
        raise ValueError(f"Correo inválido: {str(e)}")


def validate_phone(telefono: str) -> str:
    """Valida un teléfono opcional. Si viene vacío, devuelve string vacío."""
    if telefono is None:
        return ""
    telefono_str = str(telefono).strip()
    if not telefono_str:
        return ""
    if len(telefono_str) > 20:
        raise ValueError("El teléfono no puede exceder 20 caracteres")
    # Permitimos números, espacios, guiones, paréntesis y el símbolo +
    if not re.match(r"^[0-9\s\-+()]+$", telefono_str):
        raise ValueError("El teléfono solo puede contener números, espacios, +, -, y paréntesis")
    return telefono_str


def validate_password(password: str) -> str:
    """
    Valida que la contraseña sea fuerte y devuelve su versión HASHEADA.
    Nunca debemos guardar contraseñas en texto plano en la base de datos.
    """
    if not password:
        raise ValueError("La contraseña es obligatoria")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    # Las siguientes validaciones obligan a tener mayúscula, minúscula,
    # número y un carácter especial (más seguro).
    if not re.search(r"[A-Z]", password):
        raise ValueError("La contraseña debe contener al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        raise ValueError("La contraseña debe contener al menos una letra minúscula")
    if not re.search(r"\d", password):
        raise ValueError("La contraseña debe contener al menos un número")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("La contraseña debe contener al menos un carácter especial")
    # Devuelve la contraseña ya hasheada (irreversible)
    return generate_password_hash(password)


def verify_password(hashed_password: str, password: str) -> bool:
    """
    Compara la contraseña que el usuario escribió (en texto plano) con
    la que tenemos guardada (hasheada). Devuelve True si coinciden.

    Nota: si en la BD había contraseñas guardadas SIN hash (de versiones
    anteriores), también acepta la comparación directa para no romper
    el login de esos usuarios antiguos.
    """
    try:
        if check_password_hash(hashed_password, password):
            return True
    except ValueError:
        # check_password_hash lanza error si el valor guardado no es un hash
        pass

    return hashed_password == password


# ---------------------------------------------------------------------
# CLASE USER: define la tabla "usuario" en la base de datos
# ---------------------------------------------------------------------
class User(db.Model):
    __tablename__ = "usuario"  # Nombre de la tabla en Postgres

    # Cada Column define una columna. db.Integer = entero, db.String(100) = varchar.
    id_usuario = db.Column(db.Integer, primary_key=True)  # Llave primaria
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)  # único en toda la tabla
    telefono = db.Column(db.String(20))  # opcional
    contrasena = db.Column(db.String(255), nullable=False)  # guardada hasheada
    # id_rol es entero y apunta a la tabla "rol" (relación: 1 rol → muchos usuarios)
    id_rol = db.Column(db.Integer, nullable=False)
    # created_at se llena automáticamente al crear el registro
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # updated_at también se actualiza solo cada vez que cambiamos el registro
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def _nombre_rol(self) -> str:
        """
        Va a la tabla "rol" y trae el NOMBRE del rol (ej: 'cliente').
        Si algo falla, devuelve el id como texto.
        """
        try:
            row = db.session.execute(
                text("SELECT nombre FROM rol WHERE id_rol = :i LIMIT 1"),
                {"i": self.id_rol},
            ).scalar()
            return row if row else str(self.id_rol)
        except Exception:
            return str(self.id_rol)

    def to_dict(self, exclude_password=True):
        """
        Convierte el objeto User en un diccionario (JSON serializable)
        para mandárselo al frontend. Por seguridad, por defecto NO incluye
        la contraseña.
        """
        data = {
            "id_usuario": self.id_usuario,
            "nombre": self.nombre,
            "apellido": self.apellido,
            "correo": self.correo,
            "telefono": self.telefono,
            "id_rol": self._nombre_rol(),  # mandamos el nombre, no el id
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if not exclude_password:
            data["contrasena"] = self.contrasena
        return data


# ---------------------------------------------------------------------
# FUNCIONES AUXILIARES (operaciones sobre la tabla usuario)
# ---------------------------------------------------------------------

def next_usuario_id() -> int:
    """
    Calcula el siguiente id_usuario disponible (max + 1).
    Esto se usa porque en Postgres id_usuario es INTEGER (no SERIAL/autogen).
    """
    row = db.session.execute(
        text("SELECT COALESCE(MAX(id_usuario), 0) + 1 FROM usuario")
    ).scalar()
    return int(row)


def resolve_id_rol_db(rol_input: Union[str, int, None]) -> int:
    """
    El front puede mandar el rol como texto ('cliente') o como número (2).
    Esta función siempre devuelve el ID entero correspondiente.
    """
    # Si no manda nada, asumimos 'cliente' por defecto
    if rol_input is None:
        rol_input = "cliente"
    # Si ya es entero, lo devolvemos directo
    if isinstance(rol_input, int) and not isinstance(rol_input, bool):
        return int(rol_input)
    s = str(rol_input).strip()
    # Si es un string numérico, lo convertimos
    if s.isdigit():
        return int(s)
    # Buscamos en la tabla rol el id que corresponda a ese nombre
    row = db.session.execute(
        text("SELECT id_rol FROM rol WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(:n)) LIMIT 1"),
        {"n": s},
    ).scalar()
    if row is not None:
        return int(row)
    # Por si la tabla rol está vacía: ids "típicos" como respaldo
    defaults = {"cliente": 2, "admin": 1, "empleado": 3}
    if s.lower() in defaults:
        return defaults[s.lower()]
    raise ValueError(f"Rol no válido: {rol_input}")


def find_by_id(id_usuario):
    """Busca un usuario por su id. Devuelve None si no existe."""
    if id_usuario is None:
        return None
    try:
        pk = int(id_usuario)
    except (TypeError, ValueError):
        return None
    return User.query.get(pk)


def find_by_correo(correo):
    """Busca un usuario por correo (sirve para el login y para evitar duplicados)."""
    return User.query.filter_by(correo=correo).first()


def list_all():
    """Devuelve TODOS los usuarios como lista de diccionarios."""
    users = User.query.all()
    return [user.to_dict() for user in users]


def create_usuario(nombre, apellido, correo, telefono, contrasena, id_rol):
    """
    Crea un usuario nuevo. Pasos:
    1) Validar cada campo.
    2) Verificar que el correo no esté ya registrado.
    3) Hashear la contraseña.
    4) Insertar en la BD.
    """
    # 1) Validaciones (lanzan ValueError si algo está mal)
    nombre = validate_name(nombre)
    apellido = validate_name(apellido)
    correo = validate_email_format(correo)
    telefono = validate_phone(telefono)
    contrasena_hashed = validate_password(contrasena)

    # 2) ¿Ya existe alguien con ese correo?
    if find_by_correo(correo):
        raise ValueError("Correo ya registrado")

    # 3) Resolver el id_rol y crear el objeto User
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
    # 4) Guardar en la BD
    try:
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
    except Exception:
        db.session.rollback()
        raise
    return user.to_dict()


def update_usuario(id_usuario, updates):
    """
    Actualiza los campos enviados en 'updates' del usuario indicado.
    Solo permite cambiar los campos seguros (whitelist).
    """
    user = find_by_id(id_usuario)
    if not user:
        raise ValueError("Usuario no encontrado")

    for key, value in updates.items():
        if hasattr(user, key) and key in ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]:
            if key == "id_rol":
                value = resolve_id_rol_db(value)
            setattr(user, key, value)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return user.to_dict()


def delete_usuario(id_usuario):
    """Elimina al usuario si existe."""
    user = find_by_id(id_usuario)
    if not user:
        raise ValueError("Usuario no encontrado")

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
