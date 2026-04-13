from flask import Flask, send_from_directory, session, jsonify, request
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
from backend.utils.backup import backup_bp
from backend.utils.rate_limiter import rate_limit
from backend.utils.csrf import get_csrf_token, require_csrf
from backend.utils.migrations import run_migrations


def create_app(test_config=None):
    app = Flask(__name__, static_folder='../frontend', static_url_path='')

    if test_config:
        app.config.update(test_config)
    else:
        app.config.from_object(Config)

    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    init_database()
    _db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
    run_migrations(_db_path)

    app.register_blueprint(auth_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(log_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(backup_bp)

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'success': False, 'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'success': False, 'error': 'Authentication required'}), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'success': False, 'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'success': False, 'error': 'Not found'}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({'success': False, 'error': 'Method not allowed'}), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        return jsonify({'success': False, 'error': 'Too many requests. Please wait and try again.'}), 429

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @app.route('/api/auth/csrf-token', methods=['GET'])
    def csrf_token():
        return jsonify({'csrf_token': get_csrf_token()})

    @app.route('/api/health')
    def health_check():
        return jsonify({'success': True, 'status': 'ok'})

    @app.route('/api/auth/setup/status', methods=['GET'])
    def setup_status():
        db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        has_admin = cursor.fetchone()[0] > 0
        conn.close()
        return jsonify({'success': True, 'needs_setup': not has_admin})

    @app.route('/api/auth/setup', methods=['POST'])
    @rate_limit(max_requests=5, window_seconds=300, scope='setup')
    def setup_admin_direct():
        import bcrypt, traceback, uuid
        try:
            data     = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '')

            from backend.utils.validators import Validators
            valid, error = Validators.validate_username(username)
            if not valid:
                return jsonify({'success': False, 'error': error}), 400
            valid, error = Validators.validate_password(password)
            if not valid:
                return jsonify({'success': False, 'error': error}), 400

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
                return jsonify({'success': False, 'error': 'Admin already exists'}), 403

            user_id       = str(uuid.uuid4())
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute(
                "INSERT INTO users (id, username, password_hash, role, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (user_id, username, password_hash, 'admin')
            )
            conn.commit()
            conn.close()

            from backend.auth.auth_service import AuthService
            user = {'id': user_id, 'username': username, 'role': 'admin'}
            AuthService.login_user(user)
            return jsonify({'success': True, 'user': user})

        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/auth/login', methods=['POST'])
    @rate_limit(max_requests=10, window_seconds=300, scope='login')
    def login_direct():
        import bcrypt, traceback
        try:
            data     = request.get_json() or {}
            username = data.get('username', '').strip()
            password = data.get('password', '')

            if not username or not password:
                return jsonify({'success': False, 'error': 'Username and password required'}), 400

            db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
            conn    = sqlite3.connect(db_path)
            cursor  = conn.cursor()
            cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()

            if not row:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

            if bcrypt.checkpw(password.encode('utf-8'), row[2].encode('utf-8')):
                from backend.auth.auth_service import AuthService
                user = {'id': row[0], 'username': row[1], 'role': row[3]}
                AuthService.login_user(user)
                return jsonify({'success': True, 'user': user})

            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

        except Exception as e:
            print(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/admin/migrations', methods=['GET'])
    def migration_status():
        from backend.auth.auth_service import AuthService
        from backend.utils.migrations import get_migration_status
        if not AuthService.is_admin():
            return jsonify({'success': False, 'error': 'Admin required'}), 403
        db_path = '/tmp/shopkeep.db' if os.environ.get('RENDER') else Config.DATABASE_PATH
        return jsonify({'success': True, 'migrations': get_migration_status(db_path)})

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        if path and path.startswith('api/'):
            return jsonify({'success': False, 'error': 'API endpoint not found'}), 404
        return send_from_directory(app.static_folder, 'index.html')

    return app


def init_database():
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
