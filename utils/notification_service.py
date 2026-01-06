#!/usr/bin/env python3
"""
Notification and Email Service for Smart Attendance System
Provides comprehensive notification capabilities including email,
SMS placeholders, push notifications, and in-app alerts.

Author: ayushap18
Date: January 2026
ECWoC 2026 Contribution
"""

import os
import json
import logging
import smtplib
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
from queue import Queue, Empty
import time

# Configure logging
logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of notifications."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class NotificationRecipient:
    """Notification recipient details."""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    preferences: Dict[str, bool] = field(default_factory=dict)
    
    def can_receive(self, notification_type: NotificationType) -> bool:
        """Check if recipient can receive notification type."""
        type_key = notification_type.value
        return self.preferences.get(type_key, True)


@dataclass
class Notification:
    """Notification data structure."""
    id: str
    type: NotificationType
    priority: NotificationPriority
    subject: str
    body: str
    recipient: NotificationRecipient
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: NotificationStatus = NotificationStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['type'] = self.type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['scheduled_at'] = self.scheduled_at.isoformat() if self.scheduled_at else None
        data['sent_at'] = self.sent_at.isoformat() if self.sent_at else None
        return data


class EmailTemplates:
    """Email template manager."""
    
    TEMPLATES = {
        'attendance_marked': {
            'subject': 'Attendance Marked - {student_name}',
            'body': '''
Dear {student_name},

Your attendance has been marked successfully.

Details:
- Date: {date}
- Time: {time}
- Status: {status}
- Course/Session: {session_name}

Thank you for attending!

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'low_attendance_warning': {
            'subject': 'Low Attendance Warning - Action Required',
            'body': '''
Dear {student_name},

This is to inform you that your attendance has fallen below the required threshold.

Current Status:
- Overall Attendance: {attendance_rate}%
- Required Minimum: {required_rate}%
- Sessions Attended: {sessions_attended}
- Total Sessions: {total_sessions}

Please ensure regular attendance to maintain academic standing.

If you have any concerns, please contact the administration.

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'perfect_attendance': {
            'subject': 'Congratulations on Perfect Attendance! 🎉',
            'body': '''
Dear {student_name},

Congratulations! You have achieved perfect attendance for {period}.

Your commitment and dedication are commendable.

Statistics:
- Sessions Attended: {sessions_attended}
- Attendance Rate: 100%
- Streak: {streak_days} days

Keep up the excellent work!

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'session_reminder': {
            'subject': 'Reminder: {session_name} starting soon',
            'body': '''
Dear {student_name},

This is a reminder that {session_name} is starting soon.

Details:
- Date: {date}
- Time: {time}
- Location: {location}
- Instructor: {instructor}

Please ensure you arrive on time for attendance marking.

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'attendance_report': {
            'subject': 'Your Attendance Report - {period}',
            'body': '''
Dear {student_name},

Here is your attendance report for {period}.

Summary:
- Overall Attendance Rate: {attendance_rate}%
- Sessions Present: {present_count}
- Sessions Late: {late_count}
- Sessions Absent: {absent_count}
- Total Sessions: {total_sessions}

{additional_notes}

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'admin_daily_summary': {
            'subject': 'Daily Attendance Summary - {date}',
            'body': '''
Daily Attendance Summary
Date: {date}

Overview:
- Total Students: {total_students}
- Present: {present_count} ({present_rate}%)
- Late: {late_count} ({late_rate}%)
- Absent: {absent_count} ({absent_rate}%)

Department Breakdown:
{department_breakdown}

Alerts:
{alerts}

This is an automated report from the Smart Attendance System.
            '''.strip()
        },
        
        'password_reset': {
            'subject': 'Password Reset Request',
            'body': '''
Dear {user_name},

We received a request to reset your password for the Smart Attendance System.

Click the link below to reset your password:
{reset_link}

This link will expire in {expiry_hours} hours.

If you did not request this reset, please ignore this email.

Best regards,
Smart Attendance System
            '''.strip()
        },
        
        'account_verification': {
            'subject': 'Verify Your Account',
            'body': '''
Dear {user_name},

Thank you for registering with the Smart Attendance System.

Please verify your email by clicking the link below:
{verification_link}

This link will expire in {expiry_hours} hours.

Best regards,
Smart Attendance System
            '''.strip()
        }
    }
    
    @classmethod
    def get_template(cls, template_name: str) -> Optional[Dict[str, str]]:
        """Get email template by name."""
        return cls.TEMPLATES.get(template_name)
    
    @classmethod
    def render_template(cls, template_name: str, **kwargs) -> Optional[Dict[str, str]]:
        """Render template with provided variables."""
        template = cls.get_template(template_name)
        if not template:
            return None
        
        try:
            return {
                'subject': template['subject'].format(**kwargs),
                'body': template['body'].format(**kwargs)
            }
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return None
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List available template names."""
        return list(cls.TEMPLATES.keys())
    
    @classmethod
    def add_template(cls, name: str, subject: str, body: str):
        """Add custom template."""
        cls.TEMPLATES[name] = {
            'subject': subject,
            'body': body
        }


class EmailService:
    """
    Email service for sending notifications.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize email service.
        
        Args:
            config: Email configuration dictionary
        """
        self.config = config or {}
        self.smtp_host = self.config.get('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = self.config.get('SMTP_PORT', 587)
        self.smtp_user = self.config.get('SMTP_USER', '')
        self.smtp_password = self.config.get('SMTP_PASSWORD', '')
        self.from_email = self.config.get('FROM_EMAIL', self.smtp_user)
        self.from_name = self.config.get('FROM_NAME', 'Smart Attendance System')
        self.use_tls = self.config.get('USE_TLS', True)
        
        self._connection = None
    
    def _get_connection(self) -> smtplib.SMTP:
        """Get or create SMTP connection."""
        if self._connection is None:
            self._connection = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.use_tls:
                self._connection.starttls()
            if self.smtp_user and self.smtp_password:
                self._connection.login(self.smtp_user, self.smtp_password)
        return self._connection
    
    def close_connection(self):
        """Close SMTP connection."""
        if self._connection:
            try:
                self._connection.quit()
            except Exception:
                pass
            self._connection = None
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: str = None,
        attachments: List[Dict] = None,
        cc: List[str] = None,
        bcc: List[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            attachments: List of attachment dictionaries
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Get all recipients
            all_recipients = [to_email]
            if cc:
                all_recipients.extend(cc)
            if bcc:
                all_recipients.extend(bcc)
            
            # Send email
            connection = self._get_connection()
            connection.sendmail(self.from_email, all_recipients, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'to': to_email,
                'subject': subject,
                'sent_at': datetime.now().isoformat()
            }
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            return {
                'success': False,
                'error': 'Authentication failed',
                'to': to_email
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                'success': False,
                'error': str(e),
                'to': to_email
            }
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {
                'success': False,
                'error': str(e),
                'to': to_email
            }
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """Add attachment to email."""
        filename = attachment.get('filename', 'attachment')
        content = attachment.get('content')
        content_type = attachment.get('content_type', 'application/octet-stream')
        
        if content:
            part = MIMEBase(*content_type.split('/'))
            if isinstance(content, str):
                content = content.encode()
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
    
    def send_template_email(
        self,
        to_email: str,
        template_name: str,
        template_vars: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send email using template.
        
        Args:
            to_email: Recipient email
            template_name: Template name
            template_vars: Template variables
            **kwargs: Additional send_email arguments
            
        Returns:
            Result dictionary
        """
        rendered = EmailTemplates.render_template(template_name, **template_vars)
        if not rendered:
            return {
                'success': False,
                'error': f'Template not found: {template_name}'
            }
        
        return self.send_email(
            to_email=to_email,
            subject=rendered['subject'],
            body=rendered['body'],
            **kwargs
        )
    
    def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        body: str,
        personalize: bool = False
    ) -> Dict[str, Any]:
        """
        Send bulk emails to multiple recipients.
        
        Args:
            recipients: List of recipient dictionaries with email and optional name
            subject: Email subject (can include {name} placeholder)
            body: Email body (can include placeholders)
            personalize: Whether to personalize each email
            
        Returns:
            Bulk send results
        """
        results = {
            'total': len(recipients),
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for recipient in recipients:
            email = recipient.get('email')
            if not email:
                continue
            
            if personalize:
                # Replace placeholders with recipient data
                personalized_subject = subject.format(**recipient)
                personalized_body = body.format(**recipient)
            else:
                personalized_subject = subject
                personalized_body = body
            
            result = self.send_email(email, personalized_subject, personalized_body)
            
            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append({
                'email': email,
                'success': result['success'],
                'error': result.get('error')
            })
        
        return results


class NotificationQueue:
    """
    Queue for processing notifications asynchronously.
    """
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize notification queue.
        
        Args:
            max_workers: Maximum worker threads
        """
        self._queue = Queue()
        self._workers: List[threading.Thread] = []
        self._running = False
        self._max_workers = max_workers
        self._processed = 0
        self._failed = 0
        self._handlers: Dict[NotificationType, Callable] = {}
    
    def register_handler(self, notification_type: NotificationType, handler: Callable):
        """
        Register handler for notification type.
        
        Args:
            notification_type: Type of notification
            handler: Handler function
        """
        self._handlers[notification_type] = handler
        logger.info(f"Registered handler for {notification_type.value}")
    
    def enqueue(self, notification: Notification):
        """
        Add notification to queue.
        
        Args:
            notification: Notification to queue
        """
        notification.status = NotificationStatus.QUEUED
        self._queue.put(notification)
        logger.debug(f"Notification {notification.id} queued")
    
    def start(self):
        """Start queue processing."""
        if self._running:
            return
        
        self._running = True
        
        for i in range(self._max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self._workers.append(worker)
        
        logger.info(f"Started {self._max_workers} notification workers")
    
    def stop(self):
        """Stop queue processing."""
        self._running = False
        
        # Wait for workers to finish
        for worker in self._workers:
            worker.join(timeout=5)
        
        self._workers = []
        logger.info("Notification queue stopped")
    
    def _worker_loop(self):
        """Worker loop for processing notifications."""
        while self._running:
            try:
                notification = self._queue.get(timeout=1)
                self._process_notification(notification)
                self._queue.task_done()
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _process_notification(self, notification: Notification):
        """Process a single notification."""
        handler = self._handlers.get(notification.type)
        
        if not handler:
            logger.warning(f"No handler for notification type: {notification.type.value}")
            notification.status = NotificationStatus.FAILED
            return
        
        try:
            notification.status = NotificationStatus.SENDING
            
            result = handler(notification)
            
            if result.get('success'):
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.now()
                self._processed += 1
                logger.info(f"Notification {notification.id} sent successfully")
            else:
                # Retry logic
                if notification.retry_count < notification.max_retries:
                    notification.retry_count += 1
                    notification.status = NotificationStatus.QUEUED
                    self._queue.put(notification)
                    logger.warning(f"Notification {notification.id} retry {notification.retry_count}")
                else:
                    notification.status = NotificationStatus.FAILED
                    self._failed += 1
                    logger.error(f"Notification {notification.id} failed after {notification.max_retries} retries")
                    
        except Exception as e:
            logger.error(f"Error processing notification {notification.id}: {e}")
            notification.status = NotificationStatus.FAILED
            self._failed += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            'queue_size': self._queue.qsize(),
            'workers': len(self._workers),
            'running': self._running,
            'processed': self._processed,
            'failed': self._failed
        }


class NotificationManager:
    """
    Central notification management system.
    """
    
    def __init__(self, email_config: Dict = None):
        """
        Initialize notification manager.
        
        Args:
            email_config: Email service configuration
        """
        self.email_service = EmailService(email_config)
        self.queue = NotificationQueue()
        self._notification_log: List[Notification] = []
        self._subscribers: Dict[str, List[NotificationRecipient]] = {}
        
        # Register default handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup notification handlers."""
        self.queue.register_handler(NotificationType.EMAIL, self._handle_email)
        self.queue.register_handler(NotificationType.IN_APP, self._handle_in_app)
        self.queue.register_handler(NotificationType.WEBHOOK, self._handle_webhook)
    
    def _handle_email(self, notification: Notification) -> Dict[str, Any]:
        """Handle email notification."""
        if not notification.recipient.email:
            return {'success': False, 'error': 'No email address'}
        
        return self.email_service.send_email(
            to_email=notification.recipient.email,
            subject=notification.subject,
            body=notification.body
        )
    
    def _handle_in_app(self, notification: Notification) -> Dict[str, Any]:
        """Handle in-app notification (store for later retrieval)."""
        # In a real implementation, this would store to database
        self._notification_log.append(notification)
        return {'success': True}
    
    def _handle_webhook(self, notification: Notification) -> Dict[str, Any]:
        """Handle webhook notification."""
        webhook_url = notification.metadata.get('webhook_url')
        if not webhook_url:
            return {'success': False, 'error': 'No webhook URL'}
        
        # In a real implementation, this would make HTTP request
        logger.info(f"Would send webhook to {webhook_url}")
        return {'success': True}
    
    def start(self):
        """Start notification processing."""
        self.queue.start()
    
    def stop(self):
        """Stop notification processing."""
        self.queue.stop()
        self.email_service.close_connection()
    
    def send_notification(
        self,
        recipient: NotificationRecipient,
        notification_type: NotificationType,
        subject: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Dict = None,
        schedule_at: datetime = None
    ) -> Notification:
        """
        Send a notification.
        
        Args:
            recipient: Notification recipient
            notification_type: Type of notification
            subject: Notification subject
            body: Notification body
            priority: Priority level
            metadata: Additional metadata
            schedule_at: Optional scheduled time
            
        Returns:
            Created notification
        """
        # Check recipient preferences
        if not recipient.can_receive(notification_type):
            logger.info(f"Recipient {recipient.id} opted out of {notification_type.value}")
            return None
        
        notification = Notification(
            id=self._generate_id(),
            type=notification_type,
            priority=priority,
            subject=subject,
            body=body,
            recipient=recipient,
            metadata=metadata or {},
            scheduled_at=schedule_at
        )
        
        if schedule_at and schedule_at > datetime.now():
            # Schedule for later
            notification.status = NotificationStatus.PENDING
            self._schedule_notification(notification)
        else:
            # Queue immediately
            self.queue.enqueue(notification)
        
        self._notification_log.append(notification)
        return notification
    
    def send_attendance_notification(
        self,
        student_id: str,
        student_name: str,
        email: str,
        attendance_data: Dict[str, Any]
    ) -> Notification:
        """
        Send attendance marked notification.
        
        Args:
            student_id: Student ID
            student_name: Student name
            email: Student email
            attendance_data: Attendance details
            
        Returns:
            Notification
        """
        recipient = NotificationRecipient(
            id=student_id,
            name=student_name,
            email=email
        )
        
        rendered = EmailTemplates.render_template(
            'attendance_marked',
            student_name=student_name,
            date=attendance_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            time=attendance_data.get('time', datetime.now().strftime('%H:%M:%S')),
            status=attendance_data.get('status', 'Present'),
            session_name=attendance_data.get('session_name', 'General Session')
        )
        
        return self.send_notification(
            recipient=recipient,
            notification_type=NotificationType.EMAIL,
            subject=rendered['subject'],
            body=rendered['body'],
            metadata=attendance_data
        )
    
    def send_low_attendance_alert(
        self,
        student_id: str,
        student_name: str,
        email: str,
        attendance_rate: float,
        required_rate: float = 75.0,
        sessions_attended: int = 0,
        total_sessions: int = 0
    ) -> Notification:
        """
        Send low attendance warning.
        
        Args:
            student_id: Student ID
            student_name: Student name
            email: Student email
            attendance_rate: Current attendance rate
            required_rate: Required minimum rate
            sessions_attended: Sessions attended count
            total_sessions: Total sessions count
            
        Returns:
            Notification
        """
        recipient = NotificationRecipient(
            id=student_id,
            name=student_name,
            email=email
        )
        
        rendered = EmailTemplates.render_template(
            'low_attendance_warning',
            student_name=student_name,
            attendance_rate=f"{attendance_rate:.1f}",
            required_rate=f"{required_rate:.1f}",
            sessions_attended=sessions_attended,
            total_sessions=total_sessions
        )
        
        return self.send_notification(
            recipient=recipient,
            notification_type=NotificationType.EMAIL,
            subject=rendered['subject'],
            body=rendered['body'],
            priority=NotificationPriority.HIGH,
            metadata={
                'alert_type': 'low_attendance',
                'attendance_rate': attendance_rate
            }
        )
    
    def send_daily_summary(
        self,
        admin_email: str,
        admin_name: str,
        summary_data: Dict[str, Any]
    ) -> Notification:
        """
        Send daily attendance summary to admin.
        
        Args:
            admin_email: Admin email
            admin_name: Admin name
            summary_data: Summary data dictionary
            
        Returns:
            Notification
        """
        recipient = NotificationRecipient(
            id='admin',
            name=admin_name,
            email=admin_email
        )
        
        # Format department breakdown
        dept_breakdown = ""
        for dept, data in summary_data.get('departments', {}).items():
            dept_breakdown += f"  - {dept}: {data.get('present', 0)} present, {data.get('absent', 0)} absent\n"
        
        # Format alerts
        alerts = "\n".join(f"  - {alert}" for alert in summary_data.get('alerts', ['No alerts']))
        
        rendered = EmailTemplates.render_template(
            'admin_daily_summary',
            date=summary_data.get('date', datetime.now().strftime('%Y-%m-%d')),
            total_students=summary_data.get('total_students', 0),
            present_count=summary_data.get('present_count', 0),
            present_rate=summary_data.get('present_rate', 0),
            late_count=summary_data.get('late_count', 0),
            late_rate=summary_data.get('late_rate', 0),
            absent_count=summary_data.get('absent_count', 0),
            absent_rate=summary_data.get('absent_rate', 0),
            department_breakdown=dept_breakdown or "  No department data available",
            alerts=alerts
        )
        
        return self.send_notification(
            recipient=recipient,
            notification_type=NotificationType.EMAIL,
            subject=rendered['subject'],
            body=rendered['body'],
            priority=NotificationPriority.NORMAL
        )
    
    def subscribe(self, topic: str, recipient: NotificationRecipient):
        """
        Subscribe recipient to notification topic.
        
        Args:
            topic: Topic name
            recipient: Notification recipient
        """
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        
        # Avoid duplicates
        if not any(r.id == recipient.id for r in self._subscribers[topic]):
            self._subscribers[topic].append(recipient)
            logger.info(f"Recipient {recipient.id} subscribed to {topic}")
    
    def unsubscribe(self, topic: str, recipient_id: str):
        """
        Unsubscribe recipient from topic.
        
        Args:
            topic: Topic name
            recipient_id: Recipient ID
        """
        if topic in self._subscribers:
            self._subscribers[topic] = [
                r for r in self._subscribers[topic] if r.id != recipient_id
            ]
            logger.info(f"Recipient {recipient_id} unsubscribed from {topic}")
    
    def broadcast(
        self,
        topic: str,
        notification_type: NotificationType,
        subject: str,
        body: str,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[Notification]:
        """
        Broadcast notification to all topic subscribers.
        
        Args:
            topic: Topic name
            notification_type: Type of notification
            subject: Notification subject
            body: Notification body
            priority: Priority level
            
        Returns:
            List of created notifications
        """
        notifications = []
        subscribers = self._subscribers.get(topic, [])
        
        for recipient in subscribers:
            notification = self.send_notification(
                recipient=recipient,
                notification_type=notification_type,
                subject=subject,
                body=body,
                priority=priority,
                metadata={'broadcast_topic': topic}
            )
            if notification:
                notifications.append(notification)
        
        logger.info(f"Broadcast {len(notifications)} notifications to topic {topic}")
        return notifications
    
    def _generate_id(self) -> str:
        """Generate unique notification ID."""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(f"{timestamp}-{len(self._notification_log)}".encode()).hexdigest()[:12]
    
    def _schedule_notification(self, notification: Notification):
        """Schedule notification for later delivery."""
        # In a real implementation, this would use a task scheduler
        logger.info(f"Notification {notification.id} scheduled for {notification.scheduled_at}")
    
    def get_notification_history(
        self,
        recipient_id: str = None,
        notification_type: NotificationType = None,
        status: NotificationStatus = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get notification history with optional filters.
        
        Args:
            recipient_id: Filter by recipient
            notification_type: Filter by type
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of notification dictionaries
        """
        filtered = self._notification_log
        
        if recipient_id:
            filtered = [n for n in filtered if n.recipient.id == recipient_id]
        
        if notification_type:
            filtered = [n for n in filtered if n.type == notification_type]
        
        if status:
            filtered = [n for n in filtered if n.status == status]
        
        # Sort by created_at descending
        filtered.sort(key=lambda n: n.created_at, reverse=True)
        
        return [n.to_dict() for n in filtered[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification statistics."""
        total = len(self._notification_log)
        by_status = {}
        by_type = {}
        
        for notification in self._notification_log:
            status = notification.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            n_type = notification.type.value
            by_type[n_type] = by_type.get(n_type, 0) + 1
        
        return {
            'total_notifications': total,
            'by_status': by_status,
            'by_type': by_type,
            'queue_stats': self.queue.get_stats(),
            'subscribers': {topic: len(subs) for topic, subs in self._subscribers.items()}
        }


# Convenience functions

def send_email(
    to: str,
    subject: str,
    body: str,
    config: Dict = None
) -> Dict[str, Any]:
    """
    Quick function to send an email.
    
    Args:
        to: Recipient email
        subject: Email subject
        body: Email body
        config: Optional email configuration
        
    Returns:
        Send result
    """
    service = EmailService(config)
    result = service.send_email(to, subject, body)
    service.close_connection()
    return result


def send_template_email(
    to: str,
    template_name: str,
    template_vars: Dict,
    config: Dict = None
) -> Dict[str, Any]:
    """
    Quick function to send template email.
    
    Args:
        to: Recipient email
        template_name: Template name
        template_vars: Template variables
        config: Optional email configuration
        
    Returns:
        Send result
    """
    service = EmailService(config)
    result = service.send_template_email(to, template_name, template_vars)
    service.close_connection()
    return result


if __name__ == '__main__':
    print("=== Notification Service Demo ===")
    
    # List available templates
    print("\nAvailable email templates:")
    for template in EmailTemplates.list_templates():
        print(f"  - {template}")
    
    # Demo template rendering
    print("\nRendering 'attendance_marked' template:")
    rendered = EmailTemplates.render_template(
        'attendance_marked',
        student_name='John Doe',
        date='2026-01-06',
        time='09:00:00',
        status='Present',
        session_name='Morning Session'
    )
    if rendered:
        print(f"Subject: {rendered['subject']}")
        print(f"Body preview: {rendered['body'][:100]}...")
    
    # Demo notification manager
    print("\nInitializing notification manager...")
    manager = NotificationManager()
    
    print(f"\nNotification stats: {manager.get_stats()}")
    
    print("\nNotification service ready!")
