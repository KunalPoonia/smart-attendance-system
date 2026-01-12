"""
Notification Manager for Smart Attendance System.
Central orchestration of all notification logic.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class NotificationManager:
    """Central manager for all attendance notifications."""
    
    def __init__(self, app=None, db=None):
        """
        Initialize NotificationManager.
        
        Args:
            app: Flask application instance
            db: SQLAlchemy database instance
        """
        self.app = app
        self.db = db
        self.email_service = None
        self.sms_service = None
        
        if app is not None:
            self.init_app(app, db)
    
    def init_app(self, app, db):
        """
        Initialize with Flask app.
        
        Args:
            app: Flask application instance
            db: SQLAlchemy database instance
        """
        self.app = app
        self.db = db
        
        # Import services here to avoid circular imports
        from src.notifications.email_service import EmailService
        from src.notifications.sms_service import SMSService
        
        self.email_service = EmailService(app.config)
        self.sms_service = SMSService(app.config)
        
        logger.info(f"NotificationManager initialized. Email: {self.email_service.is_available()}, SMS: {self.sms_service.is_available()}")
    
    def _get_models(self):
        """Get database models (lazy import to avoid circular dependencies)."""
        from src.database.models import Student, AttendanceRecord, NotificationPreference, NotificationLog, LeaveRequest
        return Student, AttendanceRecord, NotificationPreference, NotificationLog, LeaveRequest
    
    def _log_notification(self, student_id: int, notification_type: str, channel: str,
                          recipient: str, subject: str, message: str, 
                          status: str, error_message: str = None) -> None:
        """
        Log a notification to the database.
        
        Args:
            student_id: ID of the student
            notification_type: Type of notification (absence, low_attendance, leave_status)
            channel: Notification channel (email, sms)
            recipient: Recipient address/number
            subject: Notification subject (for email)
            message: Notification message content
            status: Status (sent, failed, skipped)
            error_message: Error message if failed
        """
        try:
            _, _, _, NotificationLog, _ = self._get_models()
            
            log_entry = NotificationLog(
                student_id=student_id,
                notification_type=notification_type,
                channel=channel,
                recipient=recipient,
                subject=subject,
                message=message,
                status=status,
                error_message=error_message,
                sent_at=datetime.utcnow()
            )
            
            self.db.session.add(log_entry)
            self.db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log notification: {e}")
            # Don't raise - logging failure shouldn't break the main flow
    
    def get_notification_preferences(self, student_id: int) -> Optional[Dict[str, Any]]:
        """
        Get notification preferences for a student.
        
        Args:
            student_id: Database ID of the student
            
        Returns:
            NotificationPreference dict or None
        """
        try:
            _, _, NotificationPreference, _, _ = self._get_models()
            pref = NotificationPreference.query.filter_by(student_id=student_id).first()
            return pref.to_dict() if pref else None
        except Exception as e:
            logger.error(f"Error getting notification preferences: {e}")
            return None
    
    def notify_absence(self, student_id: int, absence_date: date) -> Dict[str, Any]:
        """
        Send absence notification for a student.
        
        Args:
            student_id: Database ID of the student
            absence_date: Date of the absence
            
        Returns:
            Dict with email_sent, sms_sent, and any error messages
        """
        result = {'email_sent': False, 'sms_sent': False, 'errors': []}
        
        try:
            Student, _, NotificationPreference, _, _ = self._get_models()
            
            student = Student.query.get(student_id)
            if not student:
                result['errors'].append(f"Student {student_id} not found")
                return result
            
            # Get notification preferences
            pref = NotificationPreference.query.filter_by(student_id=student_id).first()
            if not pref:
                logger.info(f"No notification preferences for student {student_id}")
                return result
            
            # Check if absence alerts are enabled
            if not pref.absence_alerts:
                logger.info(f"Absence alerts disabled for student {student_id}")
                return result
            
            date_str = absence_date.strftime('%Y-%m-%d')
            
            # Send email notification
            if pref.email_enabled and pref.parent_email and self.email_service.is_available():
                subject, plain_body, html_body = self.email_service.create_absence_email(
                    student.name, date_str
                )
                success, msg = self.email_service.send_email(
                    pref.parent_email, subject, plain_body, html_body
                )
                result['email_sent'] = success
                
                self._log_notification(
                    student_id=student_id,
                    notification_type='absence',
                    channel='email',
                    recipient=pref.parent_email,
                    subject=subject,
                    message=plain_body,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if not success:
                    result['errors'].append(f"Email: {msg}")
            
            # Send SMS notification
            if pref.sms_enabled and pref.parent_phone and self.sms_service.is_available():
                sms_message = self.sms_service.create_absence_sms(student.name, date_str)
                success, msg = self.sms_service.send_sms(pref.parent_phone, sms_message)
                result['sms_sent'] = success
                
                self._log_notification(
                    student_id=student_id,
                    notification_type='absence',
                    channel='sms',
                    recipient=pref.parent_phone,
                    subject=None,
                    message=sms_message,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if not success:
                    result['errors'].append(f"SMS: {msg}")
            
            logger.info(f"Absence notification for {student.name}: email={result['email_sent']}, sms={result['sms_sent']}")
            
        except Exception as e:
            logger.error(f"Error sending absence notification: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def calculate_attendance_percentage(self, student_id: int, days: int = 30) -> float:
        """
        Calculate attendance percentage for a student.
        
        Args:
            student_id: Database ID of the student
            days: Number of days to consider (default 30)
            
        Returns:
            Attendance percentage (0-100)
        """
        try:
            _, AttendanceRecord, _, _, _ = self._get_models()
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Count total school days (records for any student in the period)
            # For simplicity, we count days where at least one record exists
            total_days = self.db.session.query(
                self.db.func.count(self.db.func.distinct(AttendanceRecord.date))
            ).filter(
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date
            ).scalar() or 0
            
            if total_days == 0:
                return 100.0  # No school days = 100% attendance
            
            # Count present days for this student
            present_days = AttendanceRecord.query.filter(
                AttendanceRecord.student_id == student_id,
                AttendanceRecord.date >= start_date,
                AttendanceRecord.date <= end_date,
                AttendanceRecord.status.in_(['Present', 'Late', 'On Leave'])
            ).count()
            
            percentage = (present_days / total_days) * 100
            return round(percentage, 2)
            
        except Exception as e:
            logger.error(f"Error calculating attendance: {e}")
            return 100.0  # Default to 100% on error
    
    def check_and_notify_low_attendance(self, student_id: int) -> Dict[str, Any]:
        """
        Check if student has low attendance and send notification if needed.
        
        Args:
            student_id: Database ID of the student
            
        Returns:
            Dict with percentage, below_threshold, and notification results
        """
        result = {
            'percentage': 100.0,
            'below_threshold': False,
            'notification_sent': False,
            'errors': []
        }
        
        try:
            Student, _, NotificationPreference, _, _ = self._get_models()
            
            student = Student.query.get(student_id)
            if not student:
                result['errors'].append(f"Student {student_id} not found")
                return result
            
            # Get notification preferences
            pref = NotificationPreference.query.filter_by(student_id=student_id).first()
            threshold = pref.low_attendance_threshold if pref else 75.0
            
            # Calculate attendance
            percentage = self.calculate_attendance_percentage(student_id)
            result['percentage'] = percentage
            result['below_threshold'] = percentage < threshold
            
            if not result['below_threshold']:
                return result
            
            # Check if notifications are enabled
            if not pref or not pref.low_attendance_alerts:
                logger.info(f"Low attendance alerts disabled for student {student_id}")
                return result
            
            # Send notifications
            if pref.email_enabled and pref.parent_email and self.email_service.is_available():
                subject, plain_body, html_body = self.email_service.create_low_attendance_email(
                    student.name, percentage, threshold
                )
                success, msg = self.email_service.send_email(
                    pref.parent_email, subject, plain_body, html_body
                )
                
                self._log_notification(
                    student_id=student_id,
                    notification_type='low_attendance',
                    channel='email',
                    recipient=pref.parent_email,
                    subject=subject,
                    message=plain_body,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if success:
                    result['notification_sent'] = True
                else:
                    result['errors'].append(f"Email: {msg}")
            
            if pref.sms_enabled and pref.parent_phone and self.sms_service.is_available():
                sms_message = self.sms_service.create_low_attendance_sms(
                    student.name, percentage, threshold
                )
                success, msg = self.sms_service.send_sms(pref.parent_phone, sms_message)
                
                self._log_notification(
                    student_id=student_id,
                    notification_type='low_attendance',
                    channel='sms',
                    recipient=pref.parent_phone,
                    subject=None,
                    message=sms_message,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if success:
                    result['notification_sent'] = True
                else:
                    result['errors'].append(f"SMS: {msg}")
            
            logger.info(f"Low attendance check for {student.name}: {percentage}% (threshold: {threshold}%)")
            
        except Exception as e:
            logger.error(f"Error checking low attendance: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def notify_leave_status(self, leave_request_id: int, status: str, notes: str = "") -> Dict[str, Any]:
        """
        Send leave status notification.
        
        Args:
            leave_request_id: ID of the leave request
            status: New status (Approved/Rejected)
            notes: Optional review notes
            
        Returns:
            Dict with notification results
        """
        result = {'email_sent': False, 'sms_sent': False, 'errors': []}
        
        try:
            Student, _, NotificationPreference, _, LeaveRequest = self._get_models()
            
            leave = LeaveRequest.query.get(leave_request_id)
            if not leave:
                result['errors'].append(f"Leave request {leave_request_id} not found")
                return result
            
            student = Student.query.get(leave.student_id)
            if not student:
                result['errors'].append(f"Student not found for leave request")
                return result
            
            # Get notification preferences
            pref = NotificationPreference.query.filter_by(student_id=leave.student_id).first()
            if not pref or not pref.leave_status_alerts:
                logger.info(f"Leave status alerts disabled for student {leave.student_id}")
                return result
            
            start_str = leave.start_date.strftime('%Y-%m-%d')
            end_str = leave.end_date.strftime('%Y-%m-%d')
            
            # Send email notification
            if pref.email_enabled and pref.parent_email and self.email_service.is_available():
                subject, plain_body, html_body = self.email_service.create_leave_status_email(
                    student.name, status, leave.leave_type, start_str, end_str, notes
                )
                success, msg = self.email_service.send_email(
                    pref.parent_email, subject, plain_body, html_body
                )
                result['email_sent'] = success
                
                self._log_notification(
                    student_id=leave.student_id,
                    notification_type='leave_status',
                    channel='email',
                    recipient=pref.parent_email,
                    subject=subject,
                    message=plain_body,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if not success:
                    result['errors'].append(f"Email: {msg}")
            
            # Send SMS notification
            if pref.sms_enabled and pref.parent_phone and self.sms_service.is_available():
                sms_message = self.sms_service.create_leave_status_sms(
                    student.name, status, leave.leave_type, start_str, end_str
                )
                success, msg = self.sms_service.send_sms(pref.parent_phone, sms_message)
                result['sms_sent'] = success
                
                self._log_notification(
                    student_id=leave.student_id,
                    notification_type='leave_status',
                    channel='sms',
                    recipient=pref.parent_phone,
                    subject=None,
                    message=sms_message,
                    status='sent' if success else 'failed',
                    error_message=None if success else msg
                )
                
                if not success:
                    result['errors'].append(f"SMS: {msg}")
            
            logger.info(f"Leave status notification for {student.name}: {status}")
            
        except Exception as e:
            logger.error(f"Error sending leave status notification: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def get_notification_history(self, student_id: int = None, notification_type: str = None,
                                  status: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get notification history with optional filters.
        
        Args:
            student_id: Filter by student ID
            notification_type: Filter by type (absence, low_attendance, leave_status)
            status: Filter by status (sent, failed, skipped)
            limit: Maximum number of records to return
            
        Returns:
            List of notification log entries
        """
        try:
            _, _, _, NotificationLog, _ = self._get_models()
            
            query = NotificationLog.query
            
            if student_id:
                query = query.filter_by(student_id=student_id)
            if notification_type:
                query = query.filter_by(notification_type=notification_type)
            if status:
                query = query.filter_by(status=status)
            
            logs = query.order_by(NotificationLog.sent_at.desc()).limit(limit).all()
            
            return [log.to_dict() for log in logs]
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            return []


# Global notification manager instance
notification_manager = NotificationManager()
