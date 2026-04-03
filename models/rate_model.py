from datetime import datetime
import time
import random

# Base de datos simulada en memoria
rates = [
    {
        "id": "1",
        "name": "Tarifa Estándar",
        "hourlyRate": 5000,
        "dailyRate": 25000,
        "vehicleType": "car",
        "createdAt": datetime.now().isoformat()
    },
    {
        "id": "2",
        "name": "Tarifa Motocicleta",
        "hourlyRate": 3000,
        "dailyRate": 15000,
        "vehicleType": "motorcycle",
        "createdAt": datetime.now().isoformat()
    },
    {
        "id": "3",
        "name": "Tarifa Premium",
        "hourlyRate": 8000,
        "dailyRate": 40000,
        "vehicleType": "car",
        "createdAt": datetime.now().isoformat()
    }
]

def generate_id():
    return f"{int(time.time())}-{random.randint(0, 1000)}"

def list_all():
    return rates.copy()

def find_by_id(rate_id):
    for rate in rates:
        if rate["id"] == rate_id:
            return rate
    return None

def create(name, hourly_rate, daily_rate, vehicle_type):
    rate = {
        "id": generate_id(),
        "name": name,
        "hourlyRate": hourly_rate,
        "dailyRate": daily_rate,
        "vehicleType": vehicle_type,
        "createdAt": datetime.now().isoformat()
    }
    rates.append(rate)
    return rate

def update(rate_id, updates):
    rate = find_by_id(rate_id)
    if not rate:
        raise ValueError("Tarifa no encontrada")
    
    for key, value in updates.items():
        if key not in ["id", "createdAt"]:
            rate[key] = value
    
    return rate

def delete(rate_id):
    global rates
    new_rates = [r for r in rates if r["id"] != rate_id]
    if len(new_rates) == len(rates):
        raise ValueError("Tarifa no encontrada")
    rates = new_rates
