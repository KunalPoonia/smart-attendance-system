from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_swagger_ui import get_swaggerui_blueprint
import os
import json
import base64
from datetime import datetime, date, timedelta
import threading
import time
import logging

# Try to import cv2 with error handling
try:
    import cv2
    CV2_AVAILABLE = True
    print("✅ OpenCV imported successfully")
except ImportError as e:
    print(f"⚠️  OpenCV not available: {e}")
    CV2_AVAILABLE = False

# Import custom modules
from config import Config
from src.database.models import db, Student, AttendanceRecord, AttendanceSession, LeaveRequest
from src.core.simple_camera import SimpleCamera

# Try to import face recognition modules (graceful fallback if not available)
try:
    from src.face_recognition.face_encoder import FaceEncoder
    from src.face_recognition.face_detector import FaceDetector
    FACE_RECOGNITION_AVAILABLE = True
    print("✅ Face recognition modules imported successfully")
except ImportError as e:
    print(f"⚠️  Face recognition not available: {str(e)}")
    FaceEncoder = None
    FaceDetector = None
    FACE_RECOGNITION_AVAILABLE = False
from src.utils.helpers import (
    save_uploaded_file, export_attendance_to_csv, export_attendance_to_excel,
    generate_attendance_summary, validate_student_data, create_directory_structure,
    setup_logging, get_attendance_status
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Swagger UI Configuration
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Smart Attendance System API",
        'layout': "BaseLayout",
        'deepLinking': True
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Initialize components
simple_camera = SimpleCamera(camera_index=0)
detection_active = False
face_recognition_active = False

# Initialize face recognition components if available
if FACE_RECOGNITION_AVAILABLE:
    face_encoder = FaceEncoder(tolerance=app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6))
    face_detector = FaceDetector(camera_index=0, tolerance=app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6))
else:
    face_encoder = None
    face_detector = None

# Create directory structure
Config.init_app(app)
create_directory_structure()

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created")

# Initialize database tables
create_tables()

# Add datetime to template context
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'date': date}

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    try:
        # Get statistics
        total_students = Student.query.filter_by(is_active=True).count()
        today = date.today()
        today_attendance = AttendanceRecord.query.filter_by(date=today).count()
        
        # Get recent attendance records
        recent_records = AttendanceRecord.query.order_by(
            AttendanceRecord.created_at.desc()
        ).limit(10).all()
        
        # Use modern clean template
        return render_template('index_clean.html', 
                             total_students=total_students,
                             today_attendance=today_attendance,
                             recent_records=recent_records,
                             datetime=datetime)
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        flash('Error loading dashboard', 'error')
        return render_template('index_clean.html', 
                             total_students=0,
                             today_attendance=0,
                             recent_records=[],
                             datetime=datetime)

@app.route('/students')
def students():
    """Student management page"""
    try:
        students = Student.query.filter_by(is_active=True).all()
        return render_template('students_clean.html', students=students)
    except Exception as e:
        logger.error(f"Error in students route: {str(e)}")
        flash('Error loading students', 'error')
        return render_template('students_clean.html', students=[])

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    """Register new student"""
    if request.method == 'GET':
        return render_template('register_student_clean.html')
    
    try:
        # Get form data
        data = {
            'student_id': request.form.get('student_id'),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'department': request.form.get('department'),
            'year': request.form.get('year'),
            'section': request.form.get('section')
        }
        
        # Validate data
        errors = validate_student_data(data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register_student_clean.html', data=data)
        
        # Check if student already exists
        existing_student = Student.query.filter_by(student_id=data['student_id']).first()
        if existing_student:
            flash('Student ID already exists', 'error')
            return render_template('register_student_clean.html', data=data)
        
        # Handle image - either from file upload or camera capture
        image_path = None
        captured_image = request.form.get('captured_image')
        
        if captured_image and captured_image.startswith('data:image'):
            # Handle camera captured image (base64)
            try:
                # Extract base64 data
                header, encoded = captured_image.split(',', 1)
                image_data = base64.b64decode(encoded)
                
                # Save to file
                filename = f"student_{data['student_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
                image_path = os.path.join(app.config['STUDENT_IMAGES_FOLDER'], filename)
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
            except Exception as e:
                logger.error(f"Error saving captured image: {str(e)}")
                flash('Error saving captured image', 'error')
                return render_template('register_student_clean.html', data=data)
        elif 'image' in request.files and request.files['image'].filename != '':
            # Handle file upload
            file = request.files['image']
            image_path = save_uploaded_file(
                file, 
                app.config['STUDENT_IMAGES_FOLDER'],
                f"student_{data['student_id']}_"
            )
        
        if not image_path:
            flash('Student photo is required (upload or capture)', 'error')
            return render_template('register_student_clean.html', data=data)
        
        # Extract face encoding (if face recognition is available)
        face_encoding = None
        if FACE_RECOGNITION_AVAILABLE and face_encoder:
            face_encoding = face_encoder.encode_face_from_image(image_path)
            if face_encoding is None:
                flash('No face detected in the image. Please upload a clear photo with a visible face.', 'warning')
                # Don't remove the image, just proceed without face encoding
            else:
                flash('Face encoding created successfully!', 'success')
        
        # Create new student
        student = Student(
            student_id=data['student_id'],
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            department=data['department'],
            year=data['year'],
            section=data['section'],
            image_path=image_path
        )
        
        if face_encoding is not None:
            student.set_face_encoding(face_encoding)
        
        db.session.add(student)
        db.session.commit()
        
        flash('Student registered successfully!', 'success')
        logger.info(f"Student registered: {data['student_id']} - {data['name']}")
        return redirect(url_for('students'))
        
    except Exception as e:
        logger.error(f"Error registering student: {str(e)}")
        flash('Error registering student', 'error')
        return render_template('register_student_clean.html')

@app.route('/attendance')
def attendance():
    """Attendance management page"""
    try:
        # Get filter parameters
        date_filter = request.args.get('date', date.today().isoformat())
        department_filter = request.args.get('department', '')
        year_filter = request.args.get('year', '')
        
        # Build query
        query = AttendanceRecord.query
        
        if date_filter:
            query = query.filter(AttendanceRecord.date == date_filter)
        
        if department_filter:
            query = query.join(Student).filter(Student.department == department_filter)
        
        if year_filter:
            query = query.join(Student).filter(Student.year == year_filter)
        
        records = query.order_by(AttendanceRecord.created_at.desc()).all()
        
        # Get unique departments and years for filters
        departments = db.session.query(Student.department).distinct().all()
        years = db.session.query(Student.year).distinct().all()
        
        return render_template('attendance_clean.html', 
                             records=records,
                             departments=[d[0] for d in departments if d[0]],
                             years=[y[0] for y in years if y[0]],
                             current_date=date_filter,
                             current_department=department_filter,
                             current_year=year_filter)
    except Exception as e:
        logger.error(f"Error in attendance route: {str(e)}")
        flash('Error loading attendance records', 'error')
        return render_template('attendance_clean.html', records=[])

@app.route('/mark_attendance')
def mark_attendance():
    """Face recognition attendance marking page"""
    return render_template('mark_attendance_clean.html')

@app.route('/start_detection', methods=['POST'])
def start_detection():
    """Start camera detection"""
    global simple_camera, detection_active
    
    try:
        if detection_active:
            return jsonify({'success': False, 'message': 'Camera already active'})
        
        # Start simple camera
        if simple_camera.start_camera():
            detection_active = True
            logger.info("Camera started successfully")
            return jsonify({'success': True, 'message': 'Camera started successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start camera. Please check if camera is available.'})
            
    except Exception as e:
        logger.error(f"Error starting camera: {str(e)}")
        return jsonify({'success': False, 'message': f'Camera error: {str(e)}'})

@app.route('/start_face_recognition', methods=['POST'])
def start_face_recognition():
    """Start face recognition detection"""
    global face_detector, face_recognition_active
    
    try:
        if not FACE_RECOGNITION_AVAILABLE:
            return jsonify({'success': False, 'message': 'Face recognition libraries not installed. Please run setup_face_recognition.py'})
        
        if face_recognition_active:
            return jsonify({'success': False, 'message': 'Face recognition already active'})
        
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face detector not initialized'})
        
        # Load known faces from database
        students = Student.query.filter_by(is_active=True).all()
        students_data = []
        
        for student in students:
            face_encoding = student.get_face_encoding()
            # Check if face_encoding exists and has data
            if face_encoding is not None and (hasattr(face_encoding, '__len__') and len(face_encoding) > 0):
                students_data.append({
                    'id': student.id,
                    'name': student.name,
                    'student_id': student.student_id,
                    'face_encoding': face_encoding
                })
        
        if not students_data:
            return jsonify({'success': False, 'message': 'No students with face encodings found. Please register students with photos first.'})
        
        # Load known faces into detector
        face_detector.load_known_faces(students_data)
        
        # Start face detection
        if face_detector.start_detection():
            face_recognition_active = True
            logger.info(f"Face recognition started with {len(students_data)} known faces")
            return jsonify({'success': True, 'message': f'Face recognition started with {len(students_data)} known faces'})
        else:
            return jsonify({'success': False, 'message': 'Failed to start face recognition'})
            
    except Exception as e:
        logger.error(f"Error starting face recognition: {str(e)}")
        return jsonify({'success': False, 'message': f'Face recognition error: {str(e)}'})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    """Stop camera detection"""
    global simple_camera, detection_active
    
    try:
        if simple_camera:
            simple_camera.stop_camera()
        
        detection_active = False
        logger.info("Camera stopped")
        return jsonify({'success': True, 'message': 'Camera stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping camera: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/stop_face_recognition', methods=['POST'])
def stop_face_recognition():
    """Stop face recognition detection"""
    global face_detector, face_recognition_active
    
    try:
        if FACE_RECOGNITION_AVAILABLE and face_detector:
            face_detector.stop_detection()
        
        face_recognition_active = False
        logger.info("Face recognition stopped")
        return jsonify({'success': True, 'message': 'Face recognition stopped'})
        
    except Exception as e:
        logger.error(f"Error stopping face recognition: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_video_feed')
def get_video_feed():
    """Get video feed from camera"""
    def generate_frames():
        global simple_camera, face_detector, detection_active, face_recognition_active
        
        while (detection_active or face_recognition_active):
            try:
                frame = None
                
                # Use face recognition feed if active
                if face_recognition_active and FACE_RECOGNITION_AVAILABLE and face_detector:
                    frame = face_detector.get_current_frame_with_annotations()
                
                # Fallback to simple camera
                if frame is None and detection_active and simple_camera and simple_camera.is_camera_running():
                    frame = simple_camera.get_frame_with_overlay()
                
                if frame is not None:
                    # Encode frame as JPEG
                    ret, buffer = cv2.imencode('.jpg', frame)
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                logger.error(f"Error in video feed: {str(e)}")
                break
    
    from flask import Response
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_detected_faces')
def get_detected_faces():
    """Get currently detected faces"""
    try:
        global face_detector, face_recognition_active
        
        if face_recognition_active and FACE_RECOGNITION_AVAILABLE and face_detector:
            detected_faces = face_detector.get_detected_faces()
            
            # Format faces for frontend
            faces_data = []
            for face in detected_faces:
                faces_data.append({
                    'student_id': face['student_id'],
                    'name': face['name'],
                    'confidence': round(float(face['confidence']), 2),
                    'location': [int(x) for x in face['location']],
                    'timestamp': face['timestamp'].isoformat()
                })
            
            return jsonify({'faces': faces_data})
        else:
            return jsonify({'faces': []})
        
    except Exception as e:
        logger.error(f"Error getting detected faces: {str(e)}")
        return jsonify({'faces': []})

@app.route('/mark_manual_attendance', methods=['POST'])
def mark_manual_attendance():
    """Mark attendance manually using student ID"""
    try:
        student_id = request.form.get('student_id')
        
        if not student_id:
            flash('Student ID is required', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Get student by student_id (not database ID)
        student = Student.query.filter_by(student_id=student_id, is_active=True).first()
        if not student:
            flash(f'Student with ID {student_id} not found', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Check if already marked present today
        today = date.today()
        existing_record = AttendanceRecord.query.filter_by(
            student_id=student.id,  # Use database ID for the record
            date=today
        ).first()
        
        if existing_record:
            flash(f'{student.name} already marked present today', 'warning')
            return redirect(url_for('mark_attendance'))
        
        # Create attendance record
        now = datetime.now()
        # For manual attendance marking, always mark as Present
        status = 'Present'
        
        attendance_record = AttendanceRecord(
            student_id=student.id,  # Use database ID
            date=today,
            time_in=now,
            status=status,
            confidence_score=1.0  # Manual entry gets 100% confidence
        )
        
        db.session.add(attendance_record)
        db.session.commit()
        
        logger.info(f"Manual attendance marked: {student.name} ({student.student_id}) - {status}")
        flash(f'{student.name} marked {status.lower()} at {now.strftime("%H:%M:%S")}', 'success')
        
        return redirect(url_for('mark_attendance'))
        
    except Exception as e:
        logger.error(f"Error marking manual attendance: {str(e)}")
        flash('Error marking attendance', 'error')
        return redirect(url_for('mark_attendance'))

@app.route('/mark_student_present', methods=['POST'])
def mark_student_present():
    """Mark detected student as present"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        confidence = data.get('confidence', 0)
        
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID required'})
        
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Check if already marked present today
        today = date.today()
        existing_record = AttendanceRecord.query.filter_by(
            student_id=student_id,
            date=today
        ).first()
        
        if existing_record:
            return jsonify({
                'success': False, 
                'message': f'{student.name} already marked present today'
            })
        
        # Create attendance record
        now = datetime.now()
        # When manually marking a student present, always mark as Present
        status = 'Present'
        
        attendance_record = AttendanceRecord(
            student_id=student_id,
            date=today,
            time_in=now,
            status=status,
            confidence_score=confidence
        )
        
        db.session.add(attendance_record)
        db.session.commit()
        
        logger.info(f"Attendance marked: {student.name} ({student.student_id}) - {status}")
        
        return jsonify({
            'success': True,
            'message': f'{student.name} marked {status.lower()}',
            'student_name': student.name,
            'status': status,
            'time': now.strftime('%H:%M:%S')
        })
        
    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/auto_mark_attendance', methods=['POST'])
def auto_mark_attendance():
    """Automatically mark attendance for detected faces"""
    try:
        global face_detector, face_recognition_active
        
        if not FACE_RECOGNITION_AVAILABLE:
            return jsonify({'success': False, 'message': 'Face recognition not available'})
        
        if not face_recognition_active or not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition not active'})
        
        detected_faces = face_detector.get_detected_faces()
        marked_students = []
        
        logger.info(f"Auto mark: Found {len(detected_faces)} detected faces")
        
        for face in detected_faces:
            logger.info(f"Face: {face['name']}, ID: {face['student_id']}, Confidence: {face['confidence']}")
            if face['student_id'] and face['confidence'] > 0.3:  # Lower confidence threshold
                student = Student.query.get(face['student_id'])
                if not student:
                    continue
                
                # Check if already marked present today
                today = date.today()
                existing_record = AttendanceRecord.query.filter_by(
                    student_id=face['student_id'],
                    date=today
                ).first()
                
                if existing_record:
                    continue  # Skip if already marked
                
                # Create attendance record
                now = datetime.now()
                status = 'Present'  # Default status for auto-marked attendance
                
                attendance_record = AttendanceRecord(
                    student_id=face['student_id'],
                    date=today,
                    time_in=now,
                    status=status,
                    confidence_score=face['confidence']
                )
                
                db.session.add(attendance_record)
                marked_students.append({
                    'name': student.name,
                    'student_id': student.student_id,
                    'status': status,
                    'confidence': face['confidence']
                })
        
        if marked_students:
            db.session.commit()
            logger.info(f"Auto-marked attendance for {len(marked_students)} students")
            
            return jsonify({
                'success': True,
                'message': f'Marked {len(marked_students)} students present',
                'marked_students': marked_students
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No new students to mark present'
            })
        
    except Exception as e:
        logger.error(f"Error in auto attendance marking: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/export_attendance')
def export_attendance():
    """Export attendance records"""
    try:
        format_type = request.args.get('format', 'csv')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = AttendanceRecord.query
        
        if date_from:
            query = query.filter(AttendanceRecord.date >= date_from)
        
        if date_to:
            query = query.filter(AttendanceRecord.date <= date_to)
        
        records = query.order_by(AttendanceRecord.date.desc()).all()
        
        if not records:
            flash('No records found for export', 'warning')
            return redirect(url_for('attendance'))
        
        # Export based on format
        if format_type == 'excel':
            filepath = export_attendance_to_excel(records)
        else:
            filepath = export_attendance_to_csv(records)
        
        if filepath and os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            flash('Error exporting attendance', 'error')
            return redirect(url_for('attendance'))
            
    except Exception as e:
        logger.error(f"Error exporting attendance: {str(e)}")
        flash('Error exporting attendance', 'error')
        return redirect(url_for('attendance'))

# ==================== LEAVE MANAGEMENT ROUTES ====================

@app.route('/leave')
def leave_management():
    """Leave management page"""
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        type_filter = request.args.get('leave_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        # Build query
        query = LeaveRequest.query
        
        if status_filter:
            query = query.filter(LeaveRequest.status == status_filter)
        if type_filter:
            query = query.filter(LeaveRequest.leave_type == type_filter)
        if date_from:
            query = query.filter(LeaveRequest.start_date >= date_from)
        if date_to:
            query = query.filter(LeaveRequest.end_date <= date_to)
        
        leave_requests = query.order_by(LeaveRequest.created_at.desc()).all()
        
        # Get counts
        today = date.today()
        pending_count = LeaveRequest.query.filter_by(status='Pending').count()
        approved_count = LeaveRequest.query.filter_by(status='Approved').count()
        rejected_count = LeaveRequest.query.filter_by(status='Rejected').count()
        
        # Count students on leave today
        on_leave_today = LeaveRequest.query.filter(
            LeaveRequest.status == 'Approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).count()
        
        # Get all active students for the apply form
        students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
        
        logger.info(f"Leave management loaded: {len(leave_requests)} requests, {len(students)} students")
        
        return render_template('leave_management_clean.html',
                             leave_requests=leave_requests,
                             students=students,
                             pending_count=pending_count,
                             approved_count=approved_count,
                             rejected_count=rejected_count,
                             on_leave_today=on_leave_today,
                             current_status=status_filter,
                             current_type=type_filter,
                             date_from=date_from,
                             date_to=date_to)
    except Exception as e:
        import traceback
        logger.error(f"Error in leave management: {str(e)}")
        logger.error(traceback.format_exc())
        flash('Error loading leave management', 'error')
        return render_template('leave_management_clean.html', 
                             leave_requests=[], 
                             students=[],
                             pending_count=0, 
                             approved_count=0, 
                             rejected_count=0, 
                             on_leave_today=0,
                             current_status='',
                             current_type='',
                             date_from='',
                             date_to='')

@app.route('/apply_leave', methods=['POST'])
def apply_leave():
    """Apply for leave"""
    try:
        student_id = request.form.get('student_id')
        leave_type = request.form.get('leave_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        reason = request.form.get('reason')
        
        # Validation
        if not all([student_id, leave_type, start_date, end_date, reason]):
            flash('All fields are required', 'error')
            return redirect(url_for('leave_management'))
        
        # Parse dates
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if end < start:
            flash('End date cannot be before start date', 'error')
            return redirect(url_for('leave_management'))
        
        # Check for overlapping leave requests
        existing = LeaveRequest.query.filter(
            LeaveRequest.student_id == student_id,
            LeaveRequest.status != 'Rejected',
            LeaveRequest.start_date <= end,
            LeaveRequest.end_date >= start
        ).first()
        
        if existing:
            flash('A leave request already exists for this period', 'warning')
            return redirect(url_for('leave_management'))
        
        # Create leave request
        leave_request = LeaveRequest(
            student_id=student_id,
            leave_type=leave_type,
            start_date=start,
            end_date=end,
            reason=reason
        )
        
        db.session.add(leave_request)
        db.session.commit()
        
        student = Student.query.get(student_id)
        logger.info(f"Leave request created for {student.name}: {start_date} to {end_date}")
        flash('Leave request submitted successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error applying for leave: {str(e)}")
        flash('Error submitting leave request', 'error')
    
    return redirect(url_for('leave_management'))

@app.route('/review_leave', methods=['POST'])
def review_leave():
    """Review (approve/reject) a leave request"""
    try:
        leave_id = request.form.get('leave_id')
        status = request.form.get('status')
        reviewed_by = request.form.get('reviewed_by')
        review_notes = request.form.get('review_notes', '')
        
        leave_request = LeaveRequest.query.get_or_404(leave_id)
        
        leave_request.status = status
        leave_request.reviewed_by = reviewed_by
        leave_request.reviewed_at = datetime.utcnow()
        leave_request.review_notes = review_notes
        
        # If approved, auto-mark attendance as "On Leave" for the leave period
        if status == 'Approved':
            current_date = leave_request.start_date
            while current_date <= leave_request.end_date:
                # Check if attendance record exists for this date
                existing_record = AttendanceRecord.query.filter_by(
                    student_id=leave_request.student_id,
                    date=current_date
                ).first()
                
                if existing_record:
                    # Update existing record to "On Leave"
                    existing_record.status = 'On Leave'
                else:
                    # Create new record with "On Leave" status
                    attendance_record = AttendanceRecord(
                        student_id=leave_request.student_id,
                        date=current_date,
                        time_in=datetime.combine(current_date, datetime.min.time()),
                        status='On Leave',
                        confidence_score=1.0
                    )
                    db.session.add(attendance_record)
                
                current_date += timedelta(days=1)
        
        db.session.commit()
        
        logger.info(f"Leave request {leave_id} {status.lower()} by {reviewed_by}")
        flash(f'Leave request {status.lower()} successfully!', 'success')
        
    except Exception as e:
        logger.error(f"Error reviewing leave: {str(e)}")
        flash('Error reviewing leave request', 'error')
    
    return redirect(url_for('leave_management'))

@app.route('/api/leave/<int:leave_id>')
def get_leave_details(leave_id):
    """Get leave request details API"""
    try:
        leave = LeaveRequest.query.get_or_404(leave_id)
        return jsonify(leave.to_dict())
    except Exception as e:
        logger.error(f"Error getting leave details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students_on_leave')
def students_on_leave_api():
    """Get students currently on approved leave"""
    try:
        today = date.today()
        on_leave = LeaveRequest.query.filter(
            LeaveRequest.status == 'Approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).all()
        
        return jsonify({
            'count': len(on_leave),
            'students': [leave.to_dict() for leave in on_leave]
        })
    except Exception as e:
        logger.error(f"Error getting students on leave: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== END LEAVE MANAGEMENT ROUTES ====================

@app.route('/reports')
def reports():
    """Attendance reports and analytics"""
    try:
        # Get date range from query parameters
        date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).isoformat())
        date_to = request.args.get('date_to', date.today().isoformat())
        
        # Get attendance records for the date range
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= date_from,
            AttendanceRecord.date <= date_to
        ).all()
        
        # Generate summary
        summary = generate_attendance_summary(records)
        
        # Get department-wise statistics
        dept_stats = {}
        for record in records:
            if record.student and record.student.department:
                dept = record.student.department
                if dept not in dept_stats:
                    dept_stats[dept] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
                
                dept_stats[dept][record.status.lower()] += 1
                dept_stats[dept]['total'] += 1
        
        return render_template('reports_clean.html', 
                             summary=summary,
                             dept_stats=dept_stats,
                             date_from=date_from,
                             date_to=date_to)
        
    except Exception as e:
        logger.error(f"Error in reports route: {str(e)}")
        flash('Error loading reports', 'error')
        return render_template('reports_clean.html')

@app.route('/api/student/<int:student_id>')
def get_student(student_id):
    """Get student details API"""
    try:
        student = Student.query.get_or_404(student_id)
        return jsonify(student.to_dict())
    except Exception as e:
        logger.error(f"Error getting student: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attendance_summary')
def attendance_summary_api():
    """Get attendance summary API"""
    try:
        today = date.today()
        records = AttendanceRecord.query.filter_by(date=today).all()
        summary = generate_attendance_summary(records)
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting attendance summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/today_attendance')
def today_attendance_api():
    """Get today's attendance records API"""
    try:
        today = date.today()
        records = AttendanceRecord.query.filter_by(date=today).order_by(
            AttendanceRecord.created_at.desc()
        ).limit(10).all()
        
        attendance_data = []
        for record in records:
            attendance_data.append({
                'student_name': record.student.name,
                'student_id': record.student.student_id,
                'time': record.time_in.strftime('%H:%M:%S'),
                'status': record.status
            })
        
        return jsonify({
            'date': today.strftime('%Y-%m-%d'),
            'total_present': len(records),
            'records': attendance_data
        })
    except Exception as e:
        logger.error(f"Error getting today's attendance: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/face_recognition_status')
def face_recognition_status():
    """Get face recognition availability status"""
    return jsonify({
        'available': FACE_RECOGNITION_AVAILABLE,
        'active': face_recognition_active,
        'camera_active': detection_active
    })

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Delete a student (soft delete)"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Soft delete - just mark as inactive
        student.is_active = False
        db.session.commit()
        
        flash(f'Student {student_name} deleted successfully', 'success')
        logger.info(f"Student deleted: {student_name} (ID: {student_id})")
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting student: {str(e)}'
        }), 500

@app.route('/permanently_delete_student/<int:student_id>', methods=['POST'])
def permanently_delete_student(student_id):
    """Permanently delete a student and all records"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Delete attendance records first
        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        
        # Delete student image if exists
        if student.image_path and os.path.exists(student.image_path):
            os.remove(student.image_path)
        
        # Delete student record
        db.session.delete(student)
        db.session.commit()
        
        flash(f'Student {student_name} permanently deleted', 'success')
        logger.info(f"Student permanently deleted: {student_name} (ID: {student_id})")
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} permanently deleted'
        })
        
    except Exception as e:
        logger.error(f"Error permanently deleting student: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error permanently deleting student: {str(e)}'
        }), 500

@app.route('/update_attendance_status', methods=['POST'])
def update_attendance_status():
    """Update attendance status for a student"""
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        new_status = data.get('status')
        
        if not record_id or not new_status:
            return jsonify({
                'success': False,
                'message': 'Record ID and status are required'
            }), 400
        
        # Validate status
        valid_statuses = ['Present', 'Absent', 'Late', 'Excused']
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Get attendance record
        attendance_record = AttendanceRecord.query.get_or_404(record_id)
        student = attendance_record.student
        
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found for this record'
            }), 404
        
        # Update record status
        old_status = attendance_record.status
        attendance_record.status = new_status
        
        db.session.commit()
        
        logger.info(f"Attendance status updated: {student.name} {old_status} -> {new_status}")
        
        return jsonify({
            'success': True,
            'message': f'Updated {student.name} status from {old_status} to {new_status}',
            'student_name': student.name,
            'status': new_status
        })
        
    except Exception as e:
        logger.error(f"Error updating attendance status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        }), 500

@app.route('/mark_student_status/<int:student_id>/<status>', methods=['POST'])
def mark_student_status(student_id, status):
    """Quick mark student status (Present/Absent/Late)"""
    try:
        # Validate status
        valid_statuses = ['Present', 'Absent', 'Late', 'Excused']
        if status not in valid_statuses:
            return jsonify({
                'success': False,
                'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        # Get student
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'message': 'Student not found'
            }), 404
        
        # Check if attendance record exists for today
        today = date.today()
        attendance_record = AttendanceRecord.query.filter_by(
            student_id=student_id,
            date=today
        ).first()
        
        if attendance_record:
            # Update existing record
            attendance_record.status = status
            message = f'Updated {student.name} status to {status}'
        else:
            # Create new record
            attendance_record = AttendanceRecord(
                student_id=student_id,
                date=today,
                time_in=datetime.now(),
                status=status,
                marked_by='Manual'
            )
            db.session.add(attendance_record)
            message = f'Marked {student.name} as {status}'
        
        db.session.commit()
        
        logger.info(f"Student status marked: {student.name} -> {status}")
        flash(message, 'success')
        
        return jsonify({
            'success': True,
            'message': message,
            'student_name': student.name,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Error marking student status: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error marking status: {str(e)}'
        }), 500

@app.route('/mark_time_out/<int:record_id>', methods=['POST'])
def mark_time_out(record_id):
    """Mark time out for an attendance record"""
    try:
        record = AttendanceRecord.query.get_or_404(record_id)
        
        if record.time_out:
            return jsonify({
                'success': False,
                'message': 'Time out already marked for this record'
            }), 400
        
        record.time_out = datetime.now()
        db.session.commit()
        
        logger.info(f"Time out marked for record ID: {record_id}")
        
        return jsonify({
            'success': True,
            'message': f'Time out marked at {record.time_out.strftime("%H:%M:%S")}'
        })
        
    except Exception as e:
        logger.error(f"Error marking time out: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error marking time out: {str(e)}'
        }), 500

@app.route('/delete_attendance/<int:record_id>', methods=['POST'])
def delete_attendance(record_id):
    """Delete an attendance record"""
    try:
        record = AttendanceRecord.query.get_or_404(record_id)
        student_name = record.student.name if record.student else 'Unknown'
        
        db.session.delete(record)
        db.session.commit()
        
        logger.info(f"Attendance record deleted: {student_name} (Record ID: {record_id})")
        
        return jsonify({
            'success': True,
            'message': f'Attendance record for {student_name} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting attendance record: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error deleting record: {str(e)}'
        }), 500

# ==================== ANALYTICS DASHBOARD ROUTES ====================

@app.route('/analytics')
def analytics():
    """Advanced Analytics Dashboard"""
    try:
        today = date.today()
        
        # Get date range from query params (default: last 30 days)
        days = int(request.args.get('days', 30))
        date_from = today - timedelta(days=days)
        
        # Overview statistics
        total_students = Student.query.filter_by(is_active=True).count()
        today_records = AttendanceRecord.query.filter_by(date=today).all()
        today_present = sum(1 for r in today_records if r.status == 'Present')
        today_rate = round((today_present / total_students * 100), 1) if total_students > 0 else 0
        
        # Weekly average
        week_start = today - timedelta(days=7)
        week_records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= week_start,
            AttendanceRecord.date <= today
        ).all()
        week_present = sum(1 for r in week_records if r.status == 'Present')
        week_days = min(7, (today - week_start).days + 1)
        week_avg = round((week_present / (total_students * week_days) * 100), 1) if total_students > 0 else 0
        
        # Monthly average
        month_start = today - timedelta(days=30)
        month_records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= month_start,
            AttendanceRecord.date <= today
        ).all()
        month_present = sum(1 for r in month_records if r.status == 'Present')
        month_days = 30
        month_avg = round((month_present / (total_students * month_days) * 100), 1) if total_students > 0 else 0
        
        # Students on leave today
        on_leave_today = LeaveRequest.query.filter(
            LeaveRequest.status == 'Approved',
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today
        ).count()
        
        # Pending leave requests
        pending_leaves = LeaveRequest.query.filter_by(status='Pending').count()
        
        return render_template('analytics.html',
                             total_students=total_students,
                             today_rate=today_rate,
                             week_avg=week_avg,
                             month_avg=month_avg,
                             on_leave_today=on_leave_today,
                             pending_leaves=pending_leaves,
                             days=days)
    except Exception as e:
        logger.error(f"Error in analytics route: {str(e)}")
        flash('Error loading analytics', 'error')
        return render_template('analytics.html',
                             total_students=0,
                             today_rate=0,
                             week_avg=0,
                             month_avg=0,
                             on_leave_today=0,
                             pending_leaves=0,
                             days=30)

@app.route('/api/analytics/trend')
def analytics_trend():
    """Get attendance trend data for charts"""
    try:
        days = int(request.args.get('days', 30))
        today = date.today()
        
        trend_data = []
        total_students = Student.query.filter_by(is_active=True).count()
        
        for i in range(days - 1, -1, -1):
            current_date = today - timedelta(days=i)
            records = AttendanceRecord.query.filter_by(date=current_date).all()
            
            present = sum(1 for r in records if r.status == 'Present')
            absent = sum(1 for r in records if r.status == 'Absent')
            late = sum(1 for r in records if r.status == 'Late')
            on_leave = sum(1 for r in records if r.status == 'On Leave')
            
            rate = round((present / total_students * 100), 1) if total_students > 0 else 0
            
            trend_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'label': current_date.strftime('%b %d'),
                'present': present,
                'absent': absent,
                'late': late,
                'on_leave': on_leave,
                'rate': rate
            })
        
        return jsonify({'trend': trend_data, 'total_students': total_students})
    except Exception as e:
        logger.error(f"Error getting trend data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/department')
def analytics_department():
    """Get department-wise attendance statistics"""
    try:
        days = int(request.args.get('days', 30))
        today = date.today()
        date_from = today - timedelta(days=days)
        
        # Get all departments
        departments = db.session.query(Student.department).filter(
            Student.is_active == True,
            Student.department != None
        ).distinct().all()
        
        dept_data = []
        for (dept,) in departments:
            if not dept:
                continue
                
            # Get students in department
            dept_students = Student.query.filter_by(department=dept, is_active=True).all()
            student_ids = [s.id for s in dept_students]
            
            if not student_ids:
                continue
            
            # Get attendance records
            records = AttendanceRecord.query.filter(
                AttendanceRecord.student_id.in_(student_ids),
                AttendanceRecord.date >= date_from,
                AttendanceRecord.date <= today
            ).all()
            
            present = sum(1 for r in records if r.status == 'Present')
            total_possible = len(student_ids) * days
            rate = round((present / total_possible * 100), 1) if total_possible > 0 else 0
            
            dept_data.append({
                'department': dept,
                'students': len(student_ids),
                'present': present,
                'rate': rate
            })
        
        # Sort by rate descending
        dept_data.sort(key=lambda x: x['rate'], reverse=True)
        
        return jsonify({'departments': dept_data})
    except Exception as e:
        logger.error(f"Error getting department data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/status_distribution')
def analytics_status_distribution():
    """Get attendance status distribution"""
    try:
        days = int(request.args.get('days', 30))
        today = date.today()
        date_from = today - timedelta(days=days)
        
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= date_from,
            AttendanceRecord.date <= today
        ).all()
        
        distribution = {
            'Present': 0,
            'Absent': 0,
            'Late': 0,
            'On Leave': 0
        }
        
        for record in records:
            status = record.status if record.status in distribution else 'Absent'
            distribution[status] += 1
        
        return jsonify({'distribution': distribution})
    except Exception as e:
        logger.error(f"Error getting status distribution: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/top_students')
def analytics_top_students():
    """Get top performing students by attendance"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 10))
        today = date.today()
        date_from = today - timedelta(days=days)
        
        students = Student.query.filter_by(is_active=True).all()
        
        student_stats = []
        for student in students:
            records = AttendanceRecord.query.filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.date >= date_from,
                AttendanceRecord.date <= today
            ).all()
            
            present = sum(1 for r in records if r.status == 'Present')
            rate = round((present / days * 100), 1) if days > 0 else 0
            
            student_stats.append({
                'id': student.id,
                'name': student.name,
                'student_id': student.student_id,
                'department': student.department,
                'present_days': present,
                'rate': rate
            })
        
        # Sort by rate descending and get top
        student_stats.sort(key=lambda x: x['rate'], reverse=True)
        top_students = student_stats[:limit]
        
        return jsonify({'top_students': top_students})
    except Exception as e:
        logger.error(f"Error getting top students: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/at_risk')
def analytics_at_risk():
    """Get students with low attendance (at risk)"""
    try:
        days = int(request.args.get('days', 30))
        threshold = float(request.args.get('threshold', 75))
        limit = int(request.args.get('limit', 10))
        today = date.today()
        date_from = today - timedelta(days=days)
        
        students = Student.query.filter_by(is_active=True).all()
        
        at_risk = []
        for student in students:
            records = AttendanceRecord.query.filter(
                AttendanceRecord.student_id == student.id,
                AttendanceRecord.date >= date_from,
                AttendanceRecord.date <= today
            ).all()
            
            present = sum(1 for r in records if r.status == 'Present')
            rate = round((present / days * 100), 1) if days > 0 else 0
            
            if rate < threshold:
                at_risk.append({
                    'id': student.id,
                    'name': student.name,
                    'student_id': student.student_id,
                    'department': student.department,
                    'present_days': present,
                    'rate': rate
                })
        
        # Sort by rate ascending (worst first)
        at_risk.sort(key=lambda x: x['rate'])
        
        return jsonify({'at_risk': at_risk[:limit], 'threshold': threshold})
    except Exception as e:
        logger.error(f"Error getting at-risk students: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/weekly_heatmap')
def analytics_weekly_heatmap():
    """Get weekly attendance heatmap data"""
    try:
        weeks = int(request.args.get('weeks', 4))
        today = date.today()
        total_students = Student.query.filter_by(is_active=True).count()
        
        heatmap_data = []
        
        for week in range(weeks - 1, -1, -1):
            week_start = today - timedelta(days=today.weekday() + (week * 7))
            week_data = {'week': f'Week {weeks - week}', 'days': []}
            
            for day in range(7):
                current_date = week_start + timedelta(days=day)
                if current_date > today:
                    week_data['days'].append({'day': current_date.strftime('%a'), 'rate': None})
                    continue
                
                records = AttendanceRecord.query.filter_by(date=current_date).all()
                present = sum(1 for r in records if r.status == 'Present')
                rate = round((present / total_students * 100), 1) if total_students > 0 else 0
                
                week_data['days'].append({
                    'day': current_date.strftime('%a'),
                    'date': current_date.strftime('%Y-%m-%d'),
                    'rate': rate
                })
            
            heatmap_data.append(week_data)
        
        return jsonify({'heatmap': heatmap_data})
    except Exception as e:
        logger.error(f"Error getting heatmap data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/recent_activity')
def analytics_recent_activity():
    """Get recent attendance activity"""
    try:
        limit = int(request.args.get('limit', 20))
        
        records = AttendanceRecord.query.order_by(
            AttendanceRecord.created_at.desc()
        ).limit(limit).all()
        
        activity = []
        for record in records:
            activity.append({
                'student_name': record.student.name if record.student else 'Unknown',
                'student_id': record.student.student_id if record.student else 'N/A',
                'status': record.status,
                'date': record.date.strftime('%Y-%m-%d'),
                'time': record.time_in.strftime('%H:%M:%S') if record.time_in else 'N/A',
                'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S') if record.created_at else 'N/A'
            })
        
        return jsonify({'activity': activity})
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ==================== END ANALYTICS DASHBOARD ROUTES ====================

if __name__ == '__main__':
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Cleanup on exit
        if simple_camera:
            simple_camera.stop_camera()
        if FACE_RECOGNITION_AVAILABLE and face_detector:
            face_detector.stop_detection()