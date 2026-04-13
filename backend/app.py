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
from backend.utils.backup import backup_bp          # ← new


def create_app(test_config=None):
    app = Flask(__name__, static_folder='../frontend', static_url_path='')

    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)

    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    init_database()

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(backup_bp)               # ← new

    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'ok'})

    @app.route('/api/auth/setup/status', methods=['GET'])
    def setup_status():
        db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        has_admin = cursor.fetchone()[0] > 0
        conn.close()
        return jsonify({'needs_setup': not has_admin})

    @app.route('/api/auth/setup', methods=['POST'])
    def setup_admin_direct():
        from flask import request
        import bcrypt, traceback

        try:
            data     = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')

            from backend.utils.validators import Validators
            valid, error = Validators.validate_username(username)
            if not valid:
                return jsonify({'error': error}), 400
            valid, error = Validators.validate_password(password)
            if not valid:
                return jsonify({'error': error}), 400

            db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
            conn    = sqlite3.connect(db_path)
            cursor  = conn.cursor()

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
            if not cursor.fetchone():
                schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
                with open(schema_path, 'r') as f:
                    conn.executescript(f.read())

            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] > 0:
                conn.close()
                return jsonify({'error': 'Admin already exists'}), 403

            import uuid
            user_id       = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (user_id, username, password_hash, 'admin')
            )
            conn.commit()
            conn.close()

            from backend.auth.auth_service import AuthService
            AuthService.login_user({'id': user_id, 'username': username, 'role': 'admin'})
            return jsonify({'success': True, 'user': {'id': user_id, 'username': username, 'role': 'admin'}})

        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

    @app.route('/api/auth/login', methods=['POST'])
    def login_direct():
        from flask import request
        import bcrypt, traceback

        try:
            data     = request.get_json()
            username = data.get('username', '').strip()
            password = data.get('password', '')

            if not username or not password:
                return jsonify({'error': 'Username and password required'}), 400

            db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
            conn    = sqlite3.connect(db_path)
            cursor  = conn.cursor()
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
            import traceback
            print(traceback.format_exc())
            return jsonify({'error': str(e)}), 500

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and path.startswith('api/'):
            return jsonify({'error': 'API endpoint not found'}), 404
        return send_from_directory(app.static_folder, 'index.html')

    return app


def init_database():
    import os
    db_path     = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
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
