import uuid
from backend.models.database import db


class ProductModel:

    @staticmethod
    def validate(data):
        if not data.get('name') or len(data['name'].strip()) == 0:
            return False, "Product name is required"
        if not data.get('category') or len(data['category'].strip()) == 0:
            return False, "Category is required"
        price = data.get('price')
        if price is None or float(price) < 0:
            return False, "Price must be non-negative"
        return True, None

    @staticmethod
    def create(data):
        valid, error = ProductModel.validate(data)
        if not valid:
            raise ValueError(error)
        existing = db.execute_query(
            "SELECT id FROM products WHERE LOWER(name) = LOWER(?)",
            (data['name'].strip(),)
        )
        if existing:
            raise ValueError("Product name already exists")
        product_id = str(uuid.uuid4())
        db.execute_insert(
            """INSERT INTO products (id, name, category, price, quantity, reorder_threshold)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                product_id,
                data['name'].strip(),
                data['category'].strip(),
                float(data['price']),
                int(data.get('quantity', 0)),
                int(data.get('reorder_threshold', 10))
            )
        )
        return product_id

    @staticmethod
    def update(product_id, data):
        """Partial update — only touches fields present in data. id is immutable."""
        product = ProductModel.get_by_id(product_id)
        if not product:
            raise ValueError("Product not found")

        # Check name uniqueness only if name is being changed
        new_name = data.get('name', product['name']).strip()
        if new_name.lower() != product['name'].lower():
            clash = db.execute_query(
                "SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND id != ?",
                (new_name, product_id)
            )
            if clash:
                raise ValueError("Product name already exists")

        db.execute_update(
            """UPDATE products
               SET name              = ?,
                   category          = ?,
                   price             = ?,
                   quantity          = ?,
                   reorder_threshold = ?
               WHERE id = ?""",
            (
                new_name,
                data.get('category', product['category']).strip(),
                float(data.get('price', product['price'])),
                int(data.get('quantity', product['quantity'])),
                int(data.get('reorder_threshold', product['reorder_threshold'])),
                product_id
            )
        )
        return ProductModel.get_by_id(product_id)

    @staticmethod
    def get_all():
        result = db.execute_query(
            "SELECT id, name, category, price, quantity, reorder_threshold FROM products ORDER BY name"
        )
        return [dict(row) for row in result]

    @staticmethod
    def get_by_id(product_id):
        result = db.execute_query(
            "SELECT id, name, category, price, quantity, reorder_threshold FROM products WHERE id = ?",
            (product_id,)
        )
        return dict(result[0]) if result else None

    @staticmethod
    def delete(product_id):
        rows = db.execute_update("DELETE FROM products WHERE id = ?", (product_id,))
        if rows == 0:
            raise ValueError("Product not found")
        return True
