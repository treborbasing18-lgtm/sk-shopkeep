from flask import Blueprint, jsonify 
from backend.auth.auth_service import AuthService 
 
log_bp = Blueprint('logs', __name__, url_prefix='/api/logs') 
 
@log_bp.route('', methods=['GET']) 
@AuthService.require_admin 
def get_logs(): 
    return jsonify({'logs': []}) 
