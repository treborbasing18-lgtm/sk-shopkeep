import uuid
from backend.models.database import db

class LogModel:

    @staticmethod
    def create(user_id, action, details):
        log_id = str(uuid.uuid4())
        db.execute_insert(
            """INSERT INTO logs (id, user_id, action, details, timestamp)
VALUES (?, ?, ?, ?, datetime('now'))""",
            (log_id, user_id, action, details)
        )

    @staticmethod
    def get_all(limit=100):
        result = db.execute_query(
            """SELECT l.*, u.username
FROM logs l
LEFT JOIN users u ON l.user_id = u.id
ORDER BY l.timestamp DESC
LIMIT ?""",
            (limit,)
        )
        return [dict(row) for row in result]
