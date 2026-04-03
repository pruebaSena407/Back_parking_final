from datetime import datetime
import time
import random

# Base de datos simulada en memoria
reservations = [
    {
        "id": "1",
        "userId": "2",
        "locationName": "Parqueadero Centro",
        "spaceCode": "A-12",
        "startTime": datetime.now().isoformat(),
        "endTime": datetime.now().isoformat(),
        "status": "activa",
        "amount": 8000,
        "notes": "Reserva de ejemplo",
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
]

def generate_id():
    return f"{int(time.time())}-{random.randint(0, 1000)}"

def list_all():
    return reservations.copy()

def list_by_user(user_id):
    return [r for r in reservations if r["userId"] == user_id]

def find_by_id(reservation_id):
    for r in reservations:
        if r["id"] == reservation_id:
            return r
    return None

def create(user_id, location_name, start_time, end_time, space_code=None, amount=None, notes=None):
    reservation = {
        "id": generate_id(),
        "userId": user_id,
        "locationName": location_name,
        "spaceCode": space_code or None,
        "startTime": start_time,
        "endTime": end_time,
        "status": "activa",
        "amount": amount or None,
        "notes": notes or None,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat()
    }
    reservations.append(reservation)
    return reservation

def update(reservation_id, updates):
    reservation = find_by_id(reservation_id)
    if not reservation:
        raise ValueError("Reserva no encontrada")
    
    # Actualizar campos, excepto id y createdAt
    for key, value in updates.items():
        if key not in ["id", "createdAt"]:
            reservation[key] = value
    
    reservation["updatedAt"] = datetime.now().isoformat()
    return reservation

def delete(reservation_id):
    global reservations
    new_reservations = [r for r in reservations if r["id"] != reservation_id]
    if len(new_reservations) == len(reservations):
        raise ValueError("Reserva no encontrada")
    reservations = new_reservations
