"""
SMS Notification Service for Smart Attendance System.
Handles sending SMS notifications via Twilio.
"""
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Try to import twilio, but don't fail if not installed
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None
    TwilioRestException = Exception


class SMSService:
    """Service for sending SMS notifications via Twilio."""
    
    MAX_SMS_LENGTH = 160  # Standard SMS length
    
    def __init__(self, config):
        """
        Initialize SMSService with configuration.
        
        Args:
            config: Flask app config object with Twilio settings
        """
        self.enabled = getattr(config, 'NOTIFICATION_SMS_ENABLED', False)
        self.account_sid = getattr(config, 'TWILIO_ACCOUNT_SID', '')
        self.auth_token = getattr(config, 'TWILIO_AUTH_TOKEN', '')
        self.phone_number = getattr(config, 'TWILIO_PHONE_NUMBER', '')
        
        # Check if properly configured
        self.configured = bool(self.account_sid and self.auth_token and self.phone_number)
        
        # Initialize Twilio client if available and configured
        self.client = None
        if TWILIO_AVAILABLE and self.configured:
            try:
                self.client = TwilioClient(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
        
        if self.enabled and not TWILIO_AVAILABLE:
            logger.warning("SMS notifications enabled but Twilio library not installed. Run: pip install twilio")
        elif self.enabled and not self.configured:
            logger.warning("SMS notifications enabled but Twilio credentials not configured")
    
    def is_available(self) -> bool:
        """Check if SMS service is available for use."""
        return self.enabled and self.configured and TWILIO_AVAILABLE and self.client is not None
    
    def send_sms(self, to: str, message: str) -> Tuple[bool, str]:
        """
        Send an SMS notification.
        
        Args:
            to: Recipient phone number (with country code, e.g., +1234567890)
            message: SMS message content
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            return False, "SMS notifications are disabled"
        
        if not TWILIO_AVAILABLE:
            return False, "Twilio library not installed"
        
        if not self.configured:
            return False, "Twilio credentials not configured"
        
        if not self.client:
            return False, "Twilio client not initialized"
        
        if not to:
            return False, "Recipient phone number is required"
        
        # Normalize phone number
        to = self._normalize_phone(to)
        if not to:
            return False, "Invalid phone number format"
        
        # Truncate message if too long
        if len(message) > self.MAX_SMS_LENGTH:
            message = message[:self.MAX_SMS_LENGTH - 3] + "..."
            logger.warning(f"SMS message truncated to {self.MAX_SMS_LENGTH} characters")
        
        try:
            sms = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to
            )
            
            logger.info(f"SMS sent successfully to {to}: SID={sms.sid}")
            return True, f"SMS sent successfully (SID: {sms.sid})"
            
        except TwilioRestException as e:
            error_msg = f"Twilio error: {e.msg}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send SMS: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def _normalize_phone(self, phone: str) -> str:
        """
        Normalize phone number to E.164 format.
        
        Args:
            phone: Phone number string
            
        Returns:
            Normalized phone number or empty string if invalid
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters except leading +
        cleaned = phone.strip()
        if cleaned.startswith('+'):
            cleaned = '+' + ''.join(filter(str.isdigit, cleaned[1:]))
        else:
            cleaned = ''.join(filter(str.isdigit, cleaned))
            # Assume it needs a country code if less than 10 digits or doesn't start with +
            if len(cleaned) == 10:
                # Assume US/Canada if 10 digits
                cleaned = '+1' + cleaned
            elif len(cleaned) > 10:
                cleaned = '+' + cleaned
        
        # Validate minimum length
        if len(cleaned) < 10:
            return ""
        
        return cleaned
    
    def create_absence_sms(self, student_name: str, date: str) -> str:
        """
        Create absence notification SMS content.
        
        Returns:
            SMS message string
        """
        return f"Absence Alert: {student_name} was marked absent on {date}. Contact school if unexpected."
    
    def create_low_attendance_sms(self, student_name: str, percentage: float, threshold: float) -> str:
        """
        Create low attendance warning SMS content.
        
        Returns:
            SMS message string
        """
        return f"Low Attendance: {student_name}'s attendance is {percentage:.1f}% (min: {threshold:.1f}%). Please ensure regular attendance."
    
    def create_leave_status_sms(self, student_name: str, status: str, leave_type: str,
                                 start_date: str, end_date: str) -> str:
        """
        Create leave status notification SMS content.
        
        Returns:
            SMS message string
        """
        return f"Leave {status}: {student_name}'s {leave_type} leave ({start_date} to {end_date}) has been {status.lower()}."
