from datetime import datetime
import time, random

registros = [
    {
        "id_registro": "R1",
        "fecha": datetime.now().date().isoformat(),
        "hora_entrada": "08:00",
        "hora_salida": "10:30",
        "id_usuario": "2",
        "id_vehiculo": "V1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

def generate_id():
    return f"R{int(time.time())}{random.randint(100,999)}"

def find_by_id(id_registro):
    return next((r for r in registros if r["id_registro"] == id_registro), None)

def list_all():
    return registros.copy()

def list_by_usuario(id_usuario):
    return [r for r in registros if r["id_usuario"] == id_usuario]

def create_registro(fecha, hora_entrada, hora_salida, id_usuario, id_vehiculo):
    registro = {
        "id_registro": generate_id(),
        "fecha": fecha,
        "hora_entrada": hora_entrada,
        "hora_salida": hora_salida,
        "id_usuario": id_usuario,
        "id_vehiculo": id_vehiculo,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    registros.append(registro)
    return registro

def update_registro(id_registro, updates):
    registro = find_by_id(id_registro)
    if not registro:
        raise ValueError("Registro no encontrado")
    for key, value in updates.items():
        if key in ["fecha", "hora_entrada", "hora_salida", "id_usuario", "id_vehiculo"]:
            registro[key] = value
    registro["updated_at"] = datetime.now().isoformat()
    return registro

def delete_registro(id_registro):
    global registros
    if not find_by_id(id_registro):
        raise ValueError("Registro no encontrado")
    registros = [r for r in registros if r["id_registro"] != id_registro]
