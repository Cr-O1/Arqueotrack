import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-replit-fll-2026')

    # SQLite para Replit
    SQLALCHEMY_DATABASE_URI = 'sqlite:///arqueotrack.db'

    # Alternativa: Si la base de datos debe ser temporal
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///arqueotrack.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # Uploads - Usar ruta absoluta para Replit
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ITEMS_PER_PAGE = 20
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Configuración de seguridad para Replit
    SESSION_COOKIE_SECURE = False  # Replit usa HTTPS por defecto
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Debug activado para desarrollo
    DEBUG = True
    TESTING = False

def get_config(config_name=None):
    return Config