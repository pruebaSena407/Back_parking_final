from datetime import datetime
import time
import random

# Base de datos simulada en memoria
locations = [
    {
        "id": "1",
        "name": "Centro Comercial Andino",
        "address": "Carrera 11 #82-71",
        "capacity": 150,
        "latitude": 4.667,
        "longitude": -74.055,
        "createdAt": datetime.now().isoformat()
    },
    {
        "id": "2",
        "name": "Centro Internacional",
        "address": "Carrera 7 #33-49",
        "capacity": 200,
        "latitude": 4.617,
        "longitude": -74.068,
        "createdAt": datetime.now().isoformat()
    },
    {
        "id": "3",
        "name": "Parque de la 93",
        "address": "Calle 93 #13-45",
        "capacity": 120,
        "latitude": 4.676,
        "longitude": -74.046,
        "createdAt": datetime.now().isoformat()
    }
]

def generate_id():
    return f"{int(time.time())}-{random.randint(0, 1000)}"

def list_all():
    return locations.copy()

def find_by_id(location_id):
    for loc in locations:
        if loc["id"] == location_id:
            return loc
    return None

def create(name, address, capacity, latitude, longitude):
    location = {
        "id": generate_id(),
        "name": name,
        "address": address,
        "capacity": capacity,
        "latitude": latitude,
        "longitude": longitude,
        "createdAt": datetime.now().isoformat()
    }
    locations.append(location)
    return location

def update(location_id, updates):
    location = find_by_id(location_id)
    if not location:
        raise ValueError("Ubicación no encontrada")
    
    for key, value in updates.items():
        if key not in ["id", "createdAt"]:
            location[key] = value
    
    return location

def delete(location_id):
    global locations
    new_locations = [loc for loc in locations if loc["id"] != location_id]
    if len(new_locations) == len(locations):
        raise ValueError("Ubicación no encontrada")
    locations = new_locations
