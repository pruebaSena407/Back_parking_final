from flask import jsonify
from models import user_model, reservation_model, location_model

def get_overview():
    """Estadísticas generales del sistema"""
    users = user_model.users
    reservations = reservation_model.reservations
    
    # Contar clientes (usuarios con role "cliente")
    active_clients = sum(1 for u in users if u.get("role") == "cliente")
    
    # Reservas activas
    active_reservations = sum(1 for r in reservations if r.get("status") == "activa")
    
    # Ingresos (suma de montos en reservas completadas)
    monthly_revenue = sum(r.get("amount", 0) for r in reservations if r.get("status") == "completada")
    
    # Cantidad de ubicaciones
    location_count = len(location_model.locations)
    
    return jsonify({
        "stats": {
            "activeClients": active_clients,
            "activeReservations": active_reservations,
            "monthlyRevenue": monthly_revenue,
            "locationCount": location_count,
            "totalUsers": len(users)
        }
    }), 200

def get_occupancy():
    """Tasa de ocupación por ubicación"""
    locations = location_model.list_all()
    reservations = reservation_model.reservations
    
    occupancy_data = []
    for location in locations:
        # Contar reservas activas en esta ubicación
        active_in_location = sum(
            1 for r in reservations 
            if r.get("locationName") == location["name"] and r.get("status") == "activa"
        )
        
        occupancy_rate = (active_in_location / location["capacity"]) * 100 if location["capacity"] > 0 else 0
        
        occupancy_data.append({
            "locationId": location["id"],
            "locationName": location["name"],
            "capacity": location["capacity"],
            "occupied": active_in_location,
            "rate": round(occupancy_rate, 2)
        })
    
    return jsonify({
        "occupancy": occupancy_data,
        "averageRate": round(sum(o["rate"] for o in occupancy_data) / len(occupancy_data), 2) if occupancy_data else 0
    }), 200

def get_revenue():
    """Ingresos por período"""
    reservations = reservation_model.reservations
    
    # Total de ingresos
    total_revenue = sum(r.get("amount", 0) for r in reservations if r.get("amount"))
    
    # Ingresos completados
    completed_revenue = sum(r.get("amount", 0) for r in reservations if r.get("status") == "completada" and r.get("amount"))
    
    # Ingresos pendientes
    pending_revenue = sum(r.get("amount", 0) for r in reservations if r.get("status") == "activa" and r.get("amount"))
    
    return jsonify({
        "revenue": {
            "total": total_revenue,
            "completed": completed_revenue,
            "pending": pending_revenue,
            "reservationCount": len(reservations)
        }
    }), 200
