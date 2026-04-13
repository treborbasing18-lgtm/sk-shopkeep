from flask import Blueprint, request, jsonify
from backend.models.product_model import ProductModel
from backend.models.log_model import LogModel
from backend.auth.auth_service import AuthService
from backend.utils.validators import Validators

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
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    valid, error = Validators.validate_price(data.get('price'))
    if not valid:
        return jsonify({'success': False, 'error': error}), 400

    qty = data.get('quantity', 0)
    valid, error = Validators.validate_quantity(qty)
    if not valid:
        return jsonify({'success': False, 'error': error}), 400

    try:
        product_id = ProductModel.create(data)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'CREATE_PRODUCT', f"Created: {data['name']}")
        return jsonify({'success': True, 'product_id': product_id}), 201
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@product_bp.route('/<product_id>', methods=['GET'])
@AuthService.require_auth
def get_product(product_id):
    product = ProductModel.get_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    return jsonify({'product': product})


@product_bp.route('/<product_id>', methods=['PUT'])
@AuthService.require_auth
def update_product(product_id):
    """Edit a product. id and created_at are immutable."""
    product = ProductModel.get_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400

    # Validate any updated fields
    if 'price' in data:
        valid, error = Validators.validate_price(data['price'])
        if not valid:
            return jsonify({'success': False, 'error': error}), 400

    if 'quantity' in data:
        valid, error = Validators.validate_quantity(data['quantity'])
        if not valid:
            return jsonify({'success': False, 'error': error}), 400

    if 'reorder_threshold' in data:
        valid, error = Validators.validate_quantity(data['reorder_threshold'])
        if not valid:
            return jsonify({'success': False, 'error': 'Invalid reorder threshold'}), 400

    try:
        updated = ProductModel.update(product_id, data)
        user = AuthService.get_current_user()

        # Build a readable diff for the log
        changes = []
        for field in ('name', 'category', 'price', 'quantity', 'reorder_threshold'):
            if field in data and str(data[field]) != str(product[field]):
                changes.append(f"{field}: {product[field]} → {data[field]}")
        detail = f"Edited {product['name']}: " + (", ".join(changes) if changes else "no changes")
        LogModel.create(user['id'], 'EDIT_PRODUCT', detail)

        return jsonify({'success': True, 'product': updated})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@product_bp.route('/<product_id>', methods=['DELETE'])
@AuthService.require_admin
def delete_product(product_id):
    product = ProductModel.get_by_id(product_id)
    if not product:
        return jsonify({'success': False, 'error': 'Product not found'}), 404
    try:
        ProductModel.delete(product_id)
        user = AuthService.get_current_user()
        LogModel.create(user['id'], 'DELETE_PRODUCT', f"Deleted: {product['name']}")
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
