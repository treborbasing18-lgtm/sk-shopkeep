from flask import Blueprint, request, jsonify
from models.product_model import ProductModel
from models.log_model import LogModel
from auth.auth_service import AuthService

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
    try:
        product_id = ProductModel.create(data)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'CREATE_PRODUCT', f"Created: {data['name']}")
        return jsonify({'success': True, 'product_id': product_id}), 201
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
        LogModel.create(user['id'], 'DELETE_PRODUCT', f"Deleted: {product['name']}")
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
