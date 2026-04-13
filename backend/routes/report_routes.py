from flask import Blueprint, jsonify, request
from backend.auth.auth_service import AuthService
from backend.models.database import db

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')


@report_bp.route('/summary', methods=['GET'])
@AuthService.require_auth
def get_summary():
    """High-level dashboard numbers."""
    try:
        revenue_row = db.execute_query(
            "SELECT COALESCE(SUM(total), 0) AS total_revenue, COUNT(*) AS total_transactions FROM sales"
        )
        product_row = db.execute_query(
            "SELECT COUNT(*) AS total_products, COALESCE(SUM(quantity), 0) AS total_stock FROM products"
        )
        low_stock_row = db.execute_query(
            "SELECT COUNT(*) AS low_stock FROM products WHERE quantity <= reorder_threshold"
        )

        return jsonify({
            'total_revenue':       revenue_row[0]['total_revenue'],
            'total_transactions':  revenue_row[0]['total_transactions'],
            'total_products':      product_row[0]['total_products'],
            'total_stock':         product_row[0]['total_stock'],
            'low_stock_count':     low_stock_row[0]['low_stock'],
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@report_bp.route('/sales-summary', methods=['GET'])
@AuthService.require_auth
def get_sales_summary():
    """Daily sales totals for a date range (default: last 30 days)."""
    try:
        date_from = request.args.get('date_from', '')
        date_to   = request.args.get('date_to', '')

        if not date_from:
            date_from = "date('now', '-30 days')"
            from_param = None
        else:
            from_param = date_from

        if not date_to:
            date_to = "date('now')"
            to_param = None
        else:
            to_param = date_to

        if from_param and to_param:
            rows = db.execute_query(
                """
                SELECT DATE(timestamp) AS day,
                       COUNT(*)        AS transactions,
                       SUM(total)      AS revenue
                FROM sales
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY day
                ORDER BY day ASC
                """,
                (from_param, to_param)
            )
        else:
            rows = db.execute_query(
                f"""
                SELECT DATE(timestamp) AS day,
                       COUNT(*)        AS transactions,
                       SUM(total)      AS revenue
                FROM sales
                WHERE DATE(timestamp) BETWEEN {date_from} AND {date_to}
                GROUP BY day
                ORDER BY day ASC
                """
            )

        return jsonify({'sales_summary': [dict(r) for r in rows]})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@report_bp.route('/inventory-value', methods=['GET'])
@AuthService.require_auth
def get_inventory_value():
    """Current inventory value grouped by category."""
    try:
        rows = db.execute_query(
            """
            SELECT category,
                   COUNT(*)                        AS product_count,
                   SUM(quantity)                   AS total_units,
                   SUM(quantity * price)           AS total_value,
                   SUM(CASE WHEN quantity <= reorder_threshold THEN 1 ELSE 0 END) AS low_stock_count
            FROM products
            GROUP BY category
            ORDER BY total_value DESC
            """
        )
        total_row = db.execute_query(
            "SELECT COALESCE(SUM(quantity * price), 0) AS grand_total FROM products"
        )
        return jsonify({
            'by_category':   [dict(r) for r in rows],
            'grand_total':   total_row[0]['grand_total']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@report_bp.route('/top-products', methods=['GET'])
@AuthService.require_auth
def get_top_products():
    """Best-selling products by revenue and units sold."""
    try:
        limit = min(50, max(1, request.args.get('limit', 10, type=int)))
        rows = db.execute_query(
            """
            SELECT p.name,
                   p.category,
                   p.price,
                   p.quantity               AS stock_remaining,
                   COALESCE(SUM(s.quantity), 0)    AS units_sold,
                   COALESCE(SUM(s.total),    0)    AS revenue
            FROM products p
            LEFT JOIN sales s ON p.id = s.product_id
            GROUP BY p.id
            ORDER BY revenue DESC
            LIMIT ?
            """,
            (limit,)
        )
        return jsonify({'top_products': [dict(r) for r in rows]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
