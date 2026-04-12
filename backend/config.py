import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'shopkeep_'
    SESSION_COOKIE_NAME = 'shopkeep_session'
    
    # Use /tmp for database on Render
    if os.environ.get('RENDER'):
        DATABASE_PATH = '/tmp/shopkeep.db'
        BACKUP_PATH = '/tmp/backups'
    else:
        DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'shopkeep.db')
        BACKUP_PATH = os.path.join(os.path.dirname(__file__), '..', 'backups')
    
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000', 'http://localhost:8000', 'https://*.onrender.com']
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'