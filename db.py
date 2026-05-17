# =====================================================================
# INSTANCIA DE LA BASE DE DATOS (db.py)
# ---------------------------------------------------------------------
# Aquí creamos UNA sola instancia de SQLAlchemy que va a ser compartida
# por toda la aplicación (modelos, controladores, etc).
#
# La idea de tener este archivo separado es evitar el "import circular":
# si los modelos importaran directo desde app.py habría problemas.
# Por eso, todos importan "db" desde aquí.
# =====================================================================

from flask_sqlalchemy import SQLAlchemy

# Esta es la instancia del ORM. Luego en app.py se conecta con la app
# Flask mediante db.init_app(app).
db = SQLAlchemy()
