import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
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
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.STUDENT_IMAGES_FOLDER, exist_ok=True)
        os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
        os.makedirs('database', exist_ok=True)