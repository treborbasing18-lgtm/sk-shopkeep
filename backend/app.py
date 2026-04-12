from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
import os
import sqlite3

from backend.config import Config
from backend.routes.auth_routes import auth_bp
from backend.routes.product_routes import product_bp
from backend.routes.sales_routes import sales_bp
from backend.routes.user_routes import user_bp
from backend.routes.log_routes import log_bp
from backend.routes.report_routes import report_bp

def create_app(test_config=None):
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)
    
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    Session(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(report_bp)
    
    init_database()
    
    @app.route('/')
    def serve_frontend():
        return send_from_directory(app.static_folder, 'index.html')
    
    @app.route('/api/health')
    def health_check():
        return {'status': 'ok'}
    
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