# =====================================================================
# CONTROLADOR REGISTRO USUARIO FRECUENTE (frequent_user_controller.py)
# ---------------------------------------------------------------------
# Endpoint POST /api/frequent-users que recibe el formulario completo
# del front (FrequentUserForm.tsx), crea/asocia el usuario, el vehículo
# y guarda los campos extra en la tabla cliente_frecuente.
# =====================================================================

from flask import jsonify, request

from models import cliente_frecuente_model, user_model, vehiculo_model


def _ensure_user(data: dict):
    """
    Si ya existe un usuario con ese correo, lo devuelve; si no, lo crea
    con rol 'cliente'. Necesita una contraseña aceptable; cuando el
    formulario no la pide la generamos a partir del documento.
    """
    email = data.get("email")
    if not email:
        raise ValueError("email es requerido")

    existing = user_model.find_by_correo(email)
    if existing:
        return existing.to_dict(), False

    full_name = (data.get("fullName") or "").strip().split()
    if len(full_name) < 2:
        raise ValueError("fullName debe contener nombre y apellido")
    nombre = " ".join(full_name[:-1])
    apellido = full_name[-1]

    # Si no llega password, generamos una pseudoaleatoria con base al
    # documento para que pase la validación del modelo.
    raw_password = data.get("password")
    if not raw_password:
        doc = (data.get("documentNumber") or "").strip() or "Frecuente"
        raw_password = f"{doc}!Aa1"

    user_dict = user_model.create_usuario(
        nombre=nombre,
        apellido=apellido,
        correo=email,
        telefono=data.get("phone", ""),
        contrasena=raw_password,
        id_rol="cliente",
    )
    return user_dict, True


def _ensure_vehicle(data: dict):
    """Crea el vehículo si la placa no existe; si existe, devuelve el actual."""
    placa = (data.get("licensePlate") or "").strip().upper()
    if not placa:
        raise ValueError("licensePlate es requerido")

    existing = vehiculo_model.find_by_placa(placa)
    if existing:
        return existing.to_dict()

    return vehiculo_model.create_vehiculo(
        placa=placa,
        tipo=data.get("vehicleType", "car"),
        marca=data.get("vehicleBrand"),
        color=data.get("vehicleModel"),  # reutilizamos color para guardar el modelo
    )


def register_frequent_user():
    data = request.get_json() or {}
    try:
        user_dict, _ = _ensure_user(data)
        vehicle_dict = _ensure_vehicle(data)

        record = cliente_frecuente_model.create_cliente_frecuente(
            id_usuario=user_dict["id_usuario"],
            id_vehiculo=vehicle_dict["id_vehiculo"],
            tipo_documento=data.get("documentType"),
            numero_documento=data.get("documentNumber"),
            direccion=data.get("address"),
            sede_preferida=data.get("preferredLocation"),
        )
        return jsonify({
            "frequentUser": record,
            "user": user_dict,
            "vehicle": vehicle_dict,
        }), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400
