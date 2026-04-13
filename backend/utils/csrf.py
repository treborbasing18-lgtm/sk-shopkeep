"""
CSRF protection using the Synchronizer Token Pattern.
- Token is stored in the server-side session.
- Client reads it from GET /api/auth/csrf-token.
- Every state-changing request (POST/PUT/DELETE) must send it
  as the X-CSRF-Token header.
- Frontend api.js reads the token once on boot and attaches it automatically.
"""

import secrets
from functools import wraps
from flask import session, request, jsonify


CSRF_SESSION_KEY = '_csrf_token'
CSRF_HEADER      = 'X-CSRF-Token'
SAFE_METHODS     = {'GET', 'HEAD', 'OPTIONS'}


def generate_csrf_token() -> str:
    """Create a new token and store it in the session."""
    token = secrets.token_hex(32)
    session[CSRF_SESSION_KEY] = token
    return token


def get_csrf_token() -> str:
    """Return the existing token, creating one if absent."""
    if CSRF_SESSION_KEY not in session:
        return generate_csrf_token()
    return session[CSRF_SESSION_KEY]


def require_csrf(f):
    """
    Decorator that validates the CSRF token for state-changing requests.
    Safe methods (GET, HEAD, OPTIONS) are skipped.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.method in SAFE_METHODS:
            return f(*args, **kwargs)

        token      = request.headers.get(CSRF_HEADER, '')
        session_tk = session.get(CSRF_SESSION_KEY, '')

        if not token or not session_tk or not secrets.compare_digest(token, session_tk):
            return jsonify({
                'success': False,
                'error':   'CSRF token invalid or missing.'
            }), 403

        return f(*args, **kwargs)
    return decorated
