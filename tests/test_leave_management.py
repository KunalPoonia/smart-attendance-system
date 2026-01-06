"""Tests for Leave Management feature."""
import os
import sys
import pytest
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ['FLASK_ENV'] = 'development'


class TestLeaveManagement:
    """Test leave management functionality."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        from app import app, db
        from database.models import Student, LeaveRequest, AttendanceRecord
        
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app
        self.client = app.test_client()
        self.db = db
        self.Student = Student
        self.LeaveRequest = LeaveRequest
        self.AttendanceRecord = AttendanceRecord
        
        with app.app_context():
            db.create_all()
            
            # Create test student
            student = Student(
                student_id='TEST001',
                name='Test Student',
                email='test@example.com',
                department='Computer Science',
                year='2nd',
                section='A'
            )
            db.session.add(student)
            db.session.commit()
            self.test_student_id = student.id
            
        yield
        
        with app.app_context():
            db.drop_all()
    
    def test_leave_management_page_loads(self):
        """Test that leave management page loads successfully."""
        with self.app.app_context():
            response = self.client.get('/leave')
            assert response.status_code == 200
            assert b'Leave Management' in response.data
    
    def test_apply_leave_success(self):
        """Test successful leave application."""
        with self.app.app_context():
            start_date = date.today() + timedelta(days=1)
            end_date = date.today() + timedelta(days=3)
            
            response = self.client.post('/apply_leave', data={
                'student_id': self.test_student_id,
                'leave_type': 'Sick',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'reason': 'Medical appointment'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify leave request was created
            leave = self.LeaveRequest.query.first()
            assert leave is not None
            assert leave.leave_type == 'Sick'
            assert leave.status == 'Pending'
            assert leave.reason == 'Medical appointment'
    
    def test_apply_leave_invalid_dates(self):
        """Test leave application with end date before start date."""
        with self.app.app_context():
            start_date = date.today() + timedelta(days=5)
            end_date = date.today() + timedelta(days=1)  # Before start
            
            response = self.client.post('/apply_leave', data={
                'student_id': self.test_student_id,
                'leave_type': 'Personal',
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'reason': 'Personal work'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'End date cannot be before start date' in response.data
    
    def test_approve_leave_creates_attendance_records(self):
        """Test that approving leave creates 'On Leave' attendance records."""
        with self.app.app_context():
            # Create a leave request
            start_date = date.today() + timedelta(days=1)
            end_date = date.today() + timedelta(days=3)
            
            leave = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Sick',
                start_date=start_date,
                end_date=end_date,
                reason='Flu'
            )
            self.db.session.add(leave)
            self.db.session.commit()
            leave_id = leave.id
            
            # Approve the leave
            response = self.client.post('/review_leave', data={
                'leave_id': leave_id,
                'status': 'Approved',
                'reviewed_by': 'Admin',
                'review_notes': 'Approved for medical reasons'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify leave status updated
            leave = self.LeaveRequest.query.get(leave_id)
            assert leave.status == 'Approved'
            assert leave.reviewed_by == 'Admin'
            
            # Verify attendance records created
            attendance_records = self.AttendanceRecord.query.filter_by(
                student_id=self.test_student_id
            ).all()
            
            # Should have 3 records (3 days of leave)
            assert len(attendance_records) == 3
            for record in attendance_records:
                assert record.status == 'On Leave'
    
    def test_reject_leave(self):
        """Test rejecting a leave request."""
        with self.app.app_context():
            # Create a leave request
            leave = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Personal',
                start_date=date.today() + timedelta(days=1),
                end_date=date.today() + timedelta(days=2),
                reason='Personal work'
            )
            self.db.session.add(leave)
            self.db.session.commit()
            leave_id = leave.id
            
            # Reject the leave
            response = self.client.post('/review_leave', data={
                'leave_id': leave_id,
                'status': 'Rejected',
                'reviewed_by': 'Admin',
                'review_notes': 'Insufficient reason'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            # Verify leave status
            leave = self.LeaveRequest.query.get(leave_id)
            assert leave.status == 'Rejected'
            
            # Verify NO attendance records created for rejected leave
            attendance_records = self.AttendanceRecord.query.filter_by(
                student_id=self.test_student_id
            ).all()
            assert len(attendance_records) == 0
    
    def test_leave_api_endpoint(self):
        """Test the leave details API endpoint."""
        with self.app.app_context():
            # Create a leave request
            leave = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Academic',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=1),
                reason='Exam preparation'
            )
            self.db.session.add(leave)
            self.db.session.commit()
            leave_id = leave.id
            
            # Get leave details via API
            response = self.client.get(f'/api/leave/{leave_id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['leave_type'] == 'Academic'
            assert data['reason'] == 'Exam preparation'
            assert data['status'] == 'Pending'
    
    def test_students_on_leave_api(self):
        """Test the students on leave API endpoint."""
        with self.app.app_context():
            # Create an approved leave for today
            leave = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Sick',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=2),
                reason='Sick',
                status='Approved'
            )
            self.db.session.add(leave)
            self.db.session.commit()
            
            # Get students on leave
            response = self.client.get('/api/students_on_leave')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['count'] == 1
    
    def test_leave_duration_calculation(self):
        """Test leave duration calculation."""
        with self.app.app_context():
            leave = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Personal',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=4),
                reason='Vacation'
            )
            self.db.session.add(leave)
            self.db.session.commit()
            
            # Duration should be 5 days (inclusive)
            assert leave.duration_days == 5
    
    def test_prevent_overlapping_leave(self):
        """Test that overlapping leave requests are prevented."""
        with self.app.app_context():
            start_date = date.today() + timedelta(days=5)
            end_date = date.today() + timedelta(days=10)
            
            # Create first leave request
            leave1 = self.LeaveRequest(
                student_id=self.test_student_id,
                leave_type='Personal',
                start_date=start_date,
                end_date=end_date,
                reason='First leave'
            )
            self.db.session.add(leave1)
            self.db.session.commit()
            
            # Try to create overlapping leave
            response = self.client.post('/apply_leave', data={
                'student_id': self.test_student_id,
                'leave_type': 'Sick',
                'start_date': (start_date + timedelta(days=2)).isoformat(),
                'end_date': (end_date + timedelta(days=2)).isoformat(),
                'reason': 'Overlapping leave'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'leave request already exists' in response.data
            
            # Should still only have 1 leave request
            count = self.LeaveRequest.query.count()
            assert count == 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
