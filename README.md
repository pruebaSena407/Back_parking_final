# ParkVista Backend (Python + Flask)

Backend MVC simple y educativo para el sistema de reserva de parqueaderos.

## 📋 Requisitos Previos

- Python 3.7+
- pip (gestor de paquetes de Python)

## 🚀 Instalación

```bash
cd Back_parking_final
pip install -r requirements.txt
```

## ▶️ Ejecución

```bash
python app.py
```

El servidor estará disponible en `http://localhost:4000`

---

## 📚 API Endpoints

### 🔐 Autenticación (`/api/auth`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/signup` | Registrar nuevo usuario |
| POST | `/signin` | Iniciar sesión |

**Ejemplo de signup:**
```bash
curl -X POST http://localhost:4000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "fullName": "John Doe"
  }'
```

**Ejemplo de signin:**
```bash
curl -X POST http://localhost:4000/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@parkvista.test",
    "password": "admin123"
  }'
```

**Credenciales de prueba:**
- Admin: `admin@parkvista.test` / `admin123`
- Usuario: `user@parkvista.test` / `user123`

---

### 📍 Ubicaciones de Parqueadero (`/api/locations`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Listar todas las ubicaciones |
| GET | `/:id` | Obtener ubicación específica |
| POST | `/` | Crear nueva ubicación |
| PUT | `/:id` | Actualizar ubicación |
| DELETE | `/:id` | Eliminar ubicación |

**Campos de ubicación:**
- `name` (string): Nombre del parqueadero
- `address` (string): Dirección
- `capacity` (integer): Capacidad máxima
- `latitude` (float): Latitud
- `longitude` (float): Longitud

**Exemplo GET:**
```bash
curl http://localhost:4000/api/locations/
```

---

### 💰 Tarifas de Parqueadero (`/api/rates`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Listar todas las tarifas |
| GET | `/:id` | Obtener tarifa específica |
| POST | `/` | Crear nueva tarifa |
| PUT | `/:id` | Actualizar tarifa |
| DELETE | `/:id` | Eliminar tarifa |

**Campos de tarifa:**
- `name` (string): Nombre de la tarifa
- `hourlyRate` (integer): Tarifa por hora (COP)
- `dailyRate` (integer): Tarifa diaria (COP)
- `vehicleType` (string): Tipo de vehículo (car, motorcycle, bicycle, truck)

**Ejemplo POST:**
```bash
curl -X POST http://localhost:4000/api/rates/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Tarifa Estándar",
    "hourlyRate": 5000,
    "dailyRate": 25000,
    "vehicleType": "car"
  }'
```

---

### 👥 Usuarios/Empleados (`/api/users`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Listar todos los usuarios (admin) |
| GET | `/:id` | Obtener usuario específico |
| POST | `/` | Crear nuevo usuario |
| PUT | `/:id` | Actualizar usuario |
| DELETE | `/:id` | Eliminar usuario |

**Campos de usuario:**
- `email` (string): Email único
- `password` (string): Contraseña
- `fullName` (string): Nombre completo
- `role` (string): Rol (cliente, empleado, admin)

---

### 🅿️ Reservas (`/api/reservations`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Listar todas las reservas |
| GET | `/user/:userId` | Reservas del usuario |
| POST | `/` | Crear nueva reserva |
| PUT | `/:id` | Actualizar reserva |
| DELETE | `/:id` | Eliminar reserva |

**Campos de reserva:**
- `userId` (string): ID del usuario
- `locationName` (string): Nombre de la ubicación
- `startTime` (ISO string): Hora de inicio
- `endTime` (ISO string): Hora de fin
- `spaceCode` (string): Código del espacio
- `status` (string): Estado (activa, completada, cancelada)
- `amount` (integer): Monto en COP
- `notes` (string): Notas

---

### 📊 Estadísticas (`/api/stats`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/overview` | Estadísticas generales |
| GET | `/occupancy` | Tasa de ocupación por ubicación |
| GET | `/revenue` | Ingresos |

**Ejemplo GET overview:**
```bash
curl http://localhost:4000/api/stats/overview
```

**Respuesta esperada:**
```json
{
  "stats": {
    "activeClients": 1,
    "activeReservations": 1,
    "monthlyRevenue": 0,
    "locationCount": 3,
    "totalUsers": 2
  }
}
```

---

## 📁 Estructura MVC

```
models/              # Modelos y lógica de datos
├── __init__.py
├── user_model.py           # CRUD de usuarios
├── reservation_model.py    # CRUD de reservas
├── location_model.py       # CRUD de ubicaciones
└── rate_model.py           # CRUD de tarifas

controllers/         # Controladores con lógica de negocio
├── __init__.py
├── auth_controller.py          # Autenticación
├── user_controller.py          # Gestión de usuarios
├── reservation_controller.py   # Gestión de reservas
├── location_controller.py      # Gestión de ubicaciones
├── rate_controller.py          # Gestión de tarifas
└── stats_controller.py         # Estadísticas

routes/              # Definición de rutas REST
├── __init__.py
├── auth_routes.py
├── user_routes.py
├── reservation_routes.py
├── location_routes.py
├── rate_routes.py
└── stats_routes.py

app.py               # Aplicación Flask principal
requirements.txt     # Dependencias Python
README.md            # Documentación
```

---

## 🔄 Flujo de Datos

```
Request HTTP 
    ↓
Flask Router (route_*.py)
    ↓
Controller (*_controller.py)
    ↓
Model (*_model.py) → Base de datos en memoria
    ↓
Response JSON
```

---

## ⚠️ Notas

- Los datos se almacenan **en memoria** (se pierden al reiniciar)
- Perfecto para desarrollo, pruebas y educación
- Para producción, usar base de datos persistente (PostgreSQL, MySQL, etc.)
- CORS habilitado para trabajar con frontend en otro puerto

---

## 🔮 Próximas Implementaciones

- [ ] Persistencia en base de datos (SQLAlchemy + PostgreSQL)
- [ ] Autenticación con JWT
- [ ] Validaciones avanzadas
- [ ] Tests automatizados
- [ ] Paginación de responses
- [ ] Filtros y búsqueda
- [ ] Caché de datos
- [ ] Logging y auditoría

