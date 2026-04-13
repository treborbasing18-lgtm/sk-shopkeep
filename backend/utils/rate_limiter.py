"""
Simple in-memory rate limiter.
No external dependencies — uses a dict of (ip, action) → list of timestamps.
Automatically cleans up old entries to prevent memory leaks.
"""

import time
from threading import Lock
from flask import request, jsonify
from functools import wraps

_store: dict = {}
_lock  = Lock()


def _get_ip() -> str:
    """Respect X-Forwarded-For from Render's proxy."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


def _prune(timestamps: list, window: int) -> list:
    """Keep only timestamps within the current window."""
    cutoff = time.time() - window
    return [t for t in timestamps if t > cutoff]


def rate_limit(max_requests: int, window_seconds: int, scope: str = ''):
    """
    Decorator factory.

    @rate_limit(5, 60)          — 5 requests per 60 s per IP
    @rate_limit(3, 300, 'login') — 3 login attempts per 5 min per IP
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            ip  = _get_ip()
            key = f"{scope or f.__name__}:{ip}"

            with _lock:
                timestamps = _prune(_store.get(key, []), window_seconds)
                if len(timestamps) >= max_requests:
                    retry_after = int(window_seconds - (time.time() - timestamps[0]))
                    return jsonify({
                        'success': False,
                        'error': f'Too many requests. Try again in {retry_after}s.'
                    }), 429
                timestamps.append(time.time())
                _store[key] = timestamps

            return f(*args, **kwargs)
        return wrapped
    return decorator


def cleanup_old_entries():
    """Call periodically to free memory (optional — entries are pruned on access)."""
    cutoff = time.time() - 3600
    with _lock:
        stale = [k for k, v in _store.items() if all(t < cutoff for t in v)]
        for k in stale:
            del _store[k]
