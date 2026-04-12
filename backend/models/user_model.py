import uuid
import bcrypt
from models.database import db

class UserModel:

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    @staticmethod
    def verify_password(password, password_hash):
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    @staticmethod
    def create(username, password, role='staff'):
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters")
        existing = db.execute_query("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            raise ValueError("Username already exists")
        user_id = str(uuid.uuid4())
        password_hash = UserModel.hash_password(password)
        db.execute_insert(
            """INSERT INTO users (id, username, password_hash, role, created_at)
VALUES (?, ?, ?, ?, datetime('now'))""",
            (user_id, username, password_hash, role)
        )
        return user_id

    @staticmethod
    def authenticate(username, password):
        if not username or not password:
            return None
        result = db.execute_query(
            "SELECT id, username, password_hash, role FROM users WHERE username = ?",
            (username,)
        )
        if not result:
            return None
        user = dict(result[0])
        if UserModel.verify_password(password, user['password_hash']):
            del user['password_hash']
            return user
        return None

    @staticmethod
    def get_all():
        result = db.execute_query(
            "SELECT id, username, role, created_at FROM users ORDER BY created_at DESC"
        )
        return [dict(row) for row in result]

    @staticmethod
    def delete(user_id):
        return db.execute_update("DELETE FROM users WHERE id = ?", (user_id,))

    @staticmethod
    def get_by_id(user_id):
        result = db.execute_query(
            "SELECT id, username, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        return dict(result[0]) if result else None
