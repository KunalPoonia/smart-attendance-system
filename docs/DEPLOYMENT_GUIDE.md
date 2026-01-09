# Smart Attendance System - Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Maintenance](#maintenance)

## System Requirements

### Minimum Hardware Requirements
- **CPU**: Intel i3 or AMD equivalent (2.0 GHz+)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB free space
- **Camera**: USB webcam or built-in camera (720p minimum)
- **Network**: Ethernet or Wi-Fi connection

### Recommended Hardware Requirements
- **CPU**: Intel i5 or AMD equivalent (2.5 GHz+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 20GB+ SSD storage
- **Camera**: HD webcam (1080p) with good low-light performance
- **Network**: Stable broadband connection (10 Mbps+)

### Software Requirements
- **Operating System**: Windows 10/11, macOS 10.14+, or Ubuntu 18.04+
- **Python**: 3.8 or higher
- **Browser**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

## Local Development Setup

### Step 1: Install Python and Dependencies

#### Windows
```cmd
# Download Python from python.org (3.8+)
# Ensure Python is added to PATH during installation

# Verify installation
python --version
pip --version
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.9

# Verify installation
python3 --version
pip3 --version
```

#### Ubuntu/Linux
```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3 python3-pip python3-venv

# Install additional dependencies
sudo apt install python3-dev build-essential cmake

# Verify installation
python3 --version
pip3 --version
```

### Step 2: Clone and Setup Project

```bash
# Clone the repository (or extract from zip)
git clone <repository-url>
cd smart_attendance_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# If you encounter issues with dlib on Windows:
pip install cmake
pip install dlib

# Alternative for Windows (pre-compiled wheel):
pip install https://github.com/jloh02/dlib/releases/download/v19.22/dlib-19.22.99-cp39-cp39-win_amd64.whl
```

### Step 4: Database Setup

```bash
# Initialize database
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
"
```

### Step 5: Run the Application

```bash
# Start the development server
python app.py

# The application will be available at:
# http://localhost:5000
```

## Production Deployment

### Option 1: Using Gunicorn (Linux/macOS)

#### Install Gunicorn
```bash
pip install gunicorn
```

#### Create Gunicorn Configuration
```python
# gunicorn_config.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

#### Run with Gunicorn
```bash
gunicorn --config gunicorn_config.py app:app
```

### Option 2: Using Waitress (Windows)

#### Install Waitress
```bash
pip install waitress
```

#### Run with Waitress
```bash
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

### Option 3: Using Docker

#### Create Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/uploads student_images exports logs database

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

#### Build and Run Docker Container
```bash
# Build the image
docker build -t smart-attendance-system .

# Run the container
docker run -d \
  --name attendance-system \
  -p 5000:5000 \
  -v $(pwd)/database:/app/database \
  -v $(pwd)/student_images:/app/student_images \
  -v $(pwd)/exports:/app/exports \
  smart-attendance-system
```

## Cloud Deployment

### AWS Deployment

#### Using AWS EC2

1. **Launch EC2 Instance**
```bash
# Choose Ubuntu 20.04 LTS
# Instance type: t3.medium or larger
# Configure security group to allow HTTP (80) and HTTPS (443)
```

2. **Setup Instance**
```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3 python3-pip python3-venv nginx -y

# Clone your project
git clone <your-repo-url>
cd smart_attendance_system

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Configure Nginx**
```nginx
# /etc/nginx/sites-available/attendance-system
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

4. **Enable Site**
```bash
sudo ln -s /etc/nginx/sites-available/attendance-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

5. **Create Systemd Service**
```ini
# /etc/systemd/system/attendance-system.service
[Unit]
Description=Smart Attendance System
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/smart_attendance_system
Environment=PATH=/home/ubuntu/smart_attendance_system/venv/bin
ExecStart=/home/ubuntu/smart_attendance_system/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

6. **Start Service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable attendance-system
sudo systemctl start attendance-system
```

#### Using AWS Elastic Beanstalk

1. **Install EB CLI**
```bash
pip install awsebcli
```

2. **Initialize EB Application**
```bash
eb init smart-attendance-system
```

3. **Create Environment**
```bash
eb create production
```

4. **Deploy**
```bash
eb deploy
```

### Heroku Deployment

1. **Install Heroku CLI**
```bash
# Download from heroku.com/cli
```

2. **Prepare Application**
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Create runtime.txt
echo "python-3.9.7" > runtime.txt
```

3. **Deploy to Heroku**
```bash
heroku login
heroku create your-app-name
git add .
git commit -m "Initial deployment"
git push heroku main
```

### Google Cloud Platform (GCP)

#### Using Google App Engine

1. **Create app.yaml**
```yaml
runtime: python39

env_variables:
  FLASK_ENV: production

automatic_scaling:
  min_instances: 1
  max_instances: 10
```

2. **Deploy**
```bash
gcloud app deploy
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# .env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///database/attendance.db
FLASK_ENV=production
FACE_RECOGNITION_TOLERANCE=0.6
CAMERA_INDEX=0
```

### Production Configuration

```python
# config.py - Production settings
import os

class ProductionConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database/attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Face recognition settings
    FACE_RECOGNITION_TOLERANCE = 0.6
    FACE_DETECTION_MODEL = 'hog'
```

### Database Configuration

#### SQLite (Default)
```python
SQLALCHEMY_DATABASE_URI = 'sqlite:///database/attendance.db'
```

#### PostgreSQL
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://username:password@localhost/attendance_db'
```

#### MySQL
```python
SQLALCHEMY_DATABASE_URI = 'mysql://username:password@localhost/attendance_db'
```

## SSL/HTTPS Setup

### Using Let's Encrypt (Free SSL)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx HTTPS Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## Troubleshooting

### Common Issues

#### 1. Camera Not Working
```bash
# Check camera permissions
ls /dev/video*

# Test camera
python -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
print('Camera working:', ret)
cap.release()
"
```

#### 2. Face Recognition Library Issues
```bash
# Windows: Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# macOS: Install Xcode Command Line Tools
xcode-select --install

# Linux: Install build dependencies
sudo apt install build-essential cmake libopenblas-dev liblapack-dev
```

#### 3. Database Connection Issues
```bash
# Check database file permissions
ls -la database/

# Reset database
rm database/attendance.db
python -c "
from app import app, db
with app.app_context():
    db.create_all()
"
```

#### 4. Memory Issues
```bash
# Monitor memory usage
htop

# Optimize Python memory
export PYTHONOPTIMIZE=1

# Reduce face recognition model size
# Use 'hog' instead of 'cnn' for face detection
```

### Performance Optimization

#### 1. Database Optimization
```sql
-- Create indexes for better performance
CREATE INDEX idx_attendance_date ON attendance_records(date);
CREATE INDEX idx_attendance_student ON attendance_records(student_id);
CREATE INDEX idx_student_active ON students(is_active);
```

#### 2. Caching
```python
# Install Redis for caching
pip install redis flask-caching

# Configure caching in app.py
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})
```

#### 3. Image Optimization
```python
# Optimize uploaded images
from PIL import Image

def optimize_image(image_path, max_size=(800, 600), quality=85):
    with Image.open(image_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(image_path, optimize=True, quality=quality)
```

## Maintenance

### Regular Maintenance Tasks

#### 1. Database Backup
```bash
#!/bin/bash
# backup_db.sh
DATE=$(date +%Y%m%d_%H%M%S)
cp database/attendance.db backups/attendance_${DATE}.db
find backups/ -name "*.db" -mtime +30 -delete
```

#### 2. Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/attendance-system

# Content:
/path/to/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 ubuntu ubuntu
}
```

#### 3. System Updates
```bash
#!/bin/bash
# update_system.sh
sudo apt update && sudo apt upgrade -y
pip install --upgrade -r requirements.txt
sudo systemctl restart attendance-system
```

#### 4. Monitoring Script
```python
# monitor.py
import psutil
import requests
import smtplib
from datetime import datetime

def check_system_health():
    # Check CPU usage
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Check memory usage
    memory = psutil.virtual_memory()
    
    # Check disk usage
    disk = psutil.disk_usage('/')
    
    # Check application response
    try:
        response = requests.get('http://localhost:5000', timeout=10)
        app_status = response.status_code == 200
    except:
        app_status = False
    
    # Alert if issues found
    if cpu_percent > 80 or memory.percent > 80 or disk.percent > 90 or not app_status:
        send_alert(f"System health check failed at {datetime.now()}")

def send_alert(message):
    # Implement email/SMS alerting
    pass

if __name__ == "__main__":
    check_system_health()
```

### Security Maintenance

#### 1. Update Dependencies
```bash
# Check for security vulnerabilities
pip audit

# Update packages
pip install --upgrade -r requirements.txt
```

#### 2. Security Headers
```python
# Add security headers in app.py
from flask_talisman import Talisman

Talisman(app, force_https=True)

@app.after_request
def after_request(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

#### 3. Firewall Configuration
```bash
# Ubuntu UFW
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw deny 5000  # Block direct access to Flask
```

This deployment guide provides comprehensive instructions for setting up the Smart Attendance System in various environments, from local development to production cloud deployments. Follow the appropriate sections based on your deployment needs and infrastructure requirements.