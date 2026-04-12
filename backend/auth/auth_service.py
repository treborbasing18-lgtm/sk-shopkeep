from functools import wraps
from flask import session, jsonify

class AuthService:

    @staticmethod
    def login_user(user):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session.permanent = True

    @staticmethod
    def logout_user():
        session.clear()

    @staticmethod
    def get_current_user():
        if 'user_id' not in session:
            return None
        return {
            'id': session['user_id'],
            'username': session['username'],
            'role': session['role']
        }

    @staticmethod
    def is_authenticated():
        return 'user_id' in session

    @staticmethod
    def is_admin():
        return session.get('role') == 'admin'

    @staticmethod
    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AuthService.is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated

    @staticmethod
    def require_admin(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not AuthService.is_authenticated():
                return jsonify({'error': 'Authentication required'}), 401
            if not AuthService.is_admin():
                return jsonify({'error': 'Admin privileges required'}), 403
            return f(*args, **kwargs)
        return decorated
