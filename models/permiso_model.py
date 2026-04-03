from datetime import datetime
import time, random

permisos = [
    {"id_permiso": "1", "nombre":"ver", "descripcion":"Ver registros", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
    {"id_permiso": "2", "nombre":"editar", "descripcion":"Editar registros", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
]

def generate_id():
    return f"P{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_permiso):
    return next((p for p in permisos if p["id_permiso"] == id_permiso), None)


def list_all():
    return permisos.copy()


def create_permiso(nombre, descripcion):
    permiso = {"id_permiso": generate_id(), "nombre": nombre, "descripcion": descripcion, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
    permisos.append(permiso)
    return permiso


def update_permiso(id_permiso, updates):
    permiso = find_by_id(id_permiso)
    if not permiso:
        raise ValueError("Permiso no encontrado")
    for key, value in updates.items():
        if key in ["nombre", "descripcion"]:
            permiso[key] = value
    permiso["updated_at"] = datetime.now().isoformat()
    return permiso


def delete_permiso(id_permiso):
    global permisos
    if not find_by_id(id_permiso):
        raise ValueError("Permiso no encontrado")
    permisos = [p for p in permisos if p["id_permiso"] != id_permiso]
