from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Student(db.Model):
    """Student model for storing student information and face encodings"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    department = db.Column(db.String(50))
    year = db.Column(db.String(10))
    section = db.Column(db.String(5))
    face_encoding = db.Column(db.Text)  # JSON string of face encoding
    image_path = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    attendance_records = db.relationship('AttendanceRecord', backref='student', lazy=True)
    
    def set_face_encoding(self, encoding):
        """Convert numpy array to JSON string for storage"""
        if encoding is not None:
            self.face_encoding = json.dumps(encoding.tolist())
    
    def get_face_encoding(self):
        """Convert JSON string back to numpy array"""
        if self.face_encoding:
            import numpy as np
            return np.array(json.loads(self.face_encoding))
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'department': self.department,
            'year': self.year,
            'section': self.section,
            'image_path': self.image_path,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AttendanceRecord(db.Model):
    """Attendance record model for storing daily attendance"""
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    time_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    time_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='Present')  # Present, Absent, Late
    confidence_score = db.Column(db.Float)  # Face recognition confidence
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'student_roll': self.student.student_id if self.student else None,
            'date': self.date.isoformat() if self.date else None,
            'time_in': self.time_in.isoformat() if self.time_in else None,
            'time_out': self.time_out.isoformat() if self.time_out else None,
            'status': self.status,
            'confidence_score': self.confidence_score
        }

class AttendanceSession(db.Model):
    """Session model for managing attendance sessions"""
    __tablename__ = 'attendance_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100))
    teacher_name = db.Column(db.String(100))
    department = db.Column(db.String(50))
    year = db.Column(db.String(10))
    section = db.Column(db.String(5))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_name': self.session_name,
            'subject': self.subject,
            'teacher_name': self.teacher_name,
            'department': self.department,
            'year': self.year,
            'section': self.section,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_active': self.is_active
        }