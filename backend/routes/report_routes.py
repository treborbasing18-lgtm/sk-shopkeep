from flask import Blueprint, jsonify 
from auth.auth_service import AuthService 
 
report_bp = Blueprint('reports', __name__, url_prefix='/api/reports') 
 
@report_bp.route('/summary', methods=['GET']) 
@AuthService.require_auth 
def get_summary(): 
    return jsonify({'total_revenue': 0}) 
