#!/usr/bin/env python3
"""
Smart Attendance System - Setup Script
This script helps set up the Smart Attendance System for development or production use.
"""

import os
import sys
import subprocess
import platform
import sqlite3
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("    Smart Attendance System - Setup Script")
    print("    B.Tech Project - Face Recognition Attendance")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def check_system_dependencies():
    """Check system-specific dependencies"""
    print("\n🔍 Checking system dependencies...")
    
    system = platform.system().lower()
    
    if system == "linux":
        # Check for required packages on Linux
        required_packages = ["python3-dev", "build-essential", "cmake"]
        missing_packages = []
        
        for package in required_packages:
            result = subprocess.run(
                ["dpkg", "-l", package], 
                capture_output=True, 
                text=True
            )
            if result.returncode != 0:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"⚠️  Missing system packages: {', '.join(missing_packages)}")
            print("   Please install them using:")
            print(f"   sudo apt install {' '.join(missing_packages)}")
            return False
    
    elif system == "darwin":  # macOS
        # Check for Xcode Command Line Tools
        result = subprocess.run(
            ["xcode-select", "-p"], 
            capture_output=True, 
            text=True
        )
        if result.returncode != 0:
            print("⚠️  Xcode Command Line Tools not found")
            print("   Please install them using: xcode-select --install")
            return False
    
    print("✅ System dependencies - OK")
    return True

def create_virtual_environment():
    """Create Python virtual environment"""
    print("\n🔧 Setting up virtual environment...")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print("✅ Virtual environment already exists")
        return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False

def get_pip_command():
    """Get the appropriate pip command for the current system"""
    system = platform.system().lower()
    
    if system == "windows":
        return os.path.join("venv", "Scripts", "pip")
    else:
        return os.path.join("venv", "bin", "pip")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    
    pip_cmd = get_pip_command()
    
    # Upgrade pip first
    try:
        subprocess.run([pip_cmd, "install", "--upgrade", "pip"], check=True)
        print("✅ pip upgraded successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Failed to upgrade pip: {e}")
    
    # Install requirements
    try:
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        
        # Try installing dlib separately for Windows
        if platform.system().lower() == "windows":
            print("\n🔧 Attempting to install dlib for Windows...")
            try:
                subprocess.run([pip_cmd, "install", "cmake"], check=True)
                subprocess.run([pip_cmd, "install", "dlib"], check=True)
                subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
                print("✅ Dependencies installed successfully (with dlib fix)")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install dlib. Please install Visual Studio Build Tools")
                print("   Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/")
                return False
        
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating project directories...")
    
    directories = [
        "static/uploads",
        "static/css",
        "static/js",
        "static/images",
        "student_images",
        "exports",
        "database",
        "logs",
        "backups"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created successfully")

def initialize_database():
    """Initialize the SQLite database"""
    print("\n🗄️  Initializing database...")
    
    try:
        # Create database file
        db_path = Path("database/attendance.db")
        
        # Import and initialize database
        sys.path.insert(0, os.getcwd())
        
        # Set environment variable to avoid Flask app running
        os.environ['FLASK_ENV'] = 'setup'
        
        from database.models import db, Student, AttendanceRecord, AttendanceSession
        from flask import Flask
        from config import Config
        
        app = Flask(__name__)
        app.config.from_object(Config)
        
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
        
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False

def create_sample_config():
    """Create sample configuration files"""
    print("\n⚙️  Creating configuration files...")
    
    # Create .env.example if it doesn't exist
    env_example_content = """# Smart Attendance System Configuration
# Copy this file to .env and update the values

# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database Configuration
DATABASE_URL=sqlite:///database/attendance.db

# Face Recognition Configuration
FACE_RECOGNITION_TOLERANCE=0.6
FACE_DETECTION_MODEL=hog

# Camera Configuration
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480

# Upload Configuration
MAX_CONTENT_LENGTH=16777216

# Export Configuration
EXPORT_FOLDER=exports
"""
    
    with open(".env.example", "w") as f:
        f.write(env_example_content)
    
    # Create default .env file
    if not Path(".env").exists():
        with open(".env", "w") as f:
            f.write(env_example_content.replace("your-secret-key-here", "dev-secret-key-123"))
    
    print("✅ Configuration files created")

def test_installation():
    """Test if the installation is working"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        sys.path.insert(0, os.getcwd())
        
        import cv2
        import face_recognition
        import flask
        from database.models import db
        
        print("✅ All imports successful")
        
        # Test camera (optional)
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                print("✅ Camera test successful")
            else:
                print("⚠️  Camera test failed - check camera connection")
        except Exception as e:
            print(f"⚠️  Camera test failed: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Activate the virtual environment:")
    
    system = platform.system().lower()
    if system == "windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print()
    print("2. Start the application:")
    print("   python app.py")
    print()
    print("3. Open your browser and go to:")
    print("   http://localhost:5000")
    print()
    print("4. Register your first student and start using the system!")
    print()
    print("📚 Documentation:")
    print("   - README.md - General information")
    print("   - PROJECT_REPORT.md - Detailed project report")
    print("   - DEPLOYMENT_GUIDE.md - Production deployment")
    print("   - WORKFLOW_DIAGRAM.md - System workflow")
    print()
    print("🆘 Need help? Check the troubleshooting section in DEPLOYMENT_GUIDE.md")
    print()

def main():
    """Main setup function"""
    print_banner()
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    if not check_system_dependencies():
        print("\n⚠️  Please install missing system dependencies and run setup again")
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Creating virtual environment", create_virtual_environment),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Creating configuration", create_sample_config),
        ("Initializing database", initialize_database),
        ("Testing installation", test_installation)
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please check the error messages above and try again")
            sys.exit(1)
    
    print_next_steps()

if __name__ == "__main__":
    main()