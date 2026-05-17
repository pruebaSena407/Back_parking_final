# La instancia oficial de SQLAlchemy vive en db.py para evitar imports
# circulares y evitar tener dos instancias distintas en el proyecto.
from db import db  # noqa: F401
