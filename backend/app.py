from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
import os
import sqlite3
from config import Config
from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.sales_routes import sales_bp

def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    app.config.from_object(Config)
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    Session(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    init_database()

    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')

    return app

def init_database():
    db_path = Config.DATABASE_PATH
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.close()

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000)
