from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file, Response
from flask_sqlalchemy import SQLAlchemy
import cv2
import os
from datetime import datetime, date, timedelta
import logging
# Use enhanced face recognition system with multiple fallbacks
try:
    from face_recognition_enhanced import EnhancedFaceRecognition
    FaceRecognitionClass = EnhancedFaceRecognition
    print("🚀 Using Enhanced Face Recognition System")
except ImportError as e:
    print(f"⚠️  Enhanced face recognition not available, trying advanced...")
    try:
        from face_detection_new import AdvancedFaceDetection
        FaceRecognitionClass = AdvancedFaceDetection
        print("✅ Using Advanced Face Detection System")
    except ImportError as e2:
        print(f"⚠️  Advanced face detection not available, trying simple...")
        try:
            from face_recognition_opencv_simple import OpenCVSimpleFaceRecognition
            FaceRecognitionClass = OpenCVSimpleFaceRecognition
            print("✅ Using OpenCV Simple Face Recognition System")
        except ImportError as e3:
            print(f"❌ No face recognition system available: {e3}")
            FaceRecognitionClass = None

# Simple configuration
class SimpleConfig:
    SECRET_KEY = 'dev-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    STUDENT_IMAGES_FOLDER = 'student_images'

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(SimpleConfig)

# Initialize database
db = SQLAlchemy(app)

# Enhanced Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    department = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(100), nullable=False)  # New: Course field
    year = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    semester = db.Column(db.String(10))  # New: Semester field
    roll_number = db.Column(db.String(20))  # New: Roll number
    batch = db.Column(db.String(20))  # New: Batch year
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)  # New: Soft delete flag
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Enhanced Attendance model
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime)
    time_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Present')  # Present, Absent, Late, Excused
    attendance_type = db.Column(db.String(20), default='Regular')  # Regular, Makeup, Special
    subject = db.Column(db.String(100))  # New: Subject/Course
    class_period = db.Column(db.String(20))  # New: Class period (1st, 2nd, etc.)
    teacher_name = db.Column(db.String(100))  # New: Teacher who marked
    remarks = db.Column(db.Text)  # New: Additional remarks
    confidence_score = db.Column(db.Float)
    marked_by = db.Column(db.String(50), default='System')  # Manual or Auto
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    student = db.relationship('Student', backref='attendance_records')

# New: Class Schedule model for better organization
class ClassSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    subject_code = db.Column(db.String(20), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=False)
    class_time = db.Column(db.String(20))  # e.g., "09:00-10:00"
    class_days = db.Column(db.String(50))  # e.g., "Mon,Wed,Fri"
    room_number = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('student_images', exist_ok=True)
os.makedirs('exports', exist_ok=True)

# Initialize face recognition system
if FaceRecognitionClass:
    face_detector = FaceRecognitionClass()
    print(f"🎯 Face recognition system initialized: {FaceRecognitionClass.__name__}")
else:
    print("❌ No face recognition system available - face recognition features will be disabled")
    face_detector = None

# Create tables
with app.app_context():
    db.create_all()

# Add datetime to templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'date': date}

# Routes
@app.route('/')
def index():
    try:
        total_students = Student.query.count()
        today_attendance = AttendanceRecord.query.filter_by(date=date.today()).count()
        recent_records = AttendanceRecord.query.order_by(AttendanceRecord.created_at.desc()).limit(5).all()
        
        return render_template('index.html', 
                             total_students=total_students,
                             today_attendance=today_attendance,
                             recent_records=recent_records)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', total_students=0, today_attendance=0, recent_records=[])

@app.route('/students')
def students():
    try:
        # Get filter parameters
        show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'
        department_filter = request.args.get('department', '')
        course_filter = request.args.get('course', '')
        year_filter = request.args.get('year', '')
        section_filter = request.args.get('section', '')
        
        # Build query
        query = Student.query
        
        if not show_inactive:
            query = query.filter_by(is_active=True)
        
        if department_filter:
            query = query.filter_by(department=department_filter)
        if course_filter:
            query = query.filter_by(course=course_filter)
        if year_filter:
            query = query.filter_by(year=year_filter)
        if section_filter:
            query = query.filter_by(section=section_filter)
        
        students_list = query.order_by(Student.name).all()
        
        # Get filter options
        departments = db.session.query(Student.department).distinct().all()
        courses = db.session.query(Student.course).distinct().all()
        years = db.session.query(Student.year).distinct().all()
        sections = db.session.query(Student.section).distinct().all()
        
        return render_template('students.html', 
                             students=students_list,
                             show_inactive=show_inactive,
                             departments=[d[0] for d in departments if d[0]],
                             courses=[c[0] for c in courses if c[0]],
                             years=[y[0] for y in years if y[0]],
                             sections=[s[0] for s in sections if s[0]],
                             current_department=department_filter,
                             current_course=course_filter,
                             current_year=year_filter,
                             current_section=section_filter)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('students.html', students=[])

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'GET':
        return render_template('register_student.html')
    
    try:
        # Get form data
        student_id = request.form.get('student_id')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        course = request.form.get('course')
        year = request.form.get('year')
        section = request.form.get('section')
        semester = request.form.get('semester')
        roll_number = request.form.get('roll_number')
        batch = request.form.get('batch')
        
        # Basic validation
        if not all([student_id, name, email, department, course, year, section]):
            flash('Please fill in all required fields', 'error')
            return render_template('register_student.html')
        
        # Check if student exists
        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists', 'error')
            return render_template('register_student.html')
        
        # Handle file upload and face registration
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and (file.filename or file.content_type or file.content_length > 0):
                # Create filename with proper extension
                import uuid
                
                # Handle captured photos (blob) vs uploaded files
                if file.filename:
                    file_extension = os.path.splitext(file.filename)[1].lower()
                    if file_extension not in ['.jpg', '.jpeg', '.png', '.gif']:
                        flash('Please upload a valid image file (JPG, PNG, GIF)', 'error')
                        return render_template('register_student.html')
                else:
                    # Captured photo (blob) - default to .jpg
                    file_extension = '.jpg'
                
                filename = f"student_{student_id}_{uuid.uuid4().hex[:8]}{file_extension}"
                image_path = os.path.join('student_images', filename)
                
                # Ensure directory exists
                os.makedirs('student_images', exist_ok=True)
                
                # Save file
                try:
                    file.save(image_path)
                    print(f"Image saved to: {image_path}")
                    
                    # Verify the image was saved and is valid
                    if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
                        flash('Failed to save image file', 'error')
                        return render_template('register_student.html')
                    
                    # Add face to recognition system
                    if face_detector:
                        success, message = face_detector.add_student_face(student_id, name, image_path)
                        print(f"Face registration result: {success}, {message}")
                        
                        if not success:
                            flash(f'Face registration failed: {message}', 'error')
                            if os.path.exists(image_path):
                                os.remove(image_path)  # Remove the file if face registration failed
                            return render_template('register_student.html')
                        else:
                            flash(f'Face registered successfully: {message}', 'success')
                    else:
                        flash('Photo saved, but face recognition system not available', 'warning')
                        
                except Exception as e:
                    print(f"Error saving image: {e}")
                    flash(f'Error saving image: {str(e)}', 'error')
                    return render_template('register_student.html')
        else:
            flash('Student photo is required for face recognition', 'error')
            return render_template('register_student.html')
        
        # Create student
        student = Student(
            student_id=student_id,
            name=name,
            email=email,
            phone=phone,
            department=department,
            course=course,
            year=year,
            section=section,
            semester=semester,
            roll_number=roll_number,
            batch=batch,
            image_path=image_path
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash('Student registered successfully!', 'success')
        return redirect(url_for('students'))
        
    except Exception as e:
        print(f"Error: {e}")
        flash('Error registering student', 'error')
        return render_template('register_student.html')

@app.route('/attendance')
def attendance():
    try:
        # Get filter parameters
        date_filter = request.args.get('date', date.today().isoformat())
        department_filter = request.args.get('department', '')
        course_filter = request.args.get('course', '')
        year_filter = request.args.get('year', '')
        section_filter = request.args.get('section', '')
        status_filter = request.args.get('status', '')
        subject_filter = request.args.get('subject', '')
        
        # Build query with joins
        query = AttendanceRecord.query.join(Student)
        
        if date_filter:
            query = query.filter(AttendanceRecord.date == date_filter)
        
        if department_filter:
            query = query.filter(Student.department == department_filter)
        
        if course_filter:
            query = query.filter(Student.course == course_filter)
        
        if year_filter:
            query = query.filter(Student.year == year_filter)
        
        if section_filter:
            query = query.filter(Student.section == section_filter)
        
        if status_filter:
            query = query.filter(AttendanceRecord.status == status_filter)
        
        if subject_filter:
            query = query.filter(AttendanceRecord.subject.like(f'%{subject_filter}%'))
        
        records = query.order_by(AttendanceRecord.created_at.desc()).all()
        
        # Get unique values for filters
        departments = db.session.query(Student.department).join(AttendanceRecord).distinct().all()
        courses = db.session.query(Student.course).join(AttendanceRecord).distinct().all()
        years = db.session.query(Student.year).join(AttendanceRecord).distinct().all()
        sections = db.session.query(Student.section).join(AttendanceRecord).distinct().all()
        subjects = db.session.query(AttendanceRecord.subject).filter(AttendanceRecord.subject.isnot(None)).distinct().all()
        
        # Calculate statistics
        total_records = len(records)
        present_count = len([r for r in records if r.status == 'Present'])
        absent_count = len([r for r in records if r.status == 'Absent'])
        late_count = len([r for r in records if r.status == 'Late'])
        
        stats = {
            'total': total_records,
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'present_percentage': round((present_count / total_records * 100) if total_records > 0 else 0, 1),
            'absent_percentage': round((absent_count / total_records * 100) if total_records > 0 else 0, 1),
            'late_percentage': round((late_count / total_records * 100) if total_records > 0 else 0, 1)
        }
        
        return render_template('attendance.html', 
                             records=records,
                             stats=stats,
                             departments=[d[0] for d in departments if d[0]],
                             courses=[c[0] for c in courses if c[0]],
                             years=[y[0] for y in years if y[0]],
                             sections=[s[0] for s in sections if s[0]],
                             subjects=[s[0] for s in subjects if s[0]],
                             current_date=date_filter,
                             current_department=department_filter,
                             current_course=course_filter,
                             current_year=year_filter,
                             current_section=section_filter,
                             current_status=status_filter,
                             current_subject=subject_filter)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('attendance.html', records=[], stats={})

@app.route('/mark_attendance')
def mark_attendance():
    return render_template('mark_attendance.html')

# Camera detection routes (OpenCV-based)
@app.route('/start_detection', methods=['POST'])
def start_detection():
    try:
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition system not available'})
        success, message = face_detector.start_detection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    try:
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition system not available'})
        success, message = face_detector.stop_detection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/start_face_recognition', methods=['POST'])
def start_face_recognition():
    """Start face recognition (same as start_detection for OpenCV version)"""
    try:
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition system not available'})
        if not face_detector.is_running:
            success, message = face_detector.start_detection()
            if success:
                return jsonify({'success': True, 'message': 'Face recognition started successfully'})
            else:
                return jsonify({'success': False, 'message': message})
        else:
            return jsonify({'success': True, 'message': 'Face recognition already running'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/stop_face_recognition', methods=['POST'])
def stop_face_recognition():
    """Stop face recognition (same as stop_detection for OpenCV version)"""
    try:
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition system not available'})
        success, message = face_detector.stop_detection()
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/get_video_feed')
def get_video_feed():
    def generate_frames():
        if not face_detector:
            return
            
        while face_detector.is_running:
            try:
                # Get frame with face detection annotations (boxes, names, accuracy)
                frame = face_detector.get_current_frame_with_annotations()
                if frame is not None:
                    # Encode frame as JPEG with good quality
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        frame_bytes = buffer.tobytes()
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                import time
                time.sleep(0.033)  # ~30 FPS for smoother video
                
            except Exception as e:
                print(f"Error in video feed: {e}")
                break
    
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_detected_faces')
def get_detected_faces():
    try:
        if not face_detector:
            return jsonify({'faces': [], 'error': 'Face recognition system not available'})
            
        detected_faces = face_detector.get_detected_faces()
        
        # Format response
        faces_data = []
        for face in detected_faces:
            faces_data.append({
                'student_id': face['student_id'],
                'name': face['name'],
                'confidence': face['confidence'],
                'timestamp': face['timestamp'].isoformat()
            })
        
        return jsonify({'faces': faces_data})
        
    except Exception as e:
        return jsonify({'faces': [], 'error': str(e)})

@app.route('/mark_student_present', methods=['POST'])
def mark_student_present():
    """Mark detected student as present"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        confidence = data.get('confidence', 0)
        
        if not student_id:
            return jsonify({'success': False, 'message': 'Student ID required'})
        
        # Get student by student_id (not database ID)
        student = Student.query.filter_by(student_id=student_id).first()
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'})
        
        # Check if already marked present today
        today = date.today()
        existing_record = AttendanceRecord.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing_record:
            return jsonify({
                'success': False, 
                'message': f'{student.name} already marked present today'
            })
        
        # Create attendance record
        now = datetime.now()
        
        attendance_record = AttendanceRecord(
            student_id=student.id,
            date=today,
            time_in=now,
            status='Present',
            confidence_score=confidence
        )
        
        db.session.add(attendance_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{student.name} marked present',
            'student_name': student.name,
            'status': 'Present',
            'time': now.strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/auto_mark_attendance', methods=['POST'])
def auto_mark_attendance():
    """Automatically mark attendance for detected faces"""
    try:
        if not face_detector:
            return jsonify({'success': False, 'message': 'Face recognition system not available'})
            
        detected_faces = face_detector.get_detected_faces()
        marked_students = []
        
        for face in detected_faces:
            if face['student_id'] and face['confidence'] > 0.4:  # Minimum confidence threshold
                student = Student.query.filter_by(student_id=face['student_id']).first()
                if not student:
                    continue
                
                # Check if already marked present today
                today = date.today()
                existing_record = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    date=today
                ).first()
                
                if existing_record:
                    continue  # Skip if already marked
                
                # Create attendance record
                now = datetime.now()
                
                attendance_record = AttendanceRecord(
                    student_id=student.id,
                    date=today,
                    time_in=now,
                    status='Present',
                    confidence_score=face['confidence']
                )
                
                db.session.add(attendance_record)
                marked_students.append({
                    'name': student.name,
                    'student_id': student.student_id,
                    'status': 'Present',
                    'confidence': face['confidence']
                })
        
        if marked_students:
            db.session.commit()
            
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
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/today_attendance')
def api_today_attendance():
    """Get today's attendance records for the sidebar"""
    try:
        today = date.today()
        records = db.session.query(AttendanceRecord, Student).join(Student).filter(
            AttendanceRecord.date == today
        ).order_by(AttendanceRecord.created_at.desc()).limit(10).all()
        
        attendance_data = []
        for record, student in records:
            attendance_data.append({
                'student_id': student.student_id,
                'student_name': student.name,
                'status': record.status,
                'time': record.time_in.strftime('%H:%M') if record.time_in else 'N/A'
            })
        
        return jsonify({
            'date': today.isoformat(),
            'total_present': len([r for r, s in records if r.status == 'Present']),
            'records': attendance_data
        })
        
    except Exception as e:
        return jsonify({
            'date': date.today().isoformat(),
            'total_present': 0,
            'records': [],
            'error': str(e)
        })

@app.route('/reports')
def reports():
    try:
        records = AttendanceRecord.query.all()
        summary = {
            'total_records': len(records),
            'present_count': len([r for r in records if r.status == 'Present']),
            'late_count': 0,
            'absent_count': 0,
            'present_percentage': 100 if records else 0,
            'late_percentage': 0,
            'absent_percentage': 0
        }
        
        return render_template('reports_simple.html', 
                             summary=summary,
                             dept_stats={},
                             date_from=(date.today() - timedelta(days=30)).isoformat(),
                             date_to=date.today().isoformat())
    except Exception as e:
        print(f"Error: {e}")
        return render_template('reports_simple.html')

# Manual attendance marking for testing
@app.route('/mark_manual_attendance', methods=['POST'])
def mark_manual_attendance():
    try:
        student_id = request.form.get('student_id')
        student = Student.query.filter_by(student_id=student_id).first()
        
        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Check if already marked today
        today = date.today()
        existing = AttendanceRecord.query.filter_by(student_id=student.id, date=today).first()
        
        if existing:
            flash(f'{student.name} already marked present today', 'warning')
        else:
            record = AttendanceRecord(student_id=student.id, date=today, time_in=datetime.now())
            db.session.add(record)
            db.session.commit()
            flash(f'{student.name} marked present successfully!', 'success')
        
        return redirect(url_for('mark_attendance'))
        
    except Exception as e:
        print(f"Error: {e}")
        flash('Error marking attendance', 'error')
        return redirect(url_for('mark_attendance'))

# Student Management Routes
@app.route('/api/student/<int:student_id>')
def get_student_api(student_id):
    """Get student details API"""
    try:
        student = Student.query.get_or_404(student_id)
        return jsonify({
            'id': student.id,
            'student_id': student.student_id,
            'name': student.name,
            'email': student.email,
            'phone': getattr(student, 'phone', None),
            'department': student.department,
            'year': student.year,
            'section': student.section,
            'image_path': student.image_path,
            'created_at': student.created_at.isoformat() if student.created_at else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Soft delete a student (keeps attendance records)"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Soft delete - just mark as inactive
        student.is_active = False
        student.updated_at = datetime.utcnow()
        
        # Remove from face recognition system but keep image
        if face_detector:
            face_detector.remove_student_face(student.student_id)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} deactivated successfully. Attendance records preserved.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deactivating student: {str(e)}'
        }), 500

@app.route('/permanently_delete_student/<int:student_id>', methods=['POST'])
def permanently_delete_student(student_id):
    """Permanently delete a student and all records"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        # Delete associated attendance records
        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        
        # Delete student image if exists
        if student.image_path and os.path.exists(student.image_path):
            os.remove(student.image_path)
        
        # Remove from face recognition system
        if face_detector:
            face_detector.remove_student_face(student.student_id)
        
        # Permanently delete student
        db.session.delete(student)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} permanently deleted with all records'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error permanently deleting student: {str(e)}'
        }), 500

@app.route('/reactivate_student/<int:student_id>', methods=['POST'])
def reactivate_student(student_id):
    """Reactivate a deactivated student"""
    try:
        student = Student.query.get_or_404(student_id)
        student_name = student.name
        
        student.is_active = True
        student.updated_at = datetime.utcnow()
        
        # Re-add to face recognition if image exists
        if face_detector and student.image_path and os.path.exists(student.image_path):
            face_detector.add_student_face(student.student_id, student.name, student.image_path)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Student {student_name} reactivated successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error reactivating student: {str(e)}'
        }), 500

@app.route('/edit_student/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    """Edit student details"""
    student = Student.query.get_or_404(student_id)
    
    if request.method == 'GET':
        return render_template('edit_student.html', student=student)
    
    try:
        # Update student details
        student.name = request.form.get('name', student.name)
        student.email = request.form.get('email', student.email)
        student.department = request.form.get('department', student.department)
        student.year = request.form.get('year', student.year)
        student.section = request.form.get('section', student.section)
        
        # Handle image update
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                # Delete old image
                if student.image_path and os.path.exists(student.image_path):
                    os.remove(student.image_path)
                
                # Save new image
                filename = f"student_{student.student_id}_{file.filename}"
                image_path = os.path.join('student_images', filename)
                file.save(image_path)
                student.image_path = image_path
                
                # Update face recognition
                if face_detector:
                    success, message = face_detector.add_student_face(student.student_id, student.name, image_path)
                    if not success:
                        flash(f'Face registration failed: {message}', 'warning')
                else:
                    flash('Photo updated, but face recognition system not available', 'warning')
        
        db.session.commit()
        flash('Student updated successfully!', 'success')
        return redirect(url_for('students'))
        
    except Exception as e:
        flash(f'Error updating student: {str(e)}', 'error')
        return render_template('edit_student.html', student=student)

# Attendance Management Routes
@app.route('/mark_absent', methods=['GET', 'POST'])
def mark_absent():
    """Mark individual students as absent"""
    if request.method == 'GET':
        # Get active students for selection
        students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
        
        # Get unique values for filters
        departments = db.session.query(Student.department).filter_by(is_active=True).distinct().all()
        courses = db.session.query(Student.course).filter_by(is_active=True).distinct().all()
        years = db.session.query(Student.year).filter_by(is_active=True).distinct().all()
        sections = db.session.query(Student.section).filter_by(is_active=True).distinct().all()
        
        return render_template('mark_absent.html', 
                             students=students,
                             departments=[d[0] for d in departments if d[0]],
                             courses=[c[0] for c in courses if c[0]],
                             years=[y[0] for y in years if y[0]],
                             sections=[s[0] for s in sections if s[0]])
    
    try:
        # Handle POST request for marking absent
        student_ids = request.form.getlist('student_ids')
        selected_date = request.form.get('date', date.today().isoformat())
        subject = request.form.get('subject', '')
        class_period = request.form.get('class_period', '')
        teacher_name = request.form.get('teacher_name', '')
        remarks = request.form.get('remarks', '')
        
        if not student_ids:
            flash('Please select at least one student', 'error')
            return redirect(url_for('mark_absent'))
        
        marked_count = 0
        updated_count = 0
        
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student and student.is_active:
                # Check if already has record for this date
                existing = AttendanceRecord.query.filter_by(
                    student_id=student_id, 
                    date=selected_date
                ).first()
                
                if existing:
                    # Update existing record to absent
                    existing.status = 'Absent'
                    existing.subject = subject
                    existing.class_period = class_period
                    existing.teacher_name = teacher_name
                    existing.remarks = remarks
                    existing.marked_by = 'Manual'
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new absent record
                    record = AttendanceRecord(
                        student_id=student_id,
                        date=selected_date,
                        status='Absent',
                        subject=subject,
                        class_period=class_period,
                        teacher_name=teacher_name,
                        remarks=remarks,
                        marked_by='Manual'
                    )
                    db.session.add(record)
                    marked_count += 1
        
        db.session.commit()
        
        total_processed = marked_count + updated_count
        message = f'Processed {total_processed} students: {marked_count} new absent records, {updated_count} updated records'
        flash(message, 'success')
        
        return redirect(url_for('attendance'))
        
    except Exception as e:
        flash(f'Error marking absent: {str(e)}', 'error')
        return redirect(url_for('mark_absent'))

@app.route('/bulk_mark_absent_by_class', methods=['GET', 'POST'])
def bulk_mark_absent_by_class():
    """Bulk mark absent by class/section"""
    if request.method == 'GET':
        # Get filter options
        departments = db.session.query(Student.department).filter_by(is_active=True).distinct().all()
        courses = db.session.query(Student.course).filter_by(is_active=True).distinct().all()
        years = db.session.query(Student.year).filter_by(is_active=True).distinct().all()
        sections = db.session.query(Student.section).filter_by(is_active=True).distinct().all()
        
        return render_template('bulk_mark_absent_by_class.html',
                             departments=[d[0] for d in departments if d[0]],
                             courses=[c[0] for c in courses if c[0]],
                             years=[y[0] for y in years if y[0]],
                             sections=[s[0] for s in sections if s[0]])
    
    try:
        selected_date = request.form.get('date', date.today().isoformat())
        department = request.form.get('department')
        course = request.form.get('course')
        year = request.form.get('year')
        section = request.form.get('section')
        subject = request.form.get('subject', '')
        class_period = request.form.get('class_period', '')
        teacher_name = request.form.get('teacher_name', '')
        
        # Build query for students in the specified class
        query = Student.query.filter_by(is_active=True)
        
        if department:
            query = query.filter_by(department=department)
        if course:
            query = query.filter_by(course=course)
        if year:
            query = query.filter_by(year=year)
        if section:
            query = query.filter_by(section=section)
        
        students_in_class = query.all()
        
        if not students_in_class:
            flash('No students found for the specified criteria', 'warning')
            return redirect(url_for('bulk_mark_absent_by_class'))
        
        # Get students who are already marked present/late today
        present_students = db.session.query(AttendanceRecord.student_id).filter_by(
            date=selected_date
        ).filter(AttendanceRecord.status.in_(['Present', 'Late'])).all()
        
        present_student_ids = [s[0] for s in present_students]
        
        # Mark remaining students as absent
        absent_count = 0
        for student in students_in_class:
            if student.id not in present_student_ids:
                # Check if already marked absent
                existing = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    date=selected_date
                ).first()
                
                if not existing:
                    record = AttendanceRecord(
                        student_id=student.id,
                        date=selected_date,
                        status='Absent',
                        subject=subject,
                        class_period=class_period,
                        teacher_name=teacher_name,
                        marked_by='Bulk Operation'
                    )
                    db.session.add(record)
                    absent_count += 1
        
        db.session.commit()
        
        class_info = f"{department} - {course} - Year {year} - Section {section}"
        flash(f'Marked {absent_count} students as absent for {class_info} on {selected_date}', 'success')
        return redirect(url_for('attendance'))
        
    except Exception as e:
        flash(f'Error in bulk marking: {str(e)}', 'error')
        return redirect(url_for('bulk_mark_absent_by_class'))

@app.route('/delete_attendance/<int:record_id>', methods=['POST'])
def delete_attendance(record_id):
    """Delete an attendance record"""
    try:
        record = AttendanceRecord.query.get_or_404(record_id)
        student_name = record.student.name if record.student else 'Unknown'
        
        db.session.delete(record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Attendance record for {student_name} deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error deleting record: {str(e)}'
        }), 500

@app.route('/update_attendance_status', methods=['POST'])
def update_attendance_status():
    """Update attendance status"""
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        new_status = data.get('status')
        
        if new_status not in ['Present', 'Absent', 'Late', 'Excused']:
            return jsonify({
                'success': False,
                'message': 'Invalid status'
            }), 400
        
        record = AttendanceRecord.query.get_or_404(record_id)
        old_status = record.status
        record.status = new_status
        record.updated_at = datetime.utcnow()
        
        # Update time_in if changing to Present and no time_in exists
        if new_status == 'Present' and not record.time_in:
            record.time_in = datetime.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Status updated from {old_status} to {new_status}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating status: {str(e)}'
        }), 500

@app.route('/mark_time_out/<int:record_id>', methods=['POST'])
def mark_time_out(record_id):
    """Mark time out for attendance record"""
    try:
        record = AttendanceRecord.query.get_or_404(record_id)
        record.time_out = datetime.now()
        record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Time out marked successfully',
            'time_out': record.time_out.strftime('%H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error marking time out: {str(e)}'
        }), 500

@app.route('/mark_present', methods=['GET', 'POST'])
def mark_present():
    """Mark students as present manually"""
    if request.method == 'GET':
        # Get active students for selection
        students = Student.query.filter_by(is_active=True).order_by(Student.name).all()
        
        # Get unique values for filters
        departments = db.session.query(Student.department).filter_by(is_active=True).distinct().all()
        courses = db.session.query(Student.course).filter_by(is_active=True).distinct().all()
        years = db.session.query(Student.year).filter_by(is_active=True).distinct().all()
        sections = db.session.query(Student.section).filter_by(is_active=True).distinct().all()
        
        return render_template('mark_present.html', 
                             students=students,
                             departments=[d[0] for d in departments if d[0]],
                             courses=[c[0] for c in courses if c[0]],
                             years=[y[0] for y in years if y[0]],
                             sections=[s[0] for s in sections if s[0]])
    
    try:
        # Handle POST request for marking present
        student_ids = request.form.getlist('student_ids')
        selected_date = request.form.get('date', date.today().isoformat())
        subject = request.form.get('subject', '')
        class_period = request.form.get('class_period', '')
        teacher_name = request.form.get('teacher_name', '')
        remarks = request.form.get('remarks', '')
        
        if not student_ids:
            flash('Please select at least one student', 'error')
            return redirect(url_for('mark_present'))
        
        marked_count = 0
        updated_count = 0
        
        for student_id in student_ids:
            student = Student.query.get(student_id)
            if student and student.is_active:
                # Check if already has record for this date
                existing = AttendanceRecord.query.filter_by(
                    student_id=student_id, 
                    date=selected_date
                ).first()
                
                if existing:
                    # Update existing record to present
                    existing.status = 'Present'
                    existing.time_in = datetime.now() if not existing.time_in else existing.time_in
                    existing.subject = subject
                    existing.class_period = class_period
                    existing.teacher_name = teacher_name
                    existing.remarks = remarks
                    existing.marked_by = 'Manual'
                    existing.updated_at = datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new present record
                    record = AttendanceRecord(
                        student_id=student_id,
                        date=selected_date,
                        time_in=datetime.now(),
                        status='Present',
                        subject=subject,
                        class_period=class_period,
                        teacher_name=teacher_name,
                        remarks=remarks,
                        marked_by='Manual'
                    )
                    db.session.add(record)
                    marked_count += 1
        
        db.session.commit()
        
        total_processed = marked_count + updated_count
        message = f'Processed {total_processed} students: {marked_count} new present records, {updated_count} updated records'
        flash(message, 'success')
        
        return redirect(url_for('attendance'))
        
    except Exception as e:
        flash(f'Error marking present: {str(e)}', 'error')
        return redirect(url_for('mark_present'))

# Bulk Operations
@app.route('/bulk_mark_absent', methods=['GET', 'POST'])
def bulk_mark_absent():
    """Bulk mark students as absent"""
    if request.method == 'GET':
        students = Student.query.all()
        return render_template('bulk_mark_absent.html', students=students)
    
    try:
        selected_date = request.form.get('date', date.today().isoformat())
        all_students = Student.query.all()
        
        # Get students who are already marked present/late today
        present_students = db.session.query(AttendanceRecord.student_id).filter_by(
            date=selected_date
        ).filter(AttendanceRecord.status.in_(['Present', 'Late'])).all()
        
        present_student_ids = [s[0] for s in present_students]
        
        # Mark remaining students as absent
        absent_count = 0
        for student in all_students:
            if student.id not in present_student_ids:
                # Check if already marked absent
                existing = AttendanceRecord.query.filter_by(
                    student_id=student.id,
                    date=selected_date
                ).first()
                
                if not existing:
                    record = AttendanceRecord(
                        student_id=student.id,
                        date=selected_date,
                        time_in=datetime.now(),
                        status='Absent'
                    )
                    db.session.add(record)
                    absent_count += 1
        
        db.session.commit()
        flash(f'Marked {absent_count} students as absent for {selected_date}', 'success')
        return redirect(url_for('attendance'))
        
    except Exception as e:
        flash(f'Error in bulk marking: {str(e)}', 'error')
        return redirect(url_for('bulk_mark_absent'))

# Additional API endpoints for frontend functionality
@app.route('/api/attendance_summary')
def attendance_summary_api():
    """Get attendance summary API"""
    try:
        today = date.today()
        records = AttendanceRecord.query.filter_by(date=today).all()
        
        total_records = len(records)
        present_count = len([r for r in records if r.status == 'Present'])
        late_count = len([r for r in records if r.status == 'Late'])
        absent_count = len([r for r in records if r.status == 'Absent'])
        
        return jsonify({
            'total_records': total_records,
            'present_count': present_count,
            'late_count': late_count,
            'absent_count': absent_count,
            'present_percentage': (present_count / total_records * 100) if total_records > 0 else 0,
            'date': today.isoformat()
        })
    except Exception as e:
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
                'student_name': record.student.name if record.student else 'Unknown',
                'student_id': record.student.student_id if record.student else 'N/A',
                'time': record.time_in.strftime('%H:%M:%S') if record.time_in else 'N/A',
                'status': record.status
            })
        
        return jsonify({
            'date': today.strftime('%Y-%m-%d'),
            'total_present': len([r for r in records if r.status == 'Present']),
            'records': attendance_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/face_recognition_status')
def face_recognition_status():
    """Get face recognition availability status"""
    stats = face_detector.get_recognition_stats()
    return jsonify({
        'available': True,  # OpenCV is always available
        'active': face_detector.is_running,
        'camera_active': face_detector.is_running,
        'trained_faces': stats['total_students'],
        'total_samples': stats['total_samples'],
        'confidence_threshold': stats['confidence_threshold'],
        'is_trained': stats['is_trained']
    })



# Static file serving for student images
@app.route('/student_images/<filename>')
def serve_student_image(filename):
    """Serve student images"""
    try:
        from flask import send_from_directory
        return send_from_directory('student_images', filename)
    except Exception as e:
        # Return a default avatar or 404
        return '', 404

# Enhanced API Routes (removing duplicates)

# Create database tables
with app.app_context():
    db.create_all()
    print("📊 Database tables created/updated")

if __name__ == '__main__':
    print("🚀 Starting Smart Attendance System...")
    print("📍 Access at: http://127.0.0.1:5000")
    print("✨ Enhanced with structured records and soft delete")
    app.run(debug=True, host='0.0.0.0', port=5000)