from datetime import datetime
import time, random

incidentes = [
    {
        "id_incidente": "I1",
        "descripcion": "Siniestro leve",
        "fecha_incidente": datetime.now().date().isoformat(),
        "id_registro": "R1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

def generate_id():
    return f"I{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_incidente):
    return next((i for i in incidentes if i["id_incidente"] == id_incidente), None)


def list_all():
    return incidentes.copy()


def list_by_registro(id_registro):
    return [i for i in incidentes if i["id_registro"] == id_registro]


def create_incidente(descripcion, fecha_incidente, id_registro):
    incidente = {
        "id_incidente": generate_id(),
        "descripcion": descripcion,
        "fecha_incidente": fecha_incidente,
        "id_registro": id_registro,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    incidentes.append(incidente)
    return incidente


def update_incidente(id_incidente, updates):
    incidente = find_by_id(id_incidente)
    if not incidente:
        raise ValueError("Incidente no encontrado")
    for key,value in updates.items():
        if key in ["descripcion","fecha_incidente","id_registro"]:
            incidente[key] = value
    incidente["updated_at"] = datetime.now().isoformat()
    return incidente


def delete_incidente(id_incidente):
    global incidentes
    if not find_by_id(id_incidente):
        raise ValueError("Incidente no encontrado")
    incidentes = [i for i in incidentes if i["id_incidente"] != id_incidente]
