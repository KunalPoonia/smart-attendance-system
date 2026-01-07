from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from extensions import db
from database.models import Student, AttendanceRecord
from services.recognition_service import recognition_service
from utils.helpers import validate_student_data, save_uploaded_file
import os
import logging

bp = Blueprint('students', __name__)
logger = logging.getLogger(__name__)

@bp.route('/students')
def index():
    """Student management page"""
    try:
        students = Student.query.filter_by(is_active=True).all()
        return render_template('students.html', students=students)
    except Exception as e:
        logger.error(f"Error in students route: {str(e)}")
        flash('Error loading students', 'error')
        return render_template('students.html', students=[])

@bp.route('/register_student', methods=['GET', 'POST'])
def register():
    """Register new student"""
    if request.method == 'GET':
        return render_template('register_student.html')
    
    try:
        data = {
            'student_id': request.form.get('student_id'),
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'department': request.form.get('department'),
            'year': request.form.get('year'),
            'section': request.form.get('section')
        }
        
        errors = validate_student_data(data)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register_student.html', data=data)
        
        existing_student = Student.query.filter_by(student_id=data['student_id']).first()
        if existing_student:
            flash('Student ID already exists', 'error')
            return render_template('register_student.html', data=data)
        
        if 'image' not in request.files:
            flash('Student photo is required', 'error')
            return render_template('register_student.html', data=data)
        
        file = request.files['image']
        if file.filename == '':
            flash('No image selected', 'error')
            return render_template('register_student.html', data=data)
        
        image_path = save_uploaded_file(
            file, 
            current_app.config['STUDENT_IMAGES_FOLDER'],
            f"student_{data['student_id']}_"
        )
        
        if not image_path:
            flash('Error uploading image', 'error')
            return render_template('register_student.html', data=data)
        
        face_encoding = None
        if recognition_service.is_available():
            face_encoding = recognition_service.encode_from_image(image_path)
            if face_encoding is None:
                flash('No face detected in the image. Please upload a clear photo.', 'warning')
            else:
                flash('Face encoding created successfully!', 'success')
        
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
        logger.info(f"Student registered: {data['student_id']}")
        return redirect(url_for('students.index'))
        
    except Exception as e:
        logger.error(f"Error registering student: {str(e)}")
        flash('Error registering student', 'error')
        return render_template('register_student.html')

@bp.route('/api/student/<int:student_id>')
def get_student(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        return jsonify(student.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/delete_student/<int:student_id>', methods=['POST'])
def delete(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        student.is_active = False
        db.session.commit()
        flash(f'Student {student.name} deleted successfully', 'success')
        return jsonify({'success': True, 'message': 'Student deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/permanently_delete_student/<int:student_id>', methods=['POST'])
def permanent_delete(student_id):
    try:
        student = Student.query.get_or_404(student_id)
        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        if student.image_path and os.path.exists(student.image_path):
            os.remove(student.image_path)
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Permanently deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
