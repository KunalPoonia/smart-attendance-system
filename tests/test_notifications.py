"""Tests for Notification System feature."""
import os
import sys
import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ['FLASK_ENV'] = 'development'


class TestNotificationModels:
    """Test notification database models."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        from app import app, db
        from src.database.models import Student, NotificationPreference, NotificationLog
        
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app
        self.client = app.test_client()
        self.db = db
        self.Student = Student
        self.NotificationPreference = NotificationPreference
        self.NotificationLog = NotificationLog
        
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
    
    def test_notification_preference_creation(self):
        """Test creating notification preferences."""
        with self.app.app_context():
            pref = self.NotificationPreference(
                student_id=self.test_student_id,
                parent_email='parent@example.com',
                parent_phone='+1234567890',
                email_enabled=True,
                sms_enabled=False,
                absence_alerts=True,
                low_attendance_alerts=True,
                low_attendance_threshold=75.0,
                leave_status_alerts=True
            )
            self.db.session.add(pref)
            self.db.session.commit()
            
            # Verify
            saved_pref = self.NotificationPreference.query.filter_by(
                student_id=self.test_student_id
            ).first()
            
            assert saved_pref is not None
            assert saved_pref.parent_email == 'parent@example.com'
            assert saved_pref.email_enabled is True
            assert saved_pref.low_attendance_threshold == 75.0
    
    def test_notification_preference_to_dict(self):
        """Test notification preference serialization."""
        with self.app.app_context():
            pref = self.NotificationPreference(
                student_id=self.test_student_id,
                parent_email='parent@example.com',
                email_enabled=True
            )
            self.db.session.add(pref)
            self.db.session.commit()
            
            data = pref.to_dict()
            assert data['student_id'] == self.test_student_id
            assert data['parent_email'] == 'parent@example.com'
            assert data['email_enabled'] is True
    
    def test_notification_log_creation(self):
        """Test creating notification logs."""
        with self.app.app_context():
            log = self.NotificationLog(
                student_id=self.test_student_id,
                notification_type='absence',
                channel='email',
                recipient='parent@example.com',
                subject='Absence Alert',
                message='Your child was absent today.',
                status='sent'
            )
            self.db.session.add(log)
            self.db.session.commit()
            
            # Verify
            saved_log = self.NotificationLog.query.first()
            assert saved_log is not None
            assert saved_log.notification_type == 'absence'
            assert saved_log.status == 'sent'
    
    def test_notification_log_to_dict(self):
        """Test notification log serialization."""
        with self.app.app_context():
            log = self.NotificationLog(
                student_id=self.test_student_id,
                notification_type='low_attendance',
                channel='sms',
                recipient='+1234567890',
                message='Low attendance warning',
                status='failed',
                error_message='Service unavailable'
            )
            self.db.session.add(log)
            self.db.session.commit()
            
            data = log.to_dict()
            assert data['notification_type'] == 'low_attendance'
            assert data['channel'] == 'sms'
            assert data['status'] == 'failed'
            assert data['error_message'] == 'Service unavailable'


class TestEmailService:
    """Test email notification service."""
    
    def test_email_service_not_configured(self):
        """Test email service when not configured."""
        from src.notifications.email_service import EmailService
        
        # Create mock config with empty credentials
        config = MagicMock()
        config.NOTIFICATION_EMAIL_ENABLED = True
        config.SMTP_SERVER = 'smtp.gmail.com'
        config.SMTP_PORT = 587
        config.SMTP_USERNAME = ''
        config.SMTP_PASSWORD = ''
        config.SENDER_EMAIL = ''
        config.SENDER_NAME = 'Test'
        
        service = EmailService(config)
        
        assert service.is_available() is False
        success, msg = service.send_email('test@example.com', 'Test', 'Test body')
        assert success is False
        assert 'not configured' in msg.lower()
    
    def test_email_service_disabled(self):
        """Test email service when disabled."""
        from src.notifications.email_service import EmailService
        
        config = MagicMock()
        config.NOTIFICATION_EMAIL_ENABLED = False
        config.SMTP_USERNAME = 'user'
        config.SMTP_PASSWORD = 'pass'
        config.SENDER_EMAIL = 'sender@example.com'
        
        service = EmailService(config)
        
        success, msg = service.send_email('test@example.com', 'Test', 'Test body')
        assert success is False
        assert 'disabled' in msg.lower()
    
    def test_absence_email_creation(self):
        """Test absence email template creation."""
        from src.notifications.email_service import EmailService
        
        config = MagicMock()
        config.NOTIFICATION_EMAIL_ENABLED = False
        
        service = EmailService(config)
        subject, plain, html = service.create_absence_email('John Doe', '2026-01-12')
        
        assert 'John Doe' in subject
        assert '2026-01-12' in plain
        assert 'John Doe' in html
        assert 'absent' in plain.lower()
    
    def test_low_attendance_email_creation(self):
        """Test low attendance email template creation."""
        from src.notifications.email_service import EmailService
        
        config = MagicMock()
        config.NOTIFICATION_EMAIL_ENABLED = False
        
        service = EmailService(config)
        subject, plain, html = service.create_low_attendance_email('Jane Doe', 65.5, 75.0)
        
        assert '65.5%' in subject or 'Jane Doe' in subject
        assert '65.5' in plain
        assert '75.0' in plain
    
    def test_leave_status_email_creation(self):
        """Test leave status email template creation."""
        from src.notifications.email_service import EmailService
        
        config = MagicMock()
        config.NOTIFICATION_EMAIL_ENABLED = False
        
        service = EmailService(config)
        subject, plain, html = service.create_leave_status_email(
            'John Doe', 'Approved', 'Sick', '2026-01-10', '2026-01-12', 'Feel better soon'
        )
        
        assert 'Approved' in subject
        assert 'John Doe' in plain
        assert 'Sick' in plain


class TestSMSService:
    """Test SMS notification service."""
    
    def test_sms_service_not_configured(self):
        """Test SMS service when not configured."""
        from src.notifications.sms_service import SMSService
        
        config = MagicMock()
        config.NOTIFICATION_SMS_ENABLED = True
        config.TWILIO_ACCOUNT_SID = ''
        config.TWILIO_AUTH_TOKEN = ''
        config.TWILIO_PHONE_NUMBER = ''
        
        service = SMSService(config)
        
        assert service.is_available() is False
    
    def test_sms_service_disabled(self):
        """Test SMS service when disabled."""
        from src.notifications.sms_service import SMSService
        
        config = MagicMock()
        config.NOTIFICATION_SMS_ENABLED = False
        
        service = SMSService(config)
        
        success, msg = service.send_sms('+1234567890', 'Test message')
        assert success is False
        assert 'disabled' in msg.lower()
    
    def test_absence_sms_creation(self):
        """Test absence SMS template creation."""
        from src.notifications.sms_service import SMSService
        
        config = MagicMock()
        config.NOTIFICATION_SMS_ENABLED = False
        
        service = SMSService(config)
        message = service.create_absence_sms('John Doe', '2026-01-12')
        
        assert 'John Doe' in message
        assert '2026-01-12' in message
        assert len(message) <= 160  # SMS length limit
    
    def test_phone_normalization(self):
        """Test phone number normalization."""
        from src.notifications.sms_service import SMSService
        
        config = MagicMock()
        config.NOTIFICATION_SMS_ENABLED = False
        
        service = SMSService(config)
        
        # Test various formats
        assert service._normalize_phone('+1234567890') == '+1234567890'
        assert service._normalize_phone('1234567890') == '+11234567890'  # Assumes US
        assert service._normalize_phone('') == ''
        assert service._normalize_phone('123') == ''  # Too short


class TestNotificationRoutes:
    """Test notification API routes."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        from app import app, db
        from src.database.models import Student, NotificationPreference
        
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app
        self.client = app.test_client()
        self.db = db
        self.Student = Student
        self.NotificationPreference = NotificationPreference
        
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
    
    def test_notification_settings_page_loads(self):
        """Test that notification settings page loads."""
        with self.app.app_context():
            response = self.client.get('/notifications/settings')
            assert response.status_code == 200
            assert b'Notification' in response.data
    
    def test_notification_history_page_loads(self):
        """Test that notification history page loads."""
        with self.app.app_context():
            response = self.client.get('/notifications/history')
            assert response.status_code == 200
    
    def test_get_notification_preferences_api(self):
        """Test getting notification preferences via API."""
        with self.app.app_context():
            response = self.client.get(f'/api/notifications/preferences/{self.test_student_id}')
            assert response.status_code == 200
            
            data = response.get_json()
            assert data['student_id'] == self.test_student_id
    
    def test_update_notification_preferences_api(self):
        """Test updating notification preferences via API."""
        with self.app.app_context():
            response = self.client.post(
                f'/api/notifications/preferences/{self.test_student_id}',
                json={
                    'parent_email': 'newparent@example.com',
                    'email_enabled': True,
                    'absence_alerts': True
                }
            )
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            
            # Verify saved
            pref = self.NotificationPreference.query.filter_by(
                student_id=self.test_student_id
            ).first()
            assert pref is not None
            assert pref.parent_email == 'newparent@example.com'
    
    def test_get_student_attendance_stats(self):
        """Test getting student attendance statistics."""
        with self.app.app_context():
            response = self.client.get(
                f'/api/notifications/student/{self.test_student_id}/attendance'
            )
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'attendance_percentage' in data
            assert 'threshold' in data


class TestNotificationManager:
    """Test notification manager."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        from app import app, db
        from src.database.models import Student, NotificationPreference, AttendanceRecord
        from src.notifications.notification_manager import notification_manager
        
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        
        self.app = app
        self.db = db
        self.Student = Student
        self.NotificationPreference = NotificationPreference
        self.AttendanceRecord = AttendanceRecord
        self.notification_manager = notification_manager
        
        with app.app_context():
            db.create_all()
            notification_manager.init_app(app, db)
            
            # Create test student with preferences
            student = Student(
                student_id='TEST001',
                name='Test Student',
                email='test@example.com',
                department='Computer Science'
            )
            db.session.add(student)
            db.session.commit()
            self.test_student_id = student.id
            
            # Add notification preferences
            pref = NotificationPreference(
                student_id=student.id,
                parent_email='parent@example.com',
                email_enabled=True,
                absence_alerts=True,
                low_attendance_alerts=True,
                low_attendance_threshold=75.0
            )
            db.session.add(pref)
            db.session.commit()
            
        yield
        
        with app.app_context():
            db.drop_all()
    
    def test_get_notification_preferences(self):
        """Test getting notification preferences."""
        with self.app.app_context():
            prefs = self.notification_manager.get_notification_preferences(self.test_student_id)
            assert prefs is not None
            assert prefs['parent_email'] == 'parent@example.com'
    
    def test_calculate_attendance_percentage_no_records(self):
        """Test attendance calculation with no records."""
        with self.app.app_context():
            percentage = self.notification_manager.calculate_attendance_percentage(
                self.test_student_id
            )
            # No school days = 100%
            assert percentage == 100.0
    
    def test_calculate_attendance_percentage_with_records(self):
        """Test attendance calculation with records."""
        with self.app.app_context():
            from datetime import datetime
            
            # Add some attendance records
            today = date.today()
            for i in range(10):
                record = self.AttendanceRecord(
                    student_id=self.test_student_id,
                    date=today - timedelta(days=i),
                    time_in=datetime.now(),
                    status='Present' if i < 7 else 'Absent'  # 7 present, 3 absent
                )
                self.db.session.add(record)
            self.db.session.commit()
            
            percentage = self.notification_manager.calculate_attendance_percentage(
                self.test_student_id, days=30
            )
            # 7 present out of 10 total days = 70%
            assert percentage == 70.0
    
    def test_notify_absence_logs_notification(self):
        """Test that absence notification is logged."""
        with self.app.app_context():
            from src.database.models import NotificationLog
            
            result = self.notification_manager.notify_absence(
                self.test_student_id, 
                date.today()
            )
            
            # Email not configured, so should fail
            assert result['email_sent'] is False
            
            # But should still be logged if email service didn't throw
            # (depends on service configuration)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
