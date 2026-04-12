from flask import Blueprint, request, jsonify
from backend.models.user_model import UserModel
from backend.models.log_model import LogModel
from backend.auth.auth_service import AuthService
from backend.utils.validators import Validators

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = UserModel.authenticate(username, password)
    if user:
        AuthService.login_user(user)
        LogModel.create(user['id'], 'LOGIN', f"User logged in")
        return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
    else:
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

@auth_bp.route('/setup/status', methods=['GET'])
def check_setup_status():
    from backend.models.database import db
    result = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
    has_admin = result and result[0]['count'] > 0
    return jsonify({'needs_setup': not has_admin, 'has_users': result[0]['count'] > 0 if result else False})

@auth_bp.route('/setup', methods=['POST'])
def setup_admin():
    from backend.models.database import db
    result = db.execute_query("SELECT COUNT(*) as count FROM users WHERE role = 'admin'")
    if result and result[0]['count'] > 0:
        return jsonify({'error': 'Admin already exists. Setup completed.'}), 403
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    shop_name = data.get('shop_name', 'My Shop')
    
    valid, error = Validators.validate_username(username)
    if not valid:
        return jsonify({'error': error}), 400
    valid, error = Validators.validate_password(password)
    if not valid:
        return jsonify({'error': error}), 400
    
    try:
        user_id = UserModel.create(username, password, 'admin')
        LogModel.create(user_id, 'SETUP_COMPLETED', f'Admin account created: {username}')
        
        # Auto-login the new admin
        user = UserModel.authenticate(username, password)
        AuthService.login_user(user)
        
        return jsonify({'success': True, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role']}})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
