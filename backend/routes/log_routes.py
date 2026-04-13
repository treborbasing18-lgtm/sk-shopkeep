from flask import Blueprint, jsonify, request
from backend.auth.auth_service import AuthService
from backend.models.database import db

log_bp = Blueprint('logs', __name__, url_prefix='/api/logs')


@log_bp.route('', methods=['GET'])
@AuthService.require_admin
def get_logs():
    try:
        page     = max(1, request.args.get('page', 1, type=int))
        per_page = min(100, max(1, request.args.get('per_page', 50, type=int)))
        offset   = (page - 1) * per_page

        action    = request.args.get('action', '').strip().upper()
        user_id   = request.args.get('user_id', '').strip()
        date_from = request.args.get('date_from', '').strip()   # YYYY-MM-DD
        date_to   = request.args.get('date_to', '').strip()     # YYYY-MM-DD

        filters = []
        params  = []

        if action:
            filters.append("l.action = ?")
            params.append(action)
        if user_id:
            filters.append("l.user_id = ?")
            params.append(user_id)
        if date_from:
            filters.append("DATE(l.timestamp) >= ?")
            params.append(date_from)
        if date_to:
            filters.append("DATE(l.timestamp) <= ?")
            params.append(date_to)

        where = ("WHERE " + " AND ".join(filters)) if filters else ""

        count_row = db.execute_query(
            f"SELECT COUNT(*) as total FROM logs l {where}", params
        )
        total = count_row[0]['total'] if count_row else 0

        rows = db.execute_query(
            f"""
            SELECT l.id, l.action, l.details, l.timestamp, u.username
            FROM logs l
            LEFT JOIN users u ON l.user_id = u.id
            {where}
            ORDER BY l.timestamp DESC
            LIMIT ? OFFSET ?
            """,
            params + [per_page, offset]
        )

        return jsonify({
            'logs': [dict(r) for r in rows],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': max(1, -(-total // per_page))   # ceiling division
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
