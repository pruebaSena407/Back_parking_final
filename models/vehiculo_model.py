from datetime import datetime
import time, random

vehiculos = [
    {"id_vehiculo": "V1", "placa": "ABC123", "tipo": "car", "marca": "Toyota", "color": "Blanco", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
]

def generate_id():
    return f"V{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_vehiculo):
    return next((v for v in vehiculos if v["id_vehiculo"] == id_vehiculo), None)


def list_all():
    return vehiculos.copy()


def create_vehiculo(placa, tipo, marca, color):
    vehiculo = {"id_vehiculo": generate_id(), "placa": placa, "tipo": tipo, "marca": marca, "color": color, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
    vehiculos.append(vehiculo)
    return vehiculo


def update_vehiculo(id_vehiculo, updates):
    vehiculo = find_by_id(id_vehiculo)
    if not vehiculo:
        raise ValueError("Vehículo no encontrado")
    for key, value in updates.items():
        if key in ["placa", "tipo", "marca", "color"]:
            vehiculo[key] = value
    vehiculo["updated_at"] = datetime.now().isoformat()
    return vehiculo


def delete_vehiculo(id_vehiculo):
    global vehiculos
    if not find_by_id(id_vehiculo):
        raise ValueError("Vehículo no encontrado")
    vehiculos = [v for v in vehiculos if v["id_vehiculo"] != id_vehiculo]
