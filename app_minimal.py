#!/usr/bin/env python3
"""
Minimal Smart Attendance System
A simplified version that works without complex face recognition dependencies
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date, timedelta
import logging

# Simple configuration
class MinimalConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-minimal-fallback')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///minimal_attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    STUDENT_IMAGES_FOLDER = 'student_images'

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(MinimalConfig)

# Initialize database
db = SQLAlchemy(app)

# Simple Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    department = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(5), nullable=False)
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Simple Attendance model
class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    time_in = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Present')
    marked_by = db.Column(db.String(50), default='Manual')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('Student', backref='attendance_records')

# Create directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('student_images', exist_ok=True)

# Create tables
with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully")

# Add datetime to templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime, 'date': date}

# Routes
@app.route('/')
def index():
    """Main dashboard"""
    try:
        total_students = Student.query.filter_by(is_active=True).count()
        today_attendance = AttendanceRecord.query.filter_by(date=date.today()).count()
        recent_records = AttendanceRecord.query.order_by(AttendanceRecord.created_at.desc()).limit(5).all()
        
        return render_template('index.html', 
                             total_students=total_students,
                             today_attendance=today_attendance,
                             recent_records=recent_records,
                             face_recognition_available=False)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('index.html', 
                             total_students=0, 
                             today_attendance=0, 
                             recent_records=[],
                             face_recognition_available=False)

@app.route('/students')
def students():
    """Student management page"""
    try:
        students_list = Student.query.filter_by(is_active=True).order_by(Student.name).all()
        return render_template('students.html', students=students_list)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('students.html', students=[])

@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    """Register new student"""
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
        
        # Basic validation
        if not all([student_id, name, email, department, course, year, section]):
            flash('Please fill in all required fields', 'error')
            return render_template('register_student.html')
        
        # Check if student exists
        if Student.query.filter_by(student_id=student_id).first():
            flash('Student ID already exists', 'error')
            return render_template('register_student.html')
        
        # Handle image upload (optional for minimal version)
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                import uuid
                file_extension = os.path.splitext(file.filename)[1].lower()
                if file_extension in ['.jpg', '.jpeg', '.png', '.gif']:
                    filename = f"student_{student_id}_{uuid.uuid4().hex[:8]}{file_extension}"
                    image_path = os.path.join('student_images', filename)
                    os.makedirs('student_images', exist_ok=True)
                    file.save(image_path)
        
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
    """Attendance management page"""
    try:
        # Get filter parameters
        date_filter = request.args.get('date', date.today().isoformat())
        department_filter = request.args.get('department', '')
        
        # Build query
        query = AttendanceRecord.query.join(Student)
        
        if date_filter:
            query = query.filter(AttendanceRecord.date == date_filter)
        
        if department_filter:
            query = query.filter(Student.department == department_filter)
        
        records = query.order_by(AttendanceRecord.created_at.desc()).all()
        
        # Get unique departments for filter
        departments = db.session.query(Student.department).distinct().all()
        
        return render_template('attendance.html', 
                             records=records,
                             departments=[d[0] for d in departments if d[0]],
                             current_date=date_filter,
                             current_department=department_filter)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('attendance.html', records=[])

@app.route('/mark_attendance')
def mark_attendance():
    """Manual attendance marking page"""
    return render_template('mark_attendance.html', face_recognition_available=False)

@app.route('/mark_manual_attendance', methods=['POST'])
def mark_manual_attendance():
    """Mark attendance manually using student ID"""
    try:
        student_id = request.form.get('student_id')
        
        if not student_id:
            flash('Student ID is required', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Get student by student_id
        student = Student.query.filter_by(student_id=student_id, is_active=True).first()
        if not student:
            flash(f'Student with ID {student_id} not found', 'error')
            return redirect(url_for('mark_attendance'))
        
        # Check if already marked present today
        today = date.today()
        existing_record = AttendanceRecord.query.filter_by(
            student_id=student.id,
            date=today
        ).first()
        
        if existing_record:
            flash(f'{student.name} already marked present today', 'warning')
            return redirect(url_for('mark_attendance'))
        
        # Create attendance record
        now = datetime.now()
        attendance_record = AttendanceRecord(
            student_id=student.id,
            date=today,
            time_in=now,
            status='Present',
            marked_by='Manual'
        )
        
        db.session.add(attendance_record)
        db.session.commit()
        
        flash(f'{student.name} marked present at {now.strftime("%H:%M:%S")}', 'success')
        return redirect(url_for('mark_attendance'))
        
    except Exception as e:
        print(f"Error: {e}")
        flash('Error marking attendance', 'error')
        return redirect(url_for('mark_attendance'))

@app.route('/reports')
def reports():
    """Simple reports page"""
    try:
        # Get date range
        date_from = request.args.get('date_from', (date.today() - timedelta(days=7)).isoformat())
        date_to = request.args.get('date_to', date.today().isoformat())
        
        # Get attendance records
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= date_from,
            AttendanceRecord.date <= date_to
        ).all()
        
        # Simple statistics
        total_records = len(records)
        present_count = len([r for r in records if r.status == 'Present'])
        
        summary = {
            'total_records': total_records,
            'present_count': present_count,
            'present_percentage': round((present_count / total_records * 100) if total_records > 0 else 0, 1)
        }
        
        return render_template('reports.html', 
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to)
        
    except Exception as e:
        print(f"Error: {e}")
        return render_template('reports.html', summary={})

@app.route('/api/today_attendance')
def api_today_attendance():
    """Get today's attendance records"""
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
            'total_present': len(records),
            'records': attendance_data
        })
        
    except Exception as e:
        return jsonify({
            'date': date.today().isoformat(),
            'total_present': 0,
            'records': [],
            'error': str(e)
        })

# Dummy routes for face recognition (disabled)
@app.route('/start_detection', methods=['POST'])
def start_detection():
    return jsonify({'success': False, 'message': 'Face recognition not available in minimal version'})

@app.route('/stop_detection', methods=['POST'])
def stop_detection():
    return jsonify({'success': False, 'message': 'Face recognition not available in minimal version'})

@app.route('/start_face_recognition', methods=['POST'])
def start_face_recognition():
    return jsonify({'success': False, 'message': 'Face recognition not available in minimal version'})

@app.route('/stop_face_recognition', methods=['POST'])
def stop_face_recognition():
    return jsonify({'success': False, 'message': 'Face recognition not available in minimal version'})

@app.route('/get_detected_faces')
def get_detected_faces():
    return jsonify({'faces': []})

@app.route('/auto_mark_attendance', methods=['POST'])
def auto_mark_attendance():
    return jsonify({'success': False, 'message': 'Auto attendance not available in minimal version'})

if __name__ == '__main__':
    print("🚀 Starting Smart Attendance System (Minimal Version)")
    print("=" * 60)
    print("📍 Features available:")
    print("   ✅ Student registration")
    print("   ✅ Manual attendance marking")
    print("   ✅ Attendance reports")
    print("   ✅ Student management")
    print("   ❌ Face recognition (disabled)")
    print("=" * 60)
    print("🌐 Access the application at: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)