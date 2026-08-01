# Documentación del Backend — ParkVista

Backend del sistema de reserva de parqueaderos **ParkVista**, desarrollado en **Python** con el framework **Flask**, siguiendo una arquitectura **MVC** (Modelo-Vista-Controlador) y persistencia en **PostgreSQL**.

Este documento explica qué herramientas y tecnologías se utilizaron para lograr el resultado y cuál es el propósito de cada una.

---

## 1. Lenguaje y entorno de ejecución

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **Python** | 3.12.2 | Lenguaje de programación principal (versión fijada en `runtime.txt`). |
| **pip / requirements.txt** | — | Gestión de dependencias del proyecto. |

## 2. Framework web

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **Flask** | 3.0.0 | Microframework web. Punto de entrada (`app.py`), crea el servidor HTTP y atiende las peticiones devolviendo respuestas JSON. |
| **Blueprints de Flask** | — | Organizan el API por dominios funcionales, cada uno con su prefijo de URL. |

### Endpoints (Blueprints registrados)

- `/api/auth` — Autenticación (signup, signin)
- `/api/reservations` — Reservas
- `/api/locations` — Ubicaciones / parqueaderos
- `/api/rates` — Tarifas
- `/api/users` — Usuarios
- `/api/stats` — Estadísticas
- `/api/pagos` — Pagos
- `/api/incidentes` — Incidentes
- `/api/objetos-olvidados` — Objetos olvidados
- `/api/reports` — Reportes
- `/api/frequent-users` — Clientes frecuentes
- `/api/registros` — Registros de entrada/salida

## 3. Base de datos y ORM

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **PostgreSQL** | — | Motor de base de datos relacional (en producción, provisto por Render). |
| **Flask-SQLAlchemy** | 3.1.1 | ORM para trabajar con la base de datos mediante modelos de Python en lugar de SQL crudo. Conexión centralizada en `db.py` para evitar imports circulares. |
| **psycopg2-binary** | 2.9.9 | Driver/adaptador que conecta Python con PostgreSQL. |

Además se implementaron, en el arranque de la aplicación:

- **Migraciones idempotentes** (`ALTER TABLE ... IF NOT EXISTS`) para mantener compatibilidad con esquemas de bases de datos antiguas.
- **Índices** sobre columnas de uso frecuente (login, reportes, joins) para acelerar las consultas.

## 4. Seguridad y autenticación

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **PyJWT** | 2.8.0 | Generación y validación de **JSON Web Tokens (JWT)** firmados con algoritmo HS256 (expiración de 8 horas). |
| **Werkzeug** (`werkzeug.security`) | 3.0.0 | Hashing seguro de contraseñas (`generate_password_hash` / `check_password_hash`). Nunca se almacenan en texto plano. |
| **Flask-CORS** | 4.0.0 | Permite peticiones del frontend desde otro dominio/puerto; restringe orígenes vía `CORS_ORIGINS`. |
| **Middleware propio** (`auth_middleware.py`) | — | Decoradores `require_auth` y `require_role` para proteger endpoints y aplicar control de acceso por roles (admin, empleado, cliente). |

## 5. Configuración y despliegue

| Herramienta | Versión | Propósito |
|-------------|---------|-----------|
| **python-dotenv** | 1.0.0 | Carga de variables de entorno sensibles (URL de BD, clave JWT) desde `.env`, fuera del código fuente. |
| **Gunicorn** | 23.0.0 | Servidor WSGI de producción para el despliegue (sobre **Render**). |
| **email-validator** | 2.2.0 | Validación del formato de correos electrónicos. |
| **Git** | — | Control de versiones del proyecto. |

## 6. Arquitectura del proyecto (MVC)

```
Back_parking_final/
├── app.py            # Arranque: servidor Flask, conexión a BD, registro de rutas
├── config.py         # Variables de entorno (DATABASE_URL, JWT_SECRET_KEY)
├── db.py             # Instancia única de SQLAlchemy
├── seed_db.py        # Datos iniciales (roles, permisos, usuario admin)
├── requirements.txt  # Dependencias
├── runtime.txt       # Versión de Python
├── models/           # Modelos de datos (usuario, vehículo, reserva, pago, tarifa, ubicación, etc.)
├── controllers/      # Lógica de negocio de cada dominio
└── routes/           # Definición de endpoints REST (blueprints)
```

- **models/** — Definición de las tablas y entidades del dominio.
- **controllers/** — Lógica de negocio de cada módulo.
- **routes/** — Endpoints REST agrupados en blueprints.

## 7. Resumen

El backend es un **API REST en Python + Flask** con:

- Persistencia en **PostgreSQL** mediante el ORM **SQLAlchemy** (`psycopg2`).
- Autenticación basada en **JWT** (PyJWT) con contraseñas cifradas mediante **Werkzeug**.
- Control de acceso por roles a través de un middleware propio.
- Configuración por variables de entorno con **dotenv**.
- Despliegue en producción con **Gunicorn** sobre **Render**, con CORS habilitado para el frontend.
