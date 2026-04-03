from datetime import datetime

# Schema SQL-like for usuario table
usuarios = [
    {
        "id_usuario": "1",
        "nombre": "Admin",
        "apellido": "Demo",
        "correo": "admin@parkvista.test",
        "telefono": "3001234567",
        "contrasena": "admin123",
        "id_rol": "1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    },
    {
        "id_usuario": "2",
        "nombre": "Usuario",
        "apellido": "Demo",
        "correo": "user@parkvista.test",
        "telefono": "3017654321",
        "contrasena": "user123",
        "id_rol": "2",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]


def generate_id(prefix=""):
    import time, random
    return f"{prefix}{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_usuario):
    return next((u for u in usuarios if u["id_usuario"] == id_usuario), None)


def find_by_correo(correo):
    return next((u for u in usuarios if u["correo"].lower() == correo.lower()), None)


def list_all():
    return [{k: v for k,v in u.items() if k != "contrasena"} for u in usuarios]


def create_usuario(nombre, apellido, correo, telefono, contrasena, id_rol):
    if find_by_correo(correo):
        raise ValueError("Correo ya registrado")
    usuario = {
        "id_usuario": generate_id("U"),
        "nombre": nombre,
        "apellido": apellido,
        "correo": correo,
        "telefono": telefono,
        "contrasena": contrasena,
        "id_rol": id_rol,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    usuarios.append(usuario)
    return {k: v for k,v in usuario.items() if k != "contrasena"}


def update_usuario(id_usuario, updates):
    usuario = find_by_id(id_usuario)
    if not usuario:
        raise ValueError("Usuario no encontrado")
    for key, value in updates.items():
        if key in ["nombre", "apellido", "correo", "telefono", "contrasena", "id_rol"]:
            usuario[key] = value
    usuario["updated_at"] = datetime.now().isoformat()
    return {k: v for k,v in usuario.items() if k != "contrasena"}


def delete_usuario(id_usuario):
    global usuarios
    if not find_by_id(id_usuario):
        raise ValueError("Usuario no encontrado")
    usuarios = [u for u in usuarios if u["id_usuario"] != id_usuario]

