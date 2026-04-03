# Análisis del Frontend - Requerimientos para Backend

## 📊 Resumen Ejecutivo

El frontend está estructurado en 3 dashboards (Cliente, Empleado, Admin) y necesita **6 módulos principales** de API. Actualmente el backend solo tiene **Autenticación y Reservas**. Faltan: **Ubicaciones, Tarifas, Usuarios, Reportes/Estadísticas**.

---

## 🔍 Módulos Identificados

### 1. **AUTENTICACIÓN** ✅ (Parcial)
**Estado:** Implementado pero incompleto

**Endpoints Actuales:**
- ✅ `POST /api/auth/signup`
- ✅ `POST /api/auth/signin`

**Endpoints Faltantes:**
- `GET /api/auth/me` - obtener usuario actual (para mantener sesión)
- `PUT /api/auth/profile` - actualizar perfil del usuario
- `POST /api/auth/change-password` - cambiar contraseña

---

### 2. **UBICACIONES DE PARQUEADERO** ❌ (NO EXISTE)
**Componente:** `ParkingLocationsPanel.tsx`

**Estructura de datos:**
```json
{
  "id": number,
  "name": "string (e.g., Centro Comercial Andino)",
  "address": "string (e.g., Carrera 11 #82-71)",
  "capacity": number,
  "latitude": number,
  "longitude": number
}
```

**Endpoints Requeridos:**
- `GET /api/locations` - listar todas las ubicaciones
- `POST /api/locations` - crear nueva ubicación
- `PUT /api/locations/:id` - actualizar ubicación
- `DELETE /api/locations/:id` - eliminar ubicación

**Mock Data Actual (Front):**
```
- Centro Comercial Andino (150 espacios)
- Centro Internacional (200 espacios)
- Parque de la 93 (120 espacios)
```

---

### 3. **TARIFAS DE PARQUEADERO** ❌ (NO EXISTE)
**Componente:** `ParkingRatesPanel.tsx`

**Estructura de datos:**
```json
{
  "id": number,
  "name": "string",
  "hourlyRate": number (en COP),
  "dailyRate": number (en COP),
  "vehicleType": "car" | "motorcycle" | "bicycle" | "truck"
}
```

**Endpoints Requeridos:**
- `GET /api/rates` - listar todas las tarifas
- `POST /api/rates` - crear nueva tarifa
- `PUT /api/rates/:id` - actualizar tarifa
- `DELETE /api/rates/:id` - eliminar tarifa

**Mock Data Actual (Front):**
```
- Tarifa Estándar (Automóvil): $5.000/hora, $25.000/día
- Tarifa Motocicleta: $3.000/hora, $15.000/día
- Tarifa Premium (Automóvil): $8.000/hora, $40.000/día
```

---

### 4. **USUARIOS/EMPLEADOS** ⚠️ (PARCIAL)
**Componente:** `UserManagementPanel.tsx`

**Estructura de datos:**
```json
{
  "id": "string",
  "email": "string",
  "fullName": "string",
  "role": "cliente" | "empleado" | "admin",
  "createdAt": "ISO string"
}
```

**Endpoints Requeridos:**
- `GET /api/users` - listar todos los usuarios (solo admin)
- `POST /api/users` - crear nuevo usuario (solo admin)
- `GET /api/users/:id` - obtener usuario específico
- `PUT /api/users/:id` - actualizar usuario
- `DELETE /api/users/:id` - eliminar usuario (solo admin)

**Estado Actual:** El backend tiene modelo pero falta crear endpoints REST.

---

### 5. **RESERVAS** ✅ (IMPLEMENTADO)
**Estado:** Completamente funcional

**Endpoints:** 
- ✅ `GET /api/reservations` - listar todas
- ✅ `GET /api/reservations/user/:userId` - reservas del usuario
- ✅ `POST /api/reservations` - crear
- ✅ `PUT /api/reservations/:id` - actualizar
- ✅ `DELETE /api/reservations/:id` - eliminar

---

### 6. **REPORTES/ESTADÍSTICAS** ❌ (NO EXISTE)
**Componentes:** `AdminDashboard.tsx`, `EmployeeDashboard.tsx`, `ClientDashboard.tsx`

**Datos Esperados:**
```json
{
  "activeClients": number,
  "occupancyRate": number (0-100),
  "monthlyRevenue": number,
  "locationCount": number,
  "activeReservations": number,
  "totalHours": number
}
```

**Endpoints Requeridos:**
- `GET /api/stats/overview` - estadísticas generales
- `GET /api/stats/occupancy` - tasa de ocupación por ubicación
- `GET /api/stats/revenue` - ingresos por período

---

## 🎯 Prioridad de Implementación

### Fase 1 (CRÍTICA - Para funcionamiento básico):
1. ✅ Autenticación (completa)
2. ✅ Reservas (completa)
3. 🔴 Ubicaciones (URGENTE)
4. 🔴 Tarifas (URGENTE)
5. 🔴 Usuarios (URGENTE)

### Fase 2 (IMPORTANTE - Para UX completa):
6. Estadísticas/Reportes
7. Validaciones avanzadas
8. Caché de datos

---

## 📋 Resumen rápido de faltantes:

| Módulo | Implementado | Endpoints | Prioridad |
|--------|-------------|-----------|-----------|
| Auth | 40% | 2/5 | Alta |
| Ubicaciones | 0% | 0/4 | Crítica |
| Tarifas | 0% | 0/4 | Crítica |
| Usuarios | 20% | 0/5 | Crítica |
| Reservas | 100% | 5/5 | - |
| Estadísticas | 0% | 0/3 | Media |

---

## 🔐 Notas de Seguridad (Para implementación):
- Las tarifas y ubicaciones deben ser editables solo por admin/empleado
- Los usuarios deben ver solo sus propias reservas (menos admin)
- Los cambios de rol deben ser exclusivos de admin
- Las contraseñas deben validarse (mínimo 6 caracteres)
