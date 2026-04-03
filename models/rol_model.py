from datetime import datetime
import time, random

roles = [
    {"id_rol": "1", "nombre": "admin", "descripcion": "Administrador", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
    {"id_rol": "2", "nombre": "cliente", "descripcion": "Cliente normal", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
]


def generate_id():
    return f"R{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_rol):
    return next((r for r in roles if r["id_rol"] == id_rol), None)


def list_all():
    return roles.copy()


def create_rol(nombre, descripcion):
    role = {"id_rol": generate_id(), "nombre": nombre, "descripcion": descripcion, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
    roles.append(role)
    return role


def update_rol(id_rol, updates):
    rol = find_by_id(id_rol)
    if not rol:
        raise ValueError("Rol no encontrado")
    for key, value in updates.items():
        if key in ["nombre", "descripcion"]:
            rol[key] = value
    rol["updated_at"] = datetime.now().isoformat()
    return rol


def delete_rol(id_rol):
    global roles
    if not find_by_id(id_rol):
        raise ValueError("Rol no encontrado")
    roles = [r for r in roles if r["id_rol"] != id_rol]
