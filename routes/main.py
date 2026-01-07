from flask import Blueprint, render_template, jsonify
from extensions import db
from database.models import Student, AttendanceRecord
from services.recognition_service import recognition_service
from services.camera_service import camera_service
from datetime import date, datetime

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    try:
        total_students = Student.query.filter_by(is_active=True).count()
        today = date.today()
        today_attendance = AttendanceRecord.query.filter_by(date=today).count()
        
        recent_records = AttendanceRecord.query.order_by(
            AttendanceRecord.created_at.desc()
        ).limit(10).all()
        
        return render_template('index.html', 
                             total_students=total_students,
                             today_attendance=today_attendance,
                             recent_records=recent_records)
    except Exception:
        return render_template('index.html')

@bp.route('/api/attendance_summary')
def summary_api():
    try:
        today = date.today()
        records = AttendanceRecord.query.filter_by(date=today).all()
        
        total = len(records)
        total_students = Student.query.filter_by(is_active=True).count()
        percentage = 0
        if total_students > 0:
            percentage = int((total / total_students) * 100)
            
        return jsonify({
            'total_present': total,
            'present_percentage': percentage
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/today_attendance')
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
                'student_id': record.student.student_id if record.student else '?',
                'time': record.time_in.strftime('%H:%M'),
                'status': record.status
            })
        
        return jsonify({
            'date': today.strftime('%Y-%m-%d'),
            'total_present': len(records),
            'records': attendance_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/api/face_recognition_status')
def status():
    return jsonify({
        'available': recognition_service.is_available(),
        'active': recognition_service.is_active,
        'camera_active': camera_service.is_running
    })
