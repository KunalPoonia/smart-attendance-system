from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file, Response, current_app
from extensions import db
from database.models import Student, AttendanceRecord
from services.camera_service import camera_service
from services.recognition_service import recognition_service
from utils.helpers import export_attendance_to_csv, export_attendance_to_excel, generate_attendance_summary
from datetime import date, datetime, timedelta
import cv2
import logging
import time

bp = Blueprint('attendance', __name__)
logger = logging.getLogger(__name__)

@bp.route('/attendance')
def index():
    try:
        date_filter = request.args.get('date', date.today().isoformat())
        department_filter = request.args.get('department', '')
        year_filter = request.args.get('year', '')
        
        query = AttendanceRecord.query
        if date_filter:
            query = query.filter(AttendanceRecord.date == date_filter)
        if department_filter:
            query = query.join(Student).filter(Student.department == department_filter)
        if year_filter:
            query = query.join(Student).filter(Student.year == year_filter)
            
        records = query.order_by(AttendanceRecord.created_at.desc()).all()
        
        departments = db.session.query(Student.department).distinct().all()
        years = db.session.query(Student.year).distinct().all()
        
        return render_template('attendance.html', 
                             records=records,
                             departments=[d[0] for d in departments if d[0]],
                             years=[y[0] for y in years if y[0]],
                             current_date=date_filter,
                             current_department=department_filter,
                             current_year=year_filter)
    except Exception as e:
        logger.error(f"Error: {e}")
        return render_template('attendance.html', records=[])

@bp.route('/mark_attendance')
def mark_page():
    return render_template('mark_attendance.html')

@bp.route('/start_detection', methods=['POST'])
def start_detection():
    try:
        # Stop recognition if running to prevent conflict? 
        # Actually we might want both. But let's follow original logic which separates them or allows both?
        # New CameraService handles locking so it's safe.
        if camera_service.start_camera():
            return jsonify({'success': True, 'message': 'Camera started'})
        return jsonify({'success': False, 'message': 'Failed to start camera'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/stop_detection', methods=['POST'])
def stop_detection():
    camera_service.stop_camera()
    return jsonify({'success': True, 'message': 'Camera stopped'})

@bp.route('/start_face_recognition', methods=['POST'])
def start_recognition():
    if not recognition_service.is_available():
        return jsonify({'success': False, 'message': 'Library not available'})
        
    students = Student.query.filter_by(is_active=True).all()
    students_data = []
    for s in students:
        enc = s.get_face_encoding()
        if enc is not None:
            students_data.append({
                'id': s.id,
                'name': s.name,
                'student_id': s.student_id,
                'face_encoding': enc
            })
            
    success, msg = recognition_service.start_detection(students_data)
    # Ensure camera is also running for the feed
    camera_service.start_camera() 
    
    return jsonify({'success': success, 'message': msg})

@bp.route('/stop_face_recognition', methods=['POST'])
def stop_recognition():
    recognition_service.stop_detection()
    return jsonify({'success': True, 'message': 'Stopped'})

@bp.route('/get_video_feed')
def video_feed():
    def generate():
        while True:
            # Check if either service is "active" logic 
            # Simplified: just try to get frame from recognition service first (annotated), then camera service
            frame = recognition_service.get_frame()
            
            if frame is None:
                frame = camera_service.get_frame_with_overlay()
            
            if frame is None:
                # If both return None, maybe wait a bit or break if no service is running?
                # For robustness, we check if service IS running.
                if not camera_service.is_running and not recognition_service.is_active:
                     break
                time.sleep(0.1)
                continue

            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            
            time.sleep(0.033)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@bp.route('/get_detected_faces')
def get_faces():
    faces = recognition_service.get_detected_faces()
    # Serialize for JSON
    data = []
    for f in faces:
        data.append({
            'student_id': f['student_id'],
            'name': f['name'],
            'confidence': round(float(f['confidence']), 2),
            'location': [int(x) for x in f['location']],
            'timestamp': f['timestamp'].isoformat()
        })
    return jsonify({'faces': data})

@bp.route('/auto_mark_attendance', methods=['POST'])
def auto_mark():
    """Optimized attendance marking"""
    if not recognition_service.is_active:
        return jsonify({'success': False, 'message': 'Recognition not active'})
        
    faces = recognition_service.get_detected_faces() # Get snapshot of currently detected faces
    if not faces:
        return jsonify({'success': False, 'message': 'No faces detected'})
        
    today = date.today()
    
    # OPTIMIZATION: Fetch ALL records for today in ONE query
    # Store set of (student_id) who are already present
    existing_records = db.session.query(AttendanceRecord.student_id).filter_by(date=today).all()
    present_student_ids = {r[0] for r in existing_records}
    
    marked_count = 0
    marked_list = []
    
    for face in faces:
        sid = face.get('student_id')
        conf = face.get('confidence', 0)
        
        if sid and conf > 0.4: # Threshold
            if sid not in present_student_ids:
                # Mark present
                student = Student.query.get(sid)
                if student:
                    new_record = AttendanceRecord(
                        student_id=sid,
                        date=today,
                        time_in=datetime.now(),
                        status='Present',
                        confidence_score=conf
                    )
                    db.session.add(new_record)
                    present_student_ids.add(sid) # Add to avoid double marking in same loop
                    marked_count += 1
                    marked_list.append({'name': student.name})
    
    if marked_count > 0:
        db.session.commit()
        return jsonify({'success': True, 'message': f'Marked {marked_count} students.', 'marked_students': marked_list})
    else:
        return jsonify({'success': False, 'message': 'No new students to mark.'})

@bp.route('/mark_manual_attendance', methods=['POST'])
def manual_mark():
    student_id_str = request.form.get('student_id') # This is the String ID (e.g., "CS101"), not DB PK
    
    student = Student.query.filter_by(student_id=student_id_str, is_active=True).first()
    if not student:
        flash('Student not found', 'error')
        return redirect(url_for('attendance.mark_page'))
        
    today = date.today()
    exists = AttendanceRecord.query.filter_by(student_id=student.id, date=today).first()
    if exists:
        flash('Already marked present', 'warning')
        return redirect(url_for('attendance.mark_page'))
        
    rec = AttendanceRecord(
        student_id=student.id,
        date=today,
        time_in=datetime.now(),
        status='Present',
        confidence_score=1.0
    )
    db.session.add(rec)
    db.session.commit()
    flash(f'Marked {student.name} present', 'success')
    return redirect(url_for('attendance.mark_page'))

@bp.route('/reports')
def reports():
    try:
        date_from = request.args.get('date_from', (date.today() - timedelta(days=30)).isoformat())
        date_to = request.args.get('date_to', date.today().isoformat())
        
        records = AttendanceRecord.query.filter(
            AttendanceRecord.date >= date_from,
            AttendanceRecord.date <= date_to
        ).all()
        
        summary = generate_attendance_summary(records)
        
        dept_stats = {}
        for record in records:
            if record.student and record.student.department:
                dept = record.student.department
                if dept not in dept_stats:
                    dept_stats[dept] = {'present': 0, 'absent': 0, 'late': 0, 'total': 0}
                dept_stats[dept][record.status.lower()] += 1
                dept_stats[dept]['total'] += 1
                
        return render_template('reports.html', summary=summary, dept_stats=dept_stats)
    except Exception as e:
        logger.error(e)
        return render_template('reports.html')

@bp.route('/export_attendance')
def export():
    # Logic similar to original but using helpers
    records = AttendanceRecord.query.order_by(AttendanceRecord.date.desc()).all()
    # Filtering logic can be added here if needed
    fmt = request.args.get('format', 'csv')
    if fmt == 'excel':
        fp = export_attendance_to_excel(records)
    else:
        fp = export_attendance_to_csv(records)
    return send_file(fp, as_attachment=True)
