# Project Structure

```
smart-attendance-system/
│
├── app.py                    # Main Flask application
├── app_simple.py             # Simplified version with OpenCV
├── app_minimal.py            # Minimal version without face recognition
├── config.py                 # Application configuration
├── requirements.txt          # Python dependencies
├── Dockerfile                # Docker configuration
│
├── src/                      # Source code modules
│   ├── __init__.py
│   ├── core/                 # Core functionality
│   │   ├── __init__.py
│   │   ├── simple_camera.py          # Camera operations
│   │   ├── face_detection_new.py     # Advanced face detection
│   │   ├── face_detection_opencv.py  # OpenCV face detection
│   │   ├── face_recognition_enhanced.py
│   │   ├── face_recognition_fallback.py
│   │   ├── face_recognition_opencv_simple.py
│   │   └── face_recognition_simple.py
│   │
│   ├── database/             # Database models
│   │   ├── __init__.py
│   │   └── models.py         # SQLAlchemy models
│   │
│   ├── face_recognition/     # Face recognition module
│   │   ├── __init__.py
│   │   ├── face_detector.py  # Face detection logic
│   │   └── face_encoder.py   # Face encoding logic
│   │
│   └── utils/                # Utility functions
│       ├── __init__.py
│       └── helpers.py        # Helper functions
│
├── scripts/                  # Utility scripts
│   ├── setup.py              # Setup script
│   ├── setup_face_recognition.py
│   ├── install_requirements.py
│   ├── install_enhanced_requirements.py
│   ├── download_models.py    # Download ML models
│   ├── migrate_db.py         # Database migrations
│   ├── migrate_leave_management.py
│   ├── migrate_to_enhanced.py
│   ├── capture_and_train.py  # Training utility
│   ├── debug_recognition.py  # Debug utility
│   ├── check_students.py     # Student check utility
│   └── quick_test.py         # Quick test script
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html             # Base template
│   ├── index.html            # Dashboard
│   ├── students.html         # Student management
│   ├── attendance.html       # Attendance records
│   ├── mark_attendance.html  # Mark attendance
│   ├── register_student.html # Register student
│   ├── leave_management.html # Leave management
│   ├── reports.html          # Reports
│   └── *_clean.html          # Modern UI templates
│
├── static/                   # Static assets
│   ├── css/                  # Stylesheets
│   ├── js/                   # JavaScript files
│   ├── images/               # Images
│   └── swagger.yaml          # API documentation
│
├── tests/                    # Test files
│   ├── __init__.py
│   ├── test_*.py             # Test modules
│   └── ...
│
├── docs/                     # Documentation
│   ├── STRUCTURE.md          # This file
│   ├── DEPLOYMENT_GUIDE.md   # Deployment instructions
│   ├── CONTRIBUTING.md       # Contribution guidelines
│   ├── WORKFLOW_DIAGRAM.md   # System workflow
│   └── ...
│
├── .github/                  # GitHub configuration
│   ├── workflows/            # CI/CD workflows
│   ├── ISSUE_TEMPLATE/       # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
├── models/                   # ML model files (gitignored)
├── face_data/                # Face data (gitignored)
├── student_images/           # Student photos (gitignored)
├── exports/                  # Export files (gitignored)
├── logs/                     # Log files (gitignored)
└── instance/                 # Instance data (gitignored)
```

## Module Descriptions

### `src/core/`
Core functionality modules for camera operations and face detection/recognition.

### `src/database/`
SQLAlchemy database models for Student, AttendanceRecord, LeaveRequest, etc.

### `src/face_recognition/`
High-level face recognition module with encoder and detector classes.

### `src/utils/`
Utility functions for file handling, exports, validation, etc.

### `scripts/`
Standalone scripts for setup, migration, and maintenance tasks.

### `tests/`
Unit and integration tests for the application.

### `docs/`
Project documentation and guides.
