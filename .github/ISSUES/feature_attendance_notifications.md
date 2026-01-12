---
name: Feature Request
about: Suggest a new feature
title: '[FEATURE] Automated Attendance Notifications for Parents/Guardians'
labels: enhancement
assignees: ''
---

## Feature Description

Implement an **automated notification system** that sends alerts to parents/guardians and students about attendance-related events. The system should support multiple notification channels (Email and SMS) and provide configurable triggers for different attendance scenarios.

### Key Capabilities
- 📧 **Email Notifications** via SMTP or third-party providers (e.g., SendGrid)
- 📱 **SMS Notifications** via Twilio or similar services
- ⚙️ **Configurable** thresholds and notification preferences
- 📊 **Notification History** for audit and tracking purposes

---

## Problem it Solves

Currently, the Smart Attendance System marks attendance automatically but lacks a mechanism to inform stakeholders about attendance issues. This creates several problems:

| Problem | Impact |
|---------|--------|
| **Delayed awareness** | Parents only learn about absences at parent-teacher meetings or report cards |
| **No early intervention** | Low attendance patterns go unnoticed until it's too late |
| **Manual follow-up** | Teachers must manually contact parents about absences |
| **Lack of transparency** | Students may not realize the severity of their attendance issues |

This feature directly aligns with the project's core goals:
- ✅ **Transparency over confusion** – stakeholders stay informed
- ✅ **Accountability** – automatic notifications ensure nothing slips through

---

## Proposed Solution

### Notification Triggers
1. **Absence Alert** – Notify when a student is marked absent
2. **Low Attendance Warning** – Alert when attendance falls below threshold (default: 75%)
3. **Leave Status Update** – Notify when leave request is approved/rejected
4. **Weekly/Monthly Summary** – Scheduled attendance reports

### Technical Implementation

#### 1. Database Changes
```sql
-- New tables required
CREATE TABLE notification_preferences (
    id INTEGER PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    email_enabled BOOLEAN DEFAULT TRUE,
    sms_enabled BOOLEAN DEFAULT FALSE,
    parent_email VARCHAR(255),
    parent_phone VARCHAR(20),
    low_attendance_threshold FLOAT DEFAULT 75.0
);

CREATE TABLE notification_log (
    id INTEGER PRIMARY KEY,
    student_id INTEGER REFERENCES students(id),
    notification_type VARCHAR(50),
    channel VARCHAR(20),  -- 'email' or 'sms'
    recipient VARCHAR(255),
    message TEXT,
    status VARCHAR(20),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. New Modules
- `src/notifications/email_service.py` – Email sending logic
- `src/notifications/sms_service.py` – SMS sending logic
- `src/notifications/notification_manager.py` – Orchestrates notifications

#### 3. Configuration
```python
# config.py additions
NOTIFICATIONS = {
    'EMAIL_ENABLED': True,
    'SMS_ENABLED': False,
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': 587,
    'SENDER_EMAIL': os.getenv('NOTIFICATION_EMAIL'),
    'TWILIO_ACCOUNT_SID': os.getenv('TWILIO_SID'),
    'TWILIO_AUTH_TOKEN': os.getenv('TWILIO_TOKEN'),
    'LOW_ATTENDANCE_THRESHOLD': 75.0
}
```

#### 4. UI Components
- **Admin Settings Page** – Configure notification providers and defaults
- **Student Profile** – Add/edit parent contact details and preferences
- **Notification History** – View sent notifications with status

---

## Alternatives Considered

| Alternative | Pros | Cons |
|-------------|------|------|
| **Manual email only** | Simpler implementation | Not scalable, requires teacher effort |
| **Push notifications only** | No external dependencies | Requires mobile app (future roadmap) |
| **Third-party notification service** | Feature-rich | Additional cost, external dependency |

**Chosen approach**: Email + SMS with modular design allows future extension to push notifications when the mobile app is developed (per roadmap).

---

## Additional Context

### Roadmap Alignment
This feature supports the existing roadmap items:
- 🧾 **Audit Logs** – Notification history provides audit trail
- 📱 **Mobile App Integration** – Lays groundwork for push notifications

### Privacy Considerations
- All contact information should be stored securely
- Notifications should only be sent with consent
- Comply with data protection regulations (GDPR/local laws)

### Acceptance Criteria
- [ ] Parents receive email notification when student is marked absent
- [ ] Low attendance alerts trigger when attendance drops below threshold
- [ ] Leave request status updates are sent to students
- [ ] Admin can configure SMTP/Twilio credentials via environment variables
- [ ] Notification preferences can be set per student
- [ ] Notification history is viewable in admin dashboard
- [ ] Unit tests cover notification services with 80%+ coverage

### Mockup Reference
```
┌─────────────────────────────────────────────────────┐
│  NOTIFICATION SETTINGS                              │
├─────────────────────────────────────────────────────┤
│  Email Provider:  [SMTP ▼]                          │
│  SMTP Server:     [smtp.gmail.com          ]        │
│  Sender Email:    [attendance@school.edu   ]        │
│                                                     │
│  ☑ Enable absence alerts                            │
│  ☑ Enable low attendance warnings                   │
│  Low Attendance Threshold: [75] %                   │
│                                                     │
│  [Save Settings]                                    │
└─────────────────────────────────────────────────────┘
```
