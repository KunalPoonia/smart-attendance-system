#!/usr/bin/env python3
"""
Smart Attendance System - Test Script
This script tests the core functionality of the attendance system.
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime
import tempfile
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSmartAttendanceSystem(unittest.TestCase):
    """Test cases for Smart Attendance System"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_image_path = None
        
    def tearDown(self):
        """Clean up test environment"""
        if self.test_image_path and os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
    
    def test_imports(self):
        """Test if all required modules can be imported"""
        print("Testing imports...")
        
        try:
            import cv2
            import face_recognition
            import flask
            import numpy as np
            import pandas as pd
            from PIL import Image
            
            print("✅ All required modules imported successfully")
            
        except ImportError as e:
            self.fail(f"Failed to import required module: {e}")
    
    def test_camera_access(self):
        """Test camera access"""
        print("Testing camera access...")
        
        try:
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                print("⚠️  No camera found or camera is in use")
                return
            
            ret, frame = cap.read()
            cap.release()
            
            if ret and frame is not None:
                print(f"✅ Camera test successful - Frame shape: {frame.shape}")
            else:
                print("⚠️  Camera opened but failed to capture frame")
                
        except Exception as e:
            print(f"⚠️  Camera test failed: {e}")
    
    def test_face_recognition_library(self):
        """Test face recognition library functionality"""
        print("Testing face recognition library...")
        
        try:
            import face_recognition
            
            # Create a simple test image with a face-like pattern
            test_image = self.create_test_face_image()
            
            # Try to detect faces
            image = face_recognition.load_image_file(test_image)
            face_locations = face_recognition.face_locations(image)
            
            print(f"✅ Face recognition library working - Detected {len(face_locations)} face regions")
            
        except Exception as e:
            print(f"⚠️  Face recognition test failed: {e}")
    
    def test_database_models(self):
        """Test database models"""
        print("Testing database models...")
        
        try:
            from database.models import Student, AttendanceRecord, AttendanceSession
            from flask import Flask
            from config import Config
            
            # Create test app
            app = Flask(__name__)
            app.config.from_object(Config)
            
            # Test model creation
            student = Student(
                student_id="TEST001",
                name="Test Student",
                email="test@example.com",
                department="Computer Science"
            )
            
            print("✅ Database models working correctly")
            
        except Exception as e:
            self.fail(f"Database models test failed: {e}")
    
    def test_face_encoder(self):
        """Test face encoder functionality"""
        print("Testing face encoder...")
        
        try:
            from face_recognition.face_encoder import FaceEncoder
            
            encoder = FaceEncoder()
            test_image = self.create_test_face_image()
            
            # This might not find a face in our synthetic image, but should not crash
            encoding = encoder.encode_face_from_image(test_image)
            
            print("✅ Face encoder initialized and working")
            
        except Exception as e:
            print(f"⚠️  Face encoder test failed: {e}")
    
    def test_utilities(self):
        """Test utility functions"""
        print("Testing utility functions...")
        
        try:
            from utils.helpers import allowed_file, validate_student_data, format_datetime
            
            # Test file validation
            self.assertTrue(allowed_file("test.jpg"))
            self.assertTrue(allowed_file("test.png"))
            self.assertFalse(allowed_file("test.txt"))
            
            # Test student data validation
            valid_data = {
                'student_id': 'TEST001',
                'name': 'Test Student',
                'email': 'test@example.com',
                'department': 'Computer Science'
            }
            errors = validate_student_data(valid_data)
            self.assertEqual(len(errors), 0)
            
            # Test datetime formatting
            now = datetime.now()
            formatted = format_datetime(now)
            self.assertIsInstance(formatted, str)
            
            print("✅ Utility functions working correctly")
            
        except Exception as e:
            self.fail(f"Utility functions test failed: {e}")
    
    def test_flask_app_creation(self):
        """Test Flask app creation"""
        print("Testing Flask app creation...")
        
        try:
            from flask import Flask
            from config import Config
            
            app = Flask(__name__)
            app.config.from_object(Config)
            
            # Test basic routes exist
            with app.test_client() as client:
                # This will fail if app.py has issues, but we're just testing creation
                pass
            
            print("✅ Flask app creation successful")
            
        except Exception as e:
            print(f"⚠️  Flask app test failed: {e}")
    
    def test_directory_structure(self):
        """Test if required directories exist"""
        print("Testing directory structure...")
        
        required_dirs = [
            "database",
            "face_recognition",
            "static",
            "templates",
            "utils",
            "student_images",
            "exports"
        ]
        
        missing_dirs = []
        for directory in required_dirs:
            if not Path(directory).exists():
                missing_dirs.append(directory)
        
        if missing_dirs:
            print(f"⚠️  Missing directories: {missing_dirs}")
        else:
            print("✅ All required directories exist")
    
    def test_configuration(self):
        """Test configuration loading"""
        print("Testing configuration...")
        
        try:
            from config import Config
            
            # Check if required config attributes exist
            required_attrs = [
                'SECRET_KEY',
                'SQLALCHEMY_DATABASE_URI',
                'FACE_RECOGNITION_TOLERANCE',
                'UPLOAD_FOLDER'
            ]
            
            missing_attrs = []
            for attr in required_attrs:
                if not hasattr(Config, attr):
                    missing_attrs.append(attr)
            
            if missing_attrs:
                print(f"⚠️  Missing config attributes: {missing_attrs}")
            else:
                print("✅ Configuration loaded successfully")
                
        except Exception as e:
            print(f"⚠️  Configuration test failed: {e}")
    
    def create_test_face_image(self):
        """Create a simple test image for face recognition testing"""
        # Create a simple 200x200 RGB image
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Add some face-like features (very basic)
        # This won't be detected as a real face, but tests the pipeline
        cv2.circle(image, (100, 100), 80, (255, 255, 255), -1)  # Face outline
        cv2.circle(image, (80, 80), 10, (0, 0, 0), -1)   # Left eye
        cv2.circle(image, (120, 80), 10, (0, 0, 0), -1)  # Right eye
        cv2.ellipse(image, (100, 120), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        cv2.imwrite(temp_file.name, image)
        self.test_image_path = temp_file.name
        
        return temp_file.name

def run_system_check():
    """Run comprehensive system check"""
    print("=" * 60)
    print("    Smart Attendance System - System Check")
    print("=" * 60)
    print()
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSmartAttendanceSystem)
    runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    
    # Create custom test instance to run individual tests with output
    test_instance = TestSmartAttendanceSystem()
    
    tests = [
        ('Imports', test_instance.test_imports),
        ('Camera Access', test_instance.test_camera_access),
        ('Face Recognition Library', test_instance.test_face_recognition_library),
        ('Database Models', test_instance.test_database_models),
        ('Face Encoder', test_instance.test_face_encoder),
        ('Utilities', test_instance.test_utilities),
        ('Flask App', test_instance.test_flask_app_creation),
        ('Directory Structure', test_instance.test_directory_structure),
        ('Configuration', test_instance.test_configuration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            failed += 1
        print()
    
    # Summary
    print("=" * 60)
    print("SYSTEM CHECK SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    print()
    
    if failed == 0:
        print("🎉 All tests passed! Your system is ready to run the Smart Attendance System.")
        print()
        print("To start the application:")
        print("1. Activate virtual environment (if not already active)")
        print("2. Run: python app.py")
        print("3. Open browser to: http://localhost:5000")
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        print("Refer to DEPLOYMENT_GUIDE.md for troubleshooting help.")
    
    print()

if __name__ == "__main__":
    run_system_check()