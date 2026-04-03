from datetime import datetime

rol_permiso = []

def link_rol_permiso(id_rol, id_permiso):
    if any(rp for rp in rol_permiso if rp["id_rol"] == id_rol and rp["id_permiso"] == id_permiso):
        raise ValueError("Vinculación ya existe")
    entry = {
        "id_rol": id_rol,
        "id_permiso": id_permiso,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    rol_permiso.append(entry)
    return entry

def list_all():
    return rol_permiso.copy()

def delete_link(id_rol, id_permiso):
    global rol_permiso
    rol_permiso = [rp for rp in rol_permiso if not (rp["id_rol"] == id_rol and rp["id_permiso"] == id_permiso)]
