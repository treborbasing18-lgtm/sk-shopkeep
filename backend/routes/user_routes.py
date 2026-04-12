from flask import Blueprint, jsonify 
from backend.auth.auth_service import AuthService 
 
user_bp = Blueprint('users', __name__, url_prefix='/api/users') 
 
@user_bp.route('', methods=['GET']) 
@AuthService.require_admin 
def get_users(): 
    return jsonify({'users': []}) 
