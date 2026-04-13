from flask import Flask, send_from_directory, session, jsonify
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
    
    # INITIALIZE DATABASE FIRST
    init_database()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(report_bp)
    
    # Direct API routes
    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok'})
    
    @app.route('/api/auth/setup/status', methods=['GET'])
    def setup_status():
        import sqlite3
        db_path = '/tmp/shopkeep.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        has_admin = cursor.fetchone()[0] > 0
        conn.close()
        return jsonify({'needs_setup': not has_admin})
    
    @app.route('/api/auth/setup', methods=['POST'])
    def setup_admin_direct():
        from flask import jsonify, request
        import sqlite3
        import traceback
        import os
        
        try:
            print("=== SETUP ATTEMPT ===")
            data = request.get_json()
            print(f"Received data: {data}")
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or len(username) < 3:
                return jsonify({'error': 'Username must be at least 3 characters'}), 400
            if not password or len(password) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            
            db_path = '/tmp/shopkeep.db'
            print(f"Database path: {db_path}")
            print(f"Database exists: {os.path.exists(db_path)}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if users table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                print("Users table doesn't exist, creating schema...")
                schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
                print(f"Schema path: {schema_path}")
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())
                print("Schema created")
            
            # Check if admin exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] > 0:
                conn.close()
                return jsonify({'error': 'Admin already exists'}), 403
            
            # Create admin
            import uuid
            import bcrypt
            user_id = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (user_id, username, password_hash, 'admin')
            )
            conn.commit()
            conn.close()
            print(f"Admin created: {username}")
            
            from backend.auth.auth_service import AuthService
            AuthService.login_user({'id': user_id, 'username': username, 'role': 'admin'})
            
            return jsonify({'success': True, 'user': {'id': user_id, 'username': username, 'role': 'admin'}})
            
        except Exception as e:
            print(f"SETUP ERROR: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/auth/login', methods=['POST'])
    def login_direct():
        from flask import jsonify, request
        import sqlite3
        import bcrypt
        import traceback
        
        try:
            data = request.get_json()
            print(f"Login attempt: {data}")
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400
            
            db_path = '/tmp/shopkeep.db'
            print(f"Database path: {db_path}")
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return jsonify({'error': 'Invalid credentials'}), 401
            
            if bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8')):
                from backend.auth.auth_service import AuthService
                user = {'id': row[0], 'username': row[1], 'role': row[3]}
                AuthService.login_user(user)
                return jsonify({'success': True, 'user': user})
            
            return jsonify({'error': 'Invalid credentials'}), 401
            
        except Exception as e:
            print(f"Login error: {traceback.format_exc()}")
            return jsonify({'error': str(e)}), 500
    
    # Static file route LAST
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return send_from_directory(app.static_folder, 'index.html')
    
    return app

def init_database():
    # Use the correct path for Render
    import os
    if os.environ.get('RENDER'):
        db_path = '/tmp/shopkeep.db'
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    else:
        db_path = Config.DATABASE_PATH
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    if not os.path.exists(db_path):
        import sqlite3
        conn = sqlite3.connect(db_path)
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.close()
        print(f"Database created at: {db_path}")

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000)