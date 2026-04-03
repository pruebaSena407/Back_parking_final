# ParkVista Backend

Backend API para sistema de reserva de parqueaderos, desarrollado con Python y Flask.

## Requisitos

- Python 3.7+
- pip

## Instalación

```bash
cd Back_parking_final
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

Servidor disponible en `http://localhost:4000`

## API Endpoints

- **Autenticación**: `/api/auth` (signup, signin)
- **Ubicaciones**: `/api/locations` (CRUD de parqueaderos)
- **Tarifas**: `/api/rates` (CRUD de tarifas)
- **Usuarios**: `/api/users` (CRUD de usuarios)
- **Reservas**: `/api/reservations` (CRUD de reservas)
- **Estadísticas**: `/api/stats` (métricas generales)

## Estructura del Proyecto

- `models/`: Modelos de datos
- `controllers/`: Lógica de negocio
- `routes/`: Definición de rutas REST
- `app.py`: Aplicación principal

## Notas

- Datos almacenados en memoria (se pierden al reiniciar)
- Ideal para desarrollo y pruebas

## Despliegue (Render)

Variables de entorno necesarias:
- `DATABASE_URL` o `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_SSL_MODE`, `DB_SSL_CA`

Comando de inicio (Render):

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2
```

Asegúrate de tener en `requirements.txt`:
- `gunicorn`
- `Flask`
- `Flask-CORS`
- `Flask-SQLAlchemy`
- `PyMySQL`
- `python-dotenv`

