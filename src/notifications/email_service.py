"""
Email Notification Service for Smart Attendance System.
Handles sending email notifications via SMTP.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications via SMTP."""
    
    def __init__(self, config):
        """
        Initialize EmailService with configuration.
        
        Args:
            config: Flask app config object with SMTP settings
        """
        self.enabled = getattr(config, 'NOTIFICATION_EMAIL_ENABLED', False)
        self.smtp_server = getattr(config, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(config, 'SMTP_PORT', 587)
        self.username = getattr(config, 'SMTP_USERNAME', '')
        self.password = getattr(config, 'SMTP_PASSWORD', '')
        self.sender_email = getattr(config, 'SENDER_EMAIL', '')
        self.sender_name = getattr(config, 'SENDER_NAME', 'Smart Attendance System')
        
        # Check if properly configured
        self.configured = bool(self.username and self.password and self.sender_email)
        
        if self.enabled and not self.configured:
            logger.warning("Email notifications enabled but SMTP credentials not configured")
    
    def is_available(self) -> bool:
        """Check if email service is available for use."""
        return self.enabled and self.configured
    
    def send_email(self, to: str, subject: str, body: str, html_body: Optional[str] = None) -> Tuple[bool, str]:
        """
        Send an email notification.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.enabled:
            return False, "Email notifications are disabled"
        
        if not self.configured:
            return False, "SMTP credentials not configured"
        
        if not to:
            return False, "Recipient email address is required"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to
            
            # Attach plain text body
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.sender_email, to, msg.as_string())
            
            logger.info(f"Email sent successfully to {to}: {subject}")
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "SMTP authentication failed. Check username and password."
            logger.error(error_msg)
            return False, error_msg
            
        except smtplib.SMTPConnectError:
            error_msg = f"Failed to connect to SMTP server {self.smtp_server}:{self.smtp_port}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def create_absence_email(self, student_name: str, date: str, school_name: str = "School") -> Tuple[str, str, str]:
        """
        Create absence notification email content.
        
        Returns:
            Tuple of (subject, plain_body, html_body)
        """
        subject = f"Absence Alert: {student_name} - {date}"
        
        plain_body = f"""
Dear Parent/Guardian,

This is to inform you that {student_name} was marked absent on {date}.

If this absence was unexpected or if you have any concerns, please contact the school administration.

Best regards,
{school_name}
Smart Attendance System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .alert-box {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 4px; margin: 15px 0; }}
        .footer {{ font-size: 12px; color: #666; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">📧 Attendance Alert</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            
            <div class="alert-box">
                <strong>⚠️ Absence Notification</strong><br>
                <strong>{student_name}</strong> was marked <strong>absent</strong> on <strong>{date}</strong>.
            </div>
            
            <p>If this absence was unexpected or if you have any concerns, please contact the school administration.</p>
            
            <div class="footer">
                <p>Best regards,<br>{school_name}<br>Smart Attendance System</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, plain_body, html_body
    
    def create_low_attendance_email(self, student_name: str, percentage: float, threshold: float, 
                                     school_name: str = "School") -> Tuple[str, str, str]:
        """
        Create low attendance warning email content.
        
        Returns:
            Tuple of (subject, plain_body, html_body)
        """
        subject = f"Low Attendance Warning: {student_name} - {percentage:.1f}%"
        
        plain_body = f"""
Dear Parent/Guardian,

This is to alert you that {student_name}'s attendance has fallen below the required threshold.

Current Attendance: {percentage:.1f}%
Required Minimum: {threshold:.1f}%

Low attendance can affect academic performance and eligibility. Please ensure regular attendance.

If you have any concerns or questions, please contact the school administration.

Best regards,
{school_name}
Smart Attendance System
        """.strip()
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .warning-box {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 4px; margin: 15px 0; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 15px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #dc3545; }}
        .stat-label {{ font-size: 12px; color: #666; }}
        .footer {{ font-size: 12px; color: #666; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">⚠️ Low Attendance Warning</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            
            <div class="warning-box">
                <strong>📉 Attendance Alert</strong><br>
                <strong>{student_name}</strong>'s attendance has fallen below the required threshold.
            </div>
            
            <div class="stats">
                <div class="stat">
                    <div class="stat-value">{percentage:.1f}%</div>
                    <div class="stat-label">Current Attendance</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{threshold:.1f}%</div>
                    <div class="stat-label">Required Minimum</div>
                </div>
            </div>
            
            <p>Low attendance can affect academic performance and eligibility. Please ensure regular attendance.</p>
            
            <div class="footer">
                <p>Best regards,<br>{school_name}<br>Smart Attendance System</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, plain_body, html_body
    
    def create_leave_status_email(self, student_name: str, status: str, leave_type: str,
                                   start_date: str, end_date: str, notes: str = "",
                                   school_name: str = "School") -> Tuple[str, str, str]:
        """
        Create leave status notification email content.
        
        Returns:
            Tuple of (subject, plain_body, html_body)
        """
        status_emoji = "✅" if status == "Approved" else "❌"
        subject = f"Leave Request {status}: {student_name}"
        
        notes_section = f"\nReview Notes: {notes}" if notes else ""
        
        plain_body = f"""
Dear Parent/Guardian,

The leave request for {student_name} has been {status.lower()}.

Leave Details:
- Type: {leave_type}
- Period: {start_date} to {end_date}
- Status: {status}{notes_section}

If you have any questions, please contact the school administration.

Best regards,
{school_name}
Smart Attendance System
        """.strip()
        
        status_color = "#28a745" if status == "Approved" else "#dc3545"
        notes_html = f'<p><strong>Review Notes:</strong> {notes}</p>' if notes else ""
        
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f9f9f9; padding: 20px; border: 1px solid #ddd; }}
        .status-badge {{ display: inline-block; background: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
        .details-box {{ background: white; padding: 15px; border-radius: 8px; margin: 15px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .detail-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .detail-label {{ color: #666; }}
        .detail-value {{ font-weight: bold; }}
        .footer {{ font-size: 12px; color: #666; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2 style="margin: 0;">📋 Leave Request Update</h2>
        </div>
        <div class="content">
            <p>Dear Parent/Guardian,</p>
            
            <p>The leave request for <strong>{student_name}</strong> has been processed:</p>
            
            <p style="text-align: center;">
                <span class="status-badge">{status_emoji} {status}</span>
            </p>
            
            <div class="details-box">
                <div class="detail-row">
                    <span class="detail-label">Leave Type</span>
                    <span class="detail-value">{leave_type}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">Start Date</span>
                    <span class="detail-value">{start_date}</span>
                </div>
                <div class="detail-row">
                    <span class="detail-label">End Date</span>
                    <span class="detail-value">{end_date}</span>
                </div>
            </div>
            
            {notes_html}
            
            <div class="footer">
                <p>Best regards,<br>{school_name}<br>Smart Attendance System</p>
            </div>
        </div>
    </div>
</body>
</html>
        """.strip()
        
        return subject, plain_body, html_body
