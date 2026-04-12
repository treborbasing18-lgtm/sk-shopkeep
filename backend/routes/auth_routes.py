from flask import Blueprint, request, jsonify
from models.user_model import UserModel
from models.log_model import LogModel
from auth.auth_service import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = UserModel.authenticate(username, password)
    if user:
        AuthService.login_user(user)
        LogModel.create(user['id'], 'LOGIN', 'User logged in')
        return jsonify({'success': True, 'user': user})
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
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
    username = data.get('username', '').strip()
    password = data.get('password', '')
    try:
        user_id = UserModel.create(username, password, 'admin')
        user = UserModel.authenticate(username, password)
        AuthService.login_user(user)
        return jsonify({'success': True, 'user': user})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@auth_bp.route('/check-first-run', methods=['GET'])
def check_first_run():
    from models.database import db
    result = db.execute_query("SELECT COUNT(*) as count FROM users")
    has_users = result and result[0]['count'] > 0
    return jsonify({'needs_setup': not has_users})
