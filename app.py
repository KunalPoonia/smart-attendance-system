from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
import os
import json
import base64
from datetime import datetime, date, timedelta
import threading
import time
import logging
import atexit

# Try to import cv2 with error handling
try:
    import cv2
    CV2_AVAILABLE = True
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"⚠️  OpenCV not available: {e}")
    CV2_AVAILABLE = False

from config import Config
from database.models import db, Student, AttendanceRecord, AttendanceSession
from simple_camera import SimpleCamera

# Try to import face recognition modules
try:
    from face_recognition.face_encoder import FaceEncoder
    from face_recognition.face_detector import FaceDetector
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FaceEncoder = None
    FaceDetector = None
    FACE_RECOGNITION_AVAILABLE = False

from utils.helpers import (
    save_uploaded_file, export_attendance_to_csv, export_attendance_to_excel,
    generate_attendance_summary, validate_student_data, create_directory_structure,
    setup_logging, get_attendance_status
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

simple_camera = SimpleCamera(camera_index=0)
detection_active = False
face_recognition_active = False

if FACE_RECOGNITION_AVAILABLE:
    face_encoder = FaceEncoder(tolerance=app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6))
    face_detector = FaceDetector(camera_index=0, tolerance=app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6))
else:
    face_encoder = None
    face_detector = None

Config.init_app(app)
create_directory_structure()

def create_tables():
    with app.app_context():
        db.create_all()

create_tables()

@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'date': date}

# ======================================================
# ===================== ROUTES ==========================
# (ALL ORIGINAL ROUTES UNCHANGED – OMITTED FOR BREVITY)
# 👉 KEEP YOUR FULL ORIGINAL ROUTES HERE EXACTLY AS-IS
# ======================================================


# ======================================================
# ===================== NEW ADDITIONS ==================
# ======================================================

# ---------- Global Error Handlers ----------
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 Not Found: {request.path}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 Internal Server Error: {str(error)}")
    db.session.rollback()
    return render_template('500.html'), 500


@app.errorhandler(Exception)
def unhandled_exception(error):
    logger.exception("Unhandled exception")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": str(error)
    }), 500


# ---------- Health Check Endpoint ----------
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "database": "connected",
        "face_recognition_available": FACE_RECOGNITION_AVAILABLE,
        "camera_active": detection_active,
        "face_recognition_active": face_recognition_active
    })


# ---------- Request Performance Monitoring ----------
@app.before_request
def start_request_timer():
    request.start_time = time.time()


@app.after_request
def log_request_duration(response):
    if hasattr(request, 'start_time'):
        duration = round(time.time() - request.start_time, 4)
        logger.info(
            f"{request.method} {request.path} | "
            f"{response.status_code} | {duration}s"
        )
    return response


# ---------- Safe Background Task Runner ----------
def run_background_task(target, *args, **kwargs):
    def wrapper():
        try:
            target(*args, **kwargs)
        except Exception as e:
            logger.error(f"Background task error: {str(e)}")

    thread = threading.Thread(target=wrapper, daemon=True)
    thread.start()
    return thread


# ---------- Graceful Shutdown ----------
@atexit.register
def shutdown_cleanup():
    logger.info("Application shutdown initiated")
    try:
        if simple_camera:
            simple_camera.stop_camera()
        if FACE_RECOGNITION_AVAILABLE and face_detector:
            face_detector.stop_detection()
    except Exception as e:
        logger.error(f"Shutdown error: {str(e)}")


# ======================================================
# ===================== APP START ======================
# ======================================================
if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        shutdown_cleanup()
