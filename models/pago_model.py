from datetime import datetime
import time, random

pagos = [
    {
        "id_pago": "P1",
        "monto": 10000,
        "fecha_pago": datetime.now().date().isoformat(),
        "metodo_pago": "efectivo",
        "id_registro": "R1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

def generate_id():
    return f"P{int(time.time())}{random.randint(100,999)}"

def find_by_id(id_pago):
    return next((p for p in pagos if p["id_pago"] == id_pago), None)


def list_all():
    return pagos.copy()


def list_by_registro(id_registro):
    return [p for p in pagos if p["id_registro"] == id_registro]


def create_pago(monto, fecha_pago, metodo_pago, id_registro):
    pago = {
        "id_pago": generate_id(),
        "monto": monto,
        "fecha_pago": fecha_pago,
        "metodo_pago": metodo_pago,
        "id_registro": id_registro,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    pagos.append(pago)
    return pago


def update_pago(id_pago, updates):
    pago = find_by_id(id_pago)
    if not pago:
        raise ValueError("Pago no encontrado")
    for key,value in updates.items():
        if key in ["monto","fecha_pago","metodo_pago","id_registro"]:
            pago[key] = value
    pago["updated_at"] = datetime.now().isoformat()
    return pago


def delete_pago(id_pago):
    global pagos
    if not find_by_id(id_pago):
        raise ValueError("Pago no encontrado")
    pagos = [p for p in pagos if p["id_pago"] != id_pago]
