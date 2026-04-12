import uuid
from models.database import db
from models.product_model import ProductModel

class SalesModel:

    @staticmethod
    def create(product_id, quantity, user_id):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        product = ProductModel.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")
        if quantity > product['quantity']:
            raise ValueError(f"Only {product['quantity']} available")
        total = quantity * product['price']
        sale_id = str(uuid.uuid4())
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE products SET quantity = quantity - ? WHERE id = ?",
                (quantity, product_id)
            )
            cursor.execute(
                """INSERT INTO sales (id, product_id, quantity, unit_price, total, user_id, timestamp)
VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
                (sale_id, product_id, quantity, product['price'], total, user_id)
            )
        return {'id': sale_id, 'product_name': product['name'], 'quantity': quantity, 'total': total}

    @staticmethod
    def get_all(limit=None):
        query = """
SELECT s.id, s.quantity, s.total, s.timestamp, p.name as product_name
FROM sales s
JOIN products p ON s.product_id = p.id
ORDER BY s.timestamp DESC
"""
        if limit:
            query += f" LIMIT {int(limit)}"
        result = db.execute_query(query)
        return [dict(row) for row in result]

    @staticmethod
    def get_total_revenue():
        result = db.execute_query("SELECT COALESCE(SUM(total), 0) as total FROM sales")
        return result[0]['total'] if result else 0
