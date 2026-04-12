from flask import Flask, send_from_directory, session
from flask_cors import CORS
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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(report_bp)
    
    @app.route('/api/auth/setup/status', methods=['GET'])
    def setup_status():
        from backend.models.database import db
        result = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        has_admin = result and result[0]['count'] > 0
        return {'needs_setup': not has_admin}
    
    @app.route('/api/auth/setup', methods=['POST'])
    def setup_admin_direct():
        from flask import request, jsonify
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        from backend.models.database import db
        result = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
        if result and result[0]['count'] > 0:
            return jsonify({'error': 'Admin already exists'}), 403
        
        try:
            from backend.models.user_model import UserModel
            user_id = UserModel.create(username, password, 'admin')
            user = UserModel.authenticate(username, password)
            from backend.auth.auth_service import AuthService
            AuthService.login_user(user)
            return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    
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
    
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.close()
        print(f"Database created at: {db_path}")

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000)