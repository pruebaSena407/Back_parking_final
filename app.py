from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import DATABASE_URL
from routes.auth_routes import auth_bp
from routes.reservation_routes import reservation_bp
from routes.location_routes import location_bp
from routes.rate_routes import rate_bp
from routes.user_routes import user_bp
from routes.stats_routes import stats_bp
from routes.pago_routes import pago_bp
from routes.incidente_routes import incidente_bp
from routes.objeto_olvidado_routes import objeto_olvidado_bp

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
CORS(app)

# Registrar blueprints (rutas)
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(reservation_bp, url_prefix="/api/reservations")
app.register_blueprint(location_bp, url_prefix="/api/locations")
app.register_blueprint(rate_bp, url_prefix="/api/rates")
app.register_blueprint(user_bp, url_prefix="/api/users")
app.register_blueprint(stats_bp, url_prefix="/api/stats")
app.register_blueprint(pago_bp, url_prefix="/api/pagos")
app.register_blueprint(incidente_bp, url_prefix="/api/incidentes")
app.register_blueprint(objeto_olvidado_bp, url_prefix="/api/objetos-olvidados")

@app.route('/api/db-test', methods=['GET'])
def db_test():
    try:
        with db.engine.connect() as conn:
            result = conn.execute(db.text('SELECT 1')).scalar()
        return jsonify({'ok': True, 'db': result}), 200
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return {
        "title": "ParkVista Backend MVC",
        "version": "0.1.0",
        "message": "API disponible en /api/auth, /api/reservations, /api/locations, /api/rates, /api/users, /api/stats"
    }

@app.errorhandler(404)
def not_found(error):
    return {"error": "Ruta no encontrada"}, 404

if __name__ == "__main__":
    app.run(debug=True, port=4000)
