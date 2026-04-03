from datetime import datetime
from db import db

class User(db.Model):
    __tablename__ = "usuario"

    id_usuario = db.Column(db.String(50), primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    contrasena = db.Column(db.String(255), nullable=False)
    id_rol = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, exclude_password=True):
        data = {
            'id_usuario': self.id_usuario,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'correo': self.correo,
            'telefono': self.telefono,
            'id_rol': self.id_rol,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if not exclude_password:
            data['contrasena'] = self.contrasena
        return data


def generate_id(prefix=""):
    import time, random
    return f"{prefix}{int(time.time())}{random.randint(100,999)}"


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
    
    user = User(
        id_usuario=generate_id("U"),
        nombre=nombre,
        apellido=apellido,
        correo=correo,
        telefono=telefono,
        contrasena=contrasena,
        id_rol=id_rol
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
            setattr(user, key, value)
    
    db.session.commit()
    return user.to_dict()


def delete_usuario(id_usuario):
    user = find_by_id(id_usuario)
    if not user:
        raise ValueError("Usuario no encontrado")
    
    db.session.delete(user)
    db.session.commit()

