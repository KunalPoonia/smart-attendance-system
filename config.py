import os
import secrets
from datetime import timedelta


def get_secret_key():
    """
    Get secret key from environment or generate a secure one.
    In production, SECRET_KEY environment variable MUST be set.
    """
    secret_key = os.environ.get('SECRET_KEY')
    
    if secret_key:
        return secret_key
    
    # Check if running in production
    flask_env = os.environ.get('FLASK_ENV', 'development')
    if flask_env == 'production':
        raise ValueError(
            "SECRET_KEY environment variable must be set in production! "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    
    # Development: generate a random key (will change on restart)
    print("⚠️  WARNING: Using auto-generated SECRET_KEY. Set SECRET_KEY env var for persistence.")
    return secrets.token_hex(32)


class Config:
    # Flask Configuration
    SECRET_KEY = get_secret_key()
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Configuration
    UPLOAD_FOLDER = 'static/uploads'
    STUDENT_IMAGES_FOLDER = 'student_images'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Face Recognition Configuration
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_DETECTION_MODEL = 'hog'  # 'hog' or 'cnn'
    
    # Attendance Configuration
    ATTENDANCE_TIME_WINDOW = timedelta(hours=1)  # Prevent duplicate attendance within 1 hour
    
    # Camera Configuration
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    
    # Export Configuration
    EXPORT_FOLDER = 'exports'
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_DEFAULT = '200 per day, 50 per hour'
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.STUDENT_IMAGES_FOLDER, exist_ok=True)
        os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
        os.makedirs('database', exist_ok=True)