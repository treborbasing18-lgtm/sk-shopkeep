from flask import Blueprint, request, jsonify
from backend.models.user_model import UserModel
from backend.models.log_model import LogModel
from backend.auth.auth_service import AuthService
from backend.utils.validators import Validators

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
