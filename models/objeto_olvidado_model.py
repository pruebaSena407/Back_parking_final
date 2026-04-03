from datetime import datetime
import time, random

objetos_olvidados = [
    {
        "id_objeto_olvidado": "O1",
        "descripcion": "Llave",
        "fecha_encontrado": datetime.now().date().isoformat(),
        "id_registro": "R1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
]

def generate_id():
    return f"O{int(time.time())}{random.randint(100,999)}"


def find_by_id(id_objeto_olvidado):
    return next((o for o in objetos_olvidados if o["id_objeto_olvidado"] == id_objeto_olvidado), None)


def list_all():
    return objetos_olvidados.copy()


def list_by_registro(id_registro):
    return [o for o in objetos_olvidados if o["id_registro"] == id_registro]


def create_objeto(descripcion, fecha_encontrado, id_registro):
    objeto = {
        "id_objeto_olvidado": generate_id(),
        "descripcion": descripcion,
        "fecha_encontrado": fecha_encontrado,
        "id_registro": id_registro,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    objetos_olvidados.append(objeto)
    return objeto


def update_objeto(id_objeto_olvidado, updates):
    objeto = find_by_id(id_objeto_olvidado)
    if not objeto:
        raise ValueError("Objeto olvidado no encontrado")
    for key,value in updates.items():
        if key in ["descripcion","fecha_encontrado","id_registro"]:
            objeto[key] = value
    objeto["updated_at"] = datetime.now().isoformat()
    return objeto


def delete_objeto(id_objeto_olvidado):
    global objetos_olvidados
    if not find_by_id(id_objeto_olvidado):
        raise ValueError("Objeto olvidado no encontrado")
    objetos_olvidados = [o for o in objetos_olvidados if o["id_objeto_olvidado"] != id_objeto_olvidado]
