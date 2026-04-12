from flask import Blueprint, request, jsonify
from models.sales_model import SalesModel
from models.log_model import LogModel
from auth.auth_service import AuthService

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
    try:
        user = AuthService.get_current_user()
        sale = SalesModel.create(data['product_id'], data['quantity'], user['id'])
        LogModel.create(user['id'], 'SALE', f"Sold {sale['quantity']}x {sale['product_name']}")
        return jsonify({'success': True, 'sale': sale}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@sales_bp.route('/stats', methods=['GET'])
@AuthService.require_auth
def get_sales_stats():
    total_revenue = SalesModel.get_total_revenue()
    return jsonify({'total_revenue': total_revenue})
