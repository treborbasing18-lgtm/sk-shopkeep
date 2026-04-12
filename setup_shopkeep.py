#!/usr/bin/env python3
"""
SK ShopKeep - Automatic Project Setup
Run this script to create all necessary files and folders.
"""

import os
import sys

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(BASE_DIR, 'shopkeep')

def create_directory(path):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)
    print(f"✓ Created: {path}")

def create_file(path, content):
    """Create file with content"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Created: {path}")

def setup_project():
    """Create the entire project structure"""
    
    print("\n" + "="*60)
    print("SK ShopKeep - Project Setup")
    print("="*60 + "\n")
    
    # Create directory structure
    print("Creating directory structure...")
    create_directory(PROJECT_DIR)
    create_directory(os.path.join(PROJECT_DIR, 'backend'))
    create_directory(os.path.join(PROJECT_DIR, 'backend', 'auth'))
    create_directory(os.path.join(PROJECT_DIR, 'backend', 'routes'))
    create_directory(os.path.join(PROJECT_DIR, 'backend', 'models'))
    create_directory(os.path.join(PROJECT_DIR, 'backend', 'utils'))
    create_directory(os.path.join(PROJECT_DIR, 'database'))
    create_directory(os.path.join(PROJECT_DIR, 'frontend'))
    create_directory(os.path.join(PROJECT_DIR, 'frontend', 'css'))
    create_directory(os.path.join(PROJECT_DIR, 'frontend', 'js'))
    create_directory(os.path.join(PROJECT_DIR, 'backups'))
    
    # Create __init__.py files
    print("\nCreating Python package files...")
    create_file(os.path.join(PROJECT_DIR, 'backend', '__init__.py'), '')
    create_file(os.path.join(PROJECT_DIR, 'backend', 'auth', '__init__.py'), '')
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', '__init__.py'), 
                'from .auth_routes import auth_bp\nfrom .product_routes import product_bp\nfrom .sales_routes import sales_bp\nfrom .user_routes import user_bp\nfrom .log_routes import log_bp\nfrom .report_routes import report_bp\n')
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', '__init__.py'), '')
    create_file(os.path.join(PROJECT_DIR, 'backend', 'utils', '__init__.py'), '')
    
    # Create requirements.txt
    print("\nCreating requirements file...")
    requirements = """Flask==3.0.0
Flask-CORS==4.0.0
bcrypt==4.1.2
Flask-Session==0.5.0
python-dotenv==1.0.0
"""
    create_file(os.path.join(PROJECT_DIR, 'backend', 'requirements.txt'), requirements)
    
    # Create config.py
    print("\nCreating backend files...")
    config_content = '''import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'shopkeep_'
    
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'shopkeep.db')
    BACKUP_PATH = os.path.join(os.path.dirname(__file__), '..', 'backups')
    
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:8000']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'config.py'), config_content)
    
    # Create database schema
    print("\nCreating database schema...")
    schema_content = '''-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff')),
    created_at TEXT NOT NULL
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    quantity INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reorder_threshold INTEGER NOT NULL DEFAULT 10 CHECK (reorder_threshold >= 0)
);

-- Sales table
CREATE TABLE IF NOT EXISTS sales (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    total REAL NOT NULL CHECK (total >= 0),
    user_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);

-- Logs table
CREATE TABLE IF NOT EXISTS logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_sales_timestamp ON sales(timestamp);
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales(product_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
'''
    create_file(os.path.join(PROJECT_DIR, 'database', 'schema.sql'), schema_content)
    
    # Create database.py
    database_content = '''import sqlite3
import uuid
from contextlib import contextmanager
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute_insert(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid
    
    def execute_update(self, query, params=()):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.rowcount

db = Database()
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', 'database.py'), database_content)
    
    # Create user_model.py
    user_model_content = '''import uuid
import bcrypt
from models.database import db

class UserModel:
    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def create(username, password, role='staff'):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        if role not in ['admin', 'staff']:
            raise ValueError("Invalid role")
        
        existing = db.execute_query(
            "SELECT id FROM users WHERE username = ?", 
            (username,)
        )
        if existing:
            raise ValueError("Username already exists")
        
        user_id = str(uuid.uuid4())
        password_hash = UserModel.hash_password(password)
        
        db.execute_insert(
            """INSERT INTO users (id, username, password_hash, role, created_at) 
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (user_id, username, password_hash, role)
        )
        return user_id
    
    @staticmethod
    def authenticate(username, password):
        if not username or not password:
            return None
        
        result = db.execute_query(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        
        if not result:
            return None
        
        user = dict(result[0])
        if UserModel.verify_password(password, user['password_hash']):
            del user['password_hash']
            return user
        return None
    
    @staticmethod
    def get_all():
        result = db.execute_query(
            "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
        )
        return [dict(row) for row in result]
    
    @staticmethod
    def delete(user_id):
        return db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))
    
    @staticmethod
    def get_by_id(user_id):
        result = db.execute_query(
            "SELECT id, username, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        return dict(result[0]) if result else None
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', 'user_model.py'), user_model_content)
    
    # Create product_model.py
    product_model_content = '''import uuid
from models.database import db

class ProductModel:
    @staticmethod
    def validate(data):
        errors = []
        if not data.get('name') or len(data['name'].strip()) == 0:
            errors.append("Product name is required")
        elif len(data['name']) > 100:
            errors.append("Product name too long")
        if not data.get('category') or len(data['category'].strip()) == 0:
            errors.append("Category is required")
        price = data.get('price')
        if price is None or price < 0:
            errors.append("Price must be non-negative")
        elif price > 999999.99:
            errors.append("Price too high")
        quantity = data.get('quantity', 0)
        if quantity < 0:
            errors.append("Quantity cannot be negative")
        threshold = data.get('reorder_threshold', 10)
        if threshold < 0:
            errors.append("Reorder threshold cannot be negative")
        return errors
    
    @staticmethod
    def create(data):
        errors = ProductModel.validate(data)
        if errors:
            raise ValueError(errors[0])
        
        existing = db.execute_query(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?)",
            (data['name'].strip(),)
        )
        if existing:
            raise ValueError("Product name already exists")
        
        product_id = str(uuid.uuid4())
        db.execute_insert(
            """INSERT INTO products (id, name, category, price, quantity, reorder_threshold)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (product_id, data['name'].strip(), data['category'].strip(),
             float(data['price']), int(data.get('quantity', 0)),
             int(data.get('reorder_threshold', 10)))
        )
        return product_id
    
    @staticmethod
    def update(product_id, data):
        errors = ProductModel.validate(data)
        if errors:
            raise ValueError(errors[0])
        
        existing = db.execute_query(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND id != ?",
            (data['name'].strip(), product_id)
        )
        if existing:
            raise ValueError("Product name already exists")
        
        rows = db.execute_update(
            """UPDATE products 
               SET name = ?, category = ?, price = ?, quantity = ?, reorder_threshold = ?
               WHERE id = ?""",
            (data['name'].strip(), data['category'].strip(), float(data['price']),
             int(data.get('quantity', 0)), int(data.get('reorder_threshold', 10)), product_id)
        )
        if rows == 0:
            raise ValueError("Product not found")
        return True
    
    @staticmethod
    def delete(product_id):
        rows = db.execute_update("DELETE FROM products WHERE id = ?", (product_id,))
        if rows == 0:
            raise ValueError("Product not found")
        return True
    
    @staticmethod
    def get_all():
        result = db.execute_query(
            """SELECT id, name, category, price, quantity, reorder_threshold 
               FROM products ORDER BY name"""
        )
        return [dict(row) for row in result]
    
    @staticmethod
    def get_by_id(product_id):
        result = db.execute_query(
            """SELECT id, name, category, price, quantity, reorder_threshold 
               FROM products WHERE id = ?""",
            (product_id,)
        )
        return dict(result[0]) if result else None
    
    @staticmethod
    def update_quantity(product_id, new_quantity):
        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative")
        rows = db.execute_update(
            "UPDATE products SET quantity = ? WHERE id = ?",
            (new_quantity, product_id)
        )
        if rows == 0:
            raise ValueError("Product not found")
        return True
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', 'product_model.py'), product_model_content)
    
    # Create sales_model.py
    sales_model_content = '''import uuid
from models.database import db
from models.product_model import ProductModel

class SalesModel:
    @staticmethod
    def create(product_id, quantity, user_id):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        product = ProductModel.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        if quantity > product['quantity']:
            raise ValueError(f"Insufficient stock. Only {product['quantity']} available.")
        
        total = quantity * product['price']
        sale_id = str(uuid.uuid4())
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (quantity, product_id)
            )
            cursor.execute(
                """INSERT INTO sales (id, product_id, quantity, unit_price, total, user_id, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (sale_id, product_id, quantity, product['price'], total, user_id)
            )
        return {'id': sale_id, 'product_name': product['name'], 'quantity': quantity, 'total': total}
    
    @staticmethod
    def get_all(limit=None):
        query = """
            SELECT s.id, s.quantity, s.unit_price, s.total, s.timestamp,
                   p.name as product_name, u.username as seller
            FROM sales s
            JOIN products p ON s.product_id = p.id
            JOIN users u ON s.user_id = u.id
            ORDER BY s.timestamp DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        result = db.execute_query(query)
        return [dict(row) for row in result]
    
    @staticmethod
    def get_total_revenue():
        result = db.execute_query("SELECT COALESCE(SUM(total), 0) as total FROM sales")
        return result[0]['total'] if result else 0
    
    @staticmethod
    def get_top_products(limit=10):
        result = db.execute_query(
            """SELECT p.name, SUM(s.quantity) as total_quantity, SUM(s.total) as total_revenue
               FROM sales s
               JOIN products p ON s.product_id = p.id
               GROUP BY p.id
               ORDER BY total_quantity DESC
               LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in result]
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', 'sales_model.py'), sales_model_content)
    
    # Create log_model.py
    log_model_content = '''import uuid
from models.database import db

class LogModel:
    @staticmethod
    def create(user_id, action, details):
        log_id = str(uuid.uuid4())
        db.execute_insert(
            """INSERT INTO logs (id, user_id, action, details, timestamp)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (log_id, user_id, action, details)
        )
        return log_id
    
    @staticmethod
    def get_all(limit=100):
        result = db.execute_query(
            """SELECT l.*, u.username 
               FROM logs l
               LEFT JOIN users u ON l.user_id = u.id
               ORDER BY l.timestamp DESC
               LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in result]
    
    @staticmethod
    def log_login_attempt(username, success, ip_address=None):
        action = 'LOGIN_SUCCESS' if success else 'LOGIN_FAILED'
        details = f"Username: {username}"
        if ip_address:
            details += f", IP: {ip_address}"
        log_id = str(uuid.uuid4())
        db.execute_insert(
            "INSERT INTO logs (id, action, details, timestamp) VALUES (?, ?, ?, datetime('now'))",
            (log_id, action, details)
        )
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'models', 'log_model.py'), log_model_content)
    
    # Create auth_service.py
    auth_service_content = '''from functools import wraps
from flask import session, jsonify

class AuthService:
    @staticmethod
    def login_user(user):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True
    
    @staticmethod
    def logout_user():
        session.clear()
    
    @staticmethod
    def get_current_user():
        if 'user_id' not in session:
            return None
        return {'id': session['user_id'], 'username': session['username'], 'role': session['role']}
    
    @staticmethod
    def is_authenticated():
        return 'user_id' in session
    
    @staticmethod
    def is_admin():
        return session.get('role') == 'admin'
    
    @staticmethod
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AuthService.is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated
    
    @staticmethod
    def require_admin(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AuthService.is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            if not AuthService.is_admin():
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        return decorated
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'auth', 'auth_service.py'), auth_service_content)
    
    # Create validators.py
    validators_content = '''import re

class Validators:
    @staticmethod
    def validate_username(username):
        if not username or len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 50:
            return False, "Username too long"
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "Username can only contain letters, numbers, and underscores"
        return True, None
    
    @staticmethod
    def validate_password(password):
        if not password or len(password) < 6:
            return False, "Password must be at least 6 characters"
        if len(password) > 128:
            return False, "Password too long"
        return True, None
    
    @staticmethod
    def validate_product_data(data):
        required_fields = ['name', 'category', 'price']
        for field in required_fields:
            if field not in data:
                return False, f"Missing required field: {field}"
        if not data['name'] or len(data['name'].strip()) == 0:
            return False, "Product name is required"
        try:
            price = float(data['price'])
            if price < 0:
                return False, "Price cannot be negative"
        except (ValueError, TypeError):
            return False, "Invalid price format"
        return True, None
    
    @staticmethod
    def validate_sale_data(data):
        if 'product_id' not in data:
            return False, "Product ID is required"
        if 'quantity' not in data:
            return False, "Quantity is required"
        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                return False, "Quantity must be positive"
        except (ValueError, TypeError):
            return False, "Invalid quantity format"
        return True, None
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'utils', 'validators.py'), validators_content)
    
    # Create backup.py
    backup_content = '''import os
import shutil
from datetime import datetime
from config import Config

class BackupService:
    @staticmethod
    def create_backup():
        db_path = Config.DATABASE_PATH
        backup_dir = Config.BACKUP_PATH
        if not os.path.exists(db_path):
            raise FileNotFoundError("Database file not found")
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"shopkeep_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        shutil.copy2(db_path, backup_path)
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.db')])
        if len(backups) > 10:
            for old_backup in backups[:-10]:
                os.remove(os.path.join(backup_dir, old_backup))
        return backup_filename
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'utils', 'backup.py'), backup_content)
    
    # Create auth_routes.py
    auth_routes_content = '''from flask import Blueprint, request, jsonify
from models.user_model import UserModel
from models.log_model import LogModel
from auth.auth_service import AuthService
from utils.validators import Validators

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        LogModel.log_login_attempt(username, False, request.remote_addr)
        return jsonify({'error': 'Username and password required'}), 400
    
    user = UserModel.authenticate(username, password)
    if user:
        AuthService.login_user(user)
        LogModel.log_login_attempt(username, True, request.remote_addr)
        LogModel.create(user['id'], 'LOGIN', f"User logged in")
        return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
    else:
        LogModel.log_login_attempt(username, False, request.remote_addr)
        return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    user = AuthService.get_current_user()
    if user:
        LogModel.create(user['id'], 'LOGOUT', 'User logged out')
    AuthService.logout_user()
    return jsonify({'success': True})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    user = AuthService.get_current_user()
    if not user:
        return jsonify({'error': 'Not authenticated'}), 401
    return jsonify({'user': user})

@auth_bp.route('/setup', methods=['POST'])
def setup_first_user():
    from models.database import db
    result = db.execute_query("SELECT COUNT(*) as count FROM users")
    if result and result[0]['count'] > 0:
        return jsonify({'error': 'Setup already completed'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    valid, error = Validators.validate_username(username)
    if not valid:
        return jsonify({'error': error}), 400
    valid, error = Validators.validate_password(password)
    if not valid:
        return jsonify({'error': error}), 400
    
    try:
        user_id = UserModel.create(username, password, 'admin')
        LogModel.create(user_id, 'SETUP_COMPLETED', 'First admin user created')
        user = UserModel.authenticate(username, password)
        AuthService.login_user(user)
        return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/check-first-run', methods=['GET'])
def check_first_run():
    from models.database import db
    result = db.execute_query("SELECT COUNT(*) as count FROM users")
    has_users = result and result[0]['count'] > 0
    return jsonify({'needs_setup': not has_users})
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'auth_routes.py'), auth_routes_content)
    
    # Create product_routes.py
    product_routes_content = '''from flask import Blueprint, request, jsonify
from models.product_model import ProductModel
from models.log_model import LogModel
from auth.auth_service import AuthService
from utils.validators import Validators

product_bp = Blueprint('products', __name__, url_prefix='/api/products')

@product_bp.route('', methods=['GET'])
@AuthService.require_auth
def get_products():
    products = ProductModel.get_all()
    return jsonify({'products': products})

@product_bp.route('', methods=['POST'])
@AuthService.require_auth
def create_product():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    valid, error = Validators.validate_product_data(data)
    if not valid:
        return jsonify({'error': error}), 400
    
    try:
        product_id = ProductModel.create(data)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'CREATE_PRODUCT', f"Created product: {data['name']}")
        return jsonify({'success': True, 'product_id': product_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@product_bp.route('/<product_id>', methods=['PUT'])
@AuthService.require_auth
def update_product(product_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    valid, error = Validators.validate_product_data(data)
    if not valid:
        return jsonify({'error': error}), 400
    
    try:
        ProductModel.update(product_id, data)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'UPDATE_PRODUCT', f"Updated product: {data['name']}")
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@product_bp.route('/<product_id>', methods=['DELETE'])
@AuthService.require_admin
def delete_product(product_id):
    try:
        product = ProductModel.get_by_id(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        ProductModel.delete(product_id)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'DELETE_PRODUCT', f"Deleted product: {product['name']}")
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'product_routes.py'), product_routes_content)
    
    # Create sales_routes.py
    sales_routes_content = '''from flask import Blueprint, request, jsonify
from models.sales_model import SalesModel
from models.log_model import LogModel
from auth.auth_service import AuthService
from utils.validators import Validators

sales_bp = Blueprint('sales', __name__, url_prefix='/api/sales')

@sales_bp.route('', methods=['GET'])
@AuthService.require_auth
def get_sales():
    limit = request.args.get('limit', type=int)
    sales = SalesModel.get_all(limit)
    return jsonify({'sales': sales})

@sales_bp.route('', methods=['POST'])
@AuthService.require_auth
def create_sale():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    valid, error = Validators.validate_sale_data(data)
    if not valid:
        return jsonify({'error': error}), 400
    
    try:
        user = AuthService.get_current_user()
        sale = SalesModel.create(data['product_id'], data['quantity'], user['id'])
        LogModel.create(user['id'], 'RECORD_SALE', 
                       f"Sold {sale['quantity']}x {sale['product_name']} for ₱{sale['total']:.2f}")
        return jsonify({'success': True, 'sale': sale}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@sales_bp.route('/stats', methods=['GET'])
@AuthService.require_auth
def get_sales_stats():
    total_revenue = SalesModel.get_total_revenue()
    top_products = SalesModel.get_top_products(10)
    return jsonify({'total_revenue': total_revenue, 'top_products': top_products})
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'sales_routes.py'), sales_routes_content)
    
    # Create user_routes.py
    user_routes_content = '''from flask import Blueprint, request, jsonify
from models.user_model import UserModel
from models.log_model import LogModel
from auth.auth_service import AuthService
from utils.validators import Validators

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

@user_bp.route('', methods=['GET'])
@AuthService.require_admin
def get_users():
    users = UserModel.get_all()
    return jsonify({'users': users})

@user_bp.route('', methods=['POST'])
@AuthService.require_admin
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'staff')
    
    valid, error = Validators.validate_username(username)
    if not valid:
        return jsonify({'error': error}), 400
    valid, error = Validators.validate_password(password)
    if not valid:
        return jsonify({'error': error}), 400
    if role not in ['admin', 'staff']:
        return jsonify({'error': 'Invalid role'}), 400
    
    try:
        user_id = UserModel.create(username, password, role)
        current_user = AuthService.get_current_user()
        LogModel.create(current_user['id'], 'CREATE_USER', f"Created user: {username} ({role})")
        return jsonify({'success': True, 'user_id': user_id}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@user_bp.route('/<user_id>', methods=['DELETE'])
@AuthService.require_admin
def delete_user(user_id):
    current_user = AuthService.get_current_user()
    if user_id == current_user['id']:
        return jsonify({'error': 'Cannot delete yourself'}), 400
    
    user = UserModel.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        UserModel.delete(user_id)
        LogModel.create(current_user['id'], 'DELETE_USER', f"Deleted user: {user['username']}")
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'user_routes.py'), user_routes_content)
    
    # Create log_routes.py
    log_routes_content = '''from flask import Blueprint, request, jsonify
from models.log_model import LogModel
from auth.auth_service import AuthService

log_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

@log_bp.route('', methods=['GET'])
@AuthService.require_admin
def get_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = LogModel.get_all(limit)
    return jsonify({'logs': logs})
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'log_routes.py'), log_routes_content)
    
    # Create report_routes.py
    report_routes_content = '''from flask import Blueprint, jsonify
from models.sales_model import SalesModel
from auth.auth_service import AuthService

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/summary', methods=['GET'])
@AuthService.require_auth
def get_summary():
    total_revenue = SalesModel.get_total_revenue()
    top_products = SalesModel.get_top_products(10)
    return jsonify({'total_revenue': total_revenue, 'top_products': top_products})
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'routes', 'report_routes.py'), report_routes_content)
    
    # Create app.py
    app_content = '''from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
import os

from config import Config
from routes import auth_bp, product_bp, sales_bp, user_bp, log_bp, report_bp

def create_app():
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
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
    import sqlite3
    db_path = Config.DATABASE_PATH
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema.sql')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db_exists = os.path.exists(db_path)
    conn = sqlite3.connect(db_path)
    if not db_exists:
        with open(schema_path, 'r') as f:
            schema = f.read()
        conn.executescript(schema)
    conn.close()

if __name__ == '__main__':
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False)
'''
    create_file(os.path.join(PROJECT_DIR, 'backend', 'app.py'), app_content)
    
    # Create frontend files
    print("\nCreating frontend files...")
    
    # index.html
    index_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SK ShopKeep</title>
    <link rel="stylesheet" href="css/styles.css">
</head>
<body>
    <div id="app">Loading...</div>
    <script src="js/api.js"></script>
    <script src="js/auth.js"></script>
    <script src="js/app.js"></script>
</body>
</html>'''
    create_file(os.path.join(PROJECT_DIR, 'frontend', 'index.html'), index_content)
    
    # api.js
    api_content = '''const API_BASE = 'http://localhost:5000/api';

class ApiService {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            credentials: 'include',
            headers: {'Content-Type': 'application/json', ...options.headers},
            ...options
        };
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Request failed');
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    static async checkFirstRun() { return this.request('/auth/check-first-run'); }
    static async setup(username, password) { return this.request('/auth/setup', {method: 'POST', body: JSON.stringify({username, password})}); }
    static async login(username, password) { return this.request('/auth/login', {method: 'POST', body: JSON.stringify({username, password})}); }
    static async logout() { return this.request('/auth/logout', {method: 'POST'}); }
    static async getCurrentUser() { return this.request('/auth/me'); }
    static async getProducts() { return this.request('/products'); }
    static async createProduct(data) { return this.request('/products', {method: 'POST', body: JSON.stringify(data)}); }
    static async updateProduct(id, data) { return this.request(`/products/${id}`, {method: 'PUT', body: JSON.stringify(data)}); }
    static async deleteProduct(id) { return this.request(`/products/${id}`, {method: 'DELETE'}); }
    static async getSales(limit = null) { const query = limit ? `?limit=${limit}` : ''; return this.request(`/sales${query}`); }
    static async createSale(data) { return this.request('/sales', {method: 'POST', body: JSON.stringify(data)}); }
    static async getSalesStats() { return this.request('/sales/stats'); }
    static async getUsers() { return this.request('/users'); }
    static async createUser(data) { return this.request('/users', {method: 'POST', body: JSON.stringify(data)}); }
    static async deleteUser(id) { return this.request(`/users/${id}`, {method: 'DELETE'}); }
    static async getLogs(limit = 100) { return this.request(`/logs?limit=${limit}`); }
}'''
    create_file(os.path.join(PROJECT_DIR, 'frontend', 'js', 'api.js'), api_content)
    
    # auth.js
    auth_content = '''class AuthManager {
    constructor() {
        this.user = null;
        this.isAuthenticated = false;
        this.isAdmin = false;
    }
    
    async checkAuth() {
        try {
            const data = await ApiService.getCurrentUser();
            this.user = data.user;
            this.isAuthenticated = true;
            this.isAdmin = data.user.role === 'admin';
            return true;
        } catch (error) {
            this.user = null;
            this.isAuthenticated = false;
            this.isAdmin = false;
            return false;
        }
    }
    
    async login(username, password) {
        const data = await ApiService.login(username, password);
        if (data.success) {
            this.user = data.user;
            this.isAuthenticated = true;
            this.isAdmin = data.user.role === 'admin';
        }
        return data;
    }
    
    async logout() {
        await ApiService.logout();
        this.user = null;
        this.isAuthenticated = false;
        this.isAdmin = false;
    }
    
    async setup(username, password) {
        const data = await ApiService.setup(username, password);
        if (data.success) {
            this.user = data.user;
            this.isAuthenticated = true;
            this.isAdmin = data.user.role === 'admin';
        }
        return data;
    }
    
    getUser() { return this.user; }
}

const auth = new AuthManager();'''
    create_file(os.path.join(PROJECT_DIR, 'frontend', 'js', 'auth.js'), auth_content)
    
    # Create a simplified app.js
    app_js_content = '''class ShopKeepApp {
    constructor() {
        this.currentView = 'dashboard';
        this.state = { products: [], sales: [], stats: null, loading: false, error: null };
        this.init();
    }
    
    async init() {
        try {
            const data = await ApiService.checkFirstRun();
            if (data.needs_setup) {
                this.showSetup();
                return;
            }
        } catch (error) {}
        
        const isAuth = await auth.checkAuth();
        if (isAuth) {
            await this.loadInitialData();
            this.showApp();
        } else {
            this.showLogin();
        }
    }
    
    async loadInitialData() {
        this.state.loading = true;
        this.render();
        try {
            const [productsRes, salesRes, statsRes] = await Promise.all([
                ApiService.getProducts(), ApiService.getSales(10), ApiService.getSalesStats()
            ]);
            this.state.products = productsRes.products || [];
            this.state.sales = salesRes.sales || [];
            this.state.stats = statsRes;
        } catch (error) {
            this.state.error = 'Failed to load data';
        } finally {
            this.state.loading = false;
            this.render();
        }
    }
    
    showLogin() {
        document.body.innerHTML = `
            <div class="auth-container">
                <div class="auth-box">
                    <h2>SK ShopKeep</h2>
                    <p>Sign in to continue</p>
                    <div id="login-error" class="error-message"></div>
                    <form id="login-form">
                        <input type="text" id="username" placeholder="Username" required>
                        <input type="password" id="password" placeholder="Password" required>
                        <button type="submit">Sign In</button>
                    </form>
                </div>
            </div>
        `;
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            try {
                await auth.login(username, password);
                await this.loadInitialData();
                this.showApp();
            } catch (error) {
                document.getElementById('login-error').textContent = error.message;
            }
        });
    }
    
    showSetup() {
        document.body.innerHTML = `
            <div class="auth-container">
                <div class="auth-box">
                    <h2>Welcome to SK ShopKeep</h2>
                    <p>Create your admin account</p>
                    <div id="setup-error" class="error-message"></div>
                    <form id="setup-form">
                        <input type="text" id="username" placeholder="Username" required minlength="3">
                        <input type="password" id="password" placeholder="Password" required minlength="6">
                        <input type="password" id="confirm-password" placeholder="Confirm Password" required>
                        <button type="submit">Create Account</button>
                    </form>
                </div>
            </div>
        `;
        document.getElementById('setup-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const confirm = document.getElementById('confirm-password').value;
            if (password !== confirm) {
                document.getElementById('setup-error').textContent = 'Passwords do not match';
                return;
            }
            try {
                await auth.setup(username, password);
                await this.loadInitialData();
                this.showApp();
            } catch (error) {
                document.getElementById('setup-error').textContent = error.message;
            }
        });
    }
    
    showApp() {
        const user = auth.getUser();
        document.body.innerHTML = `
            <div class="app-container">
                <nav class="sidebar">
                    <div class="sidebar-header"><h3>SK ShopKeep</h3></div>
                    <ul class="nav-menu">
                        <li class="nav-item active" data-view="dashboard">Dashboard</li>
                        <li class="nav-item" data-view="inventory">Inventory</li>
                        <li class="nav-item" data-view="sales">Record Sale</li>
                        <li class="nav-item" data-view="reports">Reports</li>
                        ${user.role === 'admin' ? '<li class="nav-item" data-view="users">Users</li><li class="nav-item" data-view="logs">Logs</li>' : ''}
                    </ul>
                    <div class="sidebar-footer">
                        <div class="user-info">${user.username} (${user.role})</div>
                        <button id="logout-btn" class="btn-secondary">Sign Out</button>
                    </div>
                </nav>
                <main class="main-content">
                    <div id="content-area">${this.renderContent()}</div>
                </main>
            </div>
        `;
        this.attachEvents();
    }
    
    renderContent() {
        if (this.state.loading) return '<div class="loading">Loading...</div>';
        const products = this.state.products || [];
        const stats = this.state.stats || { total_revenue: 0 };
        return `
            <div class="page-header"><h1>Dashboard</h1></div>
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-label">Products</div><div class="stat-value">${products.length}</div></div>
                <div class="stat-card"><div class="stat-label">Revenue</div><div class="stat-value">₱${stats.total_revenue.toFixed(2)}</div></div>
            </div>
            <div class="card">
                <h3>Quick Actions</h3>
                <div style="padding:20px">
                    <button class="btn-primary" data-action="add-product">+ Add Product</button>
                    <button class="btn-secondary" style="margin-left:10px" data-action="record-sale">Record Sale</button>
                </div>
            </div>
        `;
    }
    
    attachEvents() {
        document.querySelectorAll('[data-view]').forEach(el => {
            el.addEventListener('click', (e) => {
                this.currentView = e.target.dataset.view;
                this.showApp();
            });
        });
        document.getElementById('logout-btn')?.addEventListener('click', async () => {
            await auth.logout();
            this.showLogin();
        });
        document.addEventListener('click', (e) => {
            if (e.target.dataset.action === 'add-product') this.showProductModal();
            if (e.target.dataset.action === 'record-sale') alert('Sale feature coming soon!');
        });
    }
    
    showProductModal() {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content">
                <h3>Add Product</h3>
                <form id="product-form">
                    <div class="form-group"><label>Name</label><input type="text" id="pname" required></div>
                    <div class="form-group"><label>Category</label><input type="text" id="pcat" required></div>
                    <div class="form-group"><label>Price (₱)</label><input type="number" id="pprice" min="0" step="0.01" required></div>
                    <div class="form-group"><label>Quantity</label><input type="number" id="pqty" min="0" value="0"></div>
                    <div class="modal-actions">
                        <button type="button" class="btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                        <button type="submit" class="btn-primary">Save</button>
                    </div>
                </form>
            </div>
        `;
        document.body.appendChild(modal);
        modal.querySelector('#product-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('pname').value,
                category: document.getElementById('pcat').value,
                price: parseFloat(document.getElementById('pprice').value),
                quantity: parseInt(document.getElementById('pqty').value) || 0
            };
            try {
                await ApiService.createProduct(data);
                await this.loadInitialData();
                modal.remove();
                this.showApp();
            } catch (error) {
                alert(error.message);
            }
        });
    }
    
    render() {}
}

document.addEventListener('DOMContentLoaded', () => new ShopKeepApp());'''
    create_file(os.path.join(PROJECT_DIR, 'frontend', 'js', 'app.js'), app_js_content)
    
    # Create styles.css
    css_content = '''*{margin:0;padding:0;box-sizing:border-box}
:root{--primary:#BA7517;--primary-dark:#633806;--success:#27500A;--success-light:#EAF3DE;--warning:#BA7517;--warning-light:#FAEEDA;--danger:#791F1F;--danger-light:#FCEBEB;--gray-50:#fafafa;--gray-100:#f5f5f5;--gray-200:#e5e5e5;--gray-300:#d4d4d4;--gray-600:#666;--gray-900:#1e1e1e}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;font-size:14px;color:var(--gray-900);background:var(--gray-100);line-height:1.5}
.auth-container{display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.auth-box{background:#fff;border-radius:8px;padding:32px;width:100%;max-width:360px;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
.auth-box h2{margin-bottom:8px;color:var(--primary)}
.auth-box p{color:var(--gray-600);margin-bottom:24px}
.auth-box input{width:100%;padding:10px 12px;margin-bottom:16px;border:1px solid var(--gray-300);border-radius:6px;font-size:14px}
.auth-box button{width:100%;padding:10px;background:var(--primary);color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer}
.app-container{display:flex;min-height:100vh}
.sidebar{width:240px;background:#fff;border-right:1px solid var(--gray-200);display:flex;flex-direction:column}
.sidebar-header{padding:20px;border-bottom:1px solid var(--gray-200)}
.sidebar-header h3{color:var(--primary)}
.nav-menu{flex:1;list-style:none;padding:16px 0}
.nav-item{padding:10px 20px;cursor:pointer;transition:background .2s}
.nav-item:hover{background:var(--gray-100)}
.nav-item.active{background:var(--warning-light);color:var(--primary-dark);font-weight:500;border-left:3px solid var(--primary)}
.sidebar-footer{padding:16px 20px;border-top:1px solid var(--gray-200)}
.user-info{font-size:13px;color:var(--gray-600);margin-bottom:12px}
.main-content{flex:1;padding:24px;overflow-y:auto}
.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px}
.page-header h1{font-size:24px;font-weight:600}
.btn-primary{background:var(--primary);color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:14px;font-weight:500;cursor:pointer}
.btn-secondary{background:#fff;color:var(--gray-900);border:1px solid var(--gray-300);padding:8px 16px;border-radius:6px;font-size:14px;cursor:pointer}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:24px}
.stat-card{background:#fff;padding:20px;border-radius:8px;border:1px solid var(--gray-200)}
.stat-label{font-size:12px;color:var(--gray-600);margin-bottom:8px}
.stat-value{font-size:28px;font-weight:600}
.card{background:#fff;border-radius:8px;border:1px solid var(--gray-200);overflow:hidden}
.card h3{padding:16px 20px;border-bottom:1px solid var(--gray-200);font-size:16px;font-weight:600}
.modal{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;z-index:1000}
.modal-content{background:#fff;border-radius:8px;padding:24px;width:100%;max-width:480px}
.form-group{margin-bottom:16px}
.form-group label{display:block;font-size:13px;font-weight:500;margin-bottom:6px}
.form-group input{width:100%;padding:8px 12px;border:1px solid var(--gray-300);border-radius:6px;font-size:14px}
.modal-actions{display:flex;gap:12px;justify-content:flex-end;margin-top:24px}
.error-message{color:var(--danger);font-size:13px;margin-bottom:12px;min-height:20px}
.loading{display:flex;align-items:center;justify-content:center;padding:60px;color:var(--gray-600)}'''
    create_file(os.path.join(PROJECT_DIR, 'frontend', 'css', 'styles.css'), css_content)
    
    # Create run.py
    run_content = '''#!/usr/bin/env python3
import os
import sys
import webbrowser
from threading import Timer

def open_browser():
    webbrowser.open('http://localhost:5000')

def main():
    print("\\n" + "="*50)
    print("SK ShopKeep - Starting Server")
    print("="*50 + "\\n")
    
    if not os.path.exists('backend/app.py'):
        print("Error: Please run this script from the project root directory")
        sys.exit(1)
    
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    
    Timer(1.5, open_browser).start()
    
    print("Server running at: http://localhost:5000")
    print("Press Ctrl+C to stop\\n")
    
    from backend.app import create_app
    app = create_app()
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)

if __name__ == '__main__':
    main()'''
    create_file(os.path.join(PROJECT_DIR, 'run.py'), run_content)
    
    # Create README
    readme_content = '''# SK ShopKeep - Offline Inventory Management System

## Quick Start

1. Install Python dependencies: