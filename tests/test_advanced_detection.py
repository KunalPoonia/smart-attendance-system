#!/usr/bin/env python3
"""
Test script for Advanced Face Detection System
"""

import sys
import os
import cv2
import numpy as np

def test_opencv_installation():
    """Test OpenCV installation and features"""
    print("🔧 Testing OpenCV Installation...")
    print("-" * 40)
    
    try:
        import cv2
        print(f"✅ OpenCV version: {cv2.__version__}")
        
        # Test Haar cascades
        face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if os.path.exists(face_cascade_path):
            print("✅ Haar cascade face detector available")
        else:
            print("❌ Haar cascade face detector not found")
        
        # Test LBPH face recognizer
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            print("✅ LBPH face recognizer available")
        except AttributeError:
            print("❌ LBPH face recognizer not available (install opencv-contrib-python)")
            return False
        
        # Test DNN module
        try:
            net = cv2.dnn.readNet()  # Just test if dnn module exists
            print("✅ DNN module available")
        except:
            print("⚠️  DNN module not available")
        
        return True
        
    except ImportError as e:
        print(f"❌ OpenCV not available: {e}")
        return False

def test_camera_access():
    """Test camera access and basic functionality"""
    print("\n📹 Testing Camera Access...")
    print("-" * 40)
    
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Could not open camera")
            return False
        
        # Test frame capture
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read frame from camera")
            cap.release()
            return False
        
        print(f"✅ Camera access successful")
        print(f"📐 Frame size: {frame.shape}")
        
        # Test face detection on camera frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        print(f"🔍 Detected {len(faces)} faces in current frame")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def test_advanced_face_detection():
    """Test the advanced face detection system"""
    print("\n🎯 Testing Advanced Face Detection System...")
    print("-" * 50)
    
    try:
        from face_detection_new import AdvancedFaceDetection
        
        # Initialize system
        face_detector = AdvancedFaceDetection()
        print("✅ Advanced Face Detection System initialized")
        
        # Test system stats
        stats = face_detector.get_recognition_stats()
        print(f"📊 System Stats:")
        print(f"   - Detection method: {stats['detection_method']}")
        print(f"   - DNN available: {stats['has_dnn']}")
        print(f"   - Known students: {stats['total_students']}")
        print(f"   - Is trained: {stats['is_trained']}")
        
        # Test detection start/stop
        success, message = face_detector.start_detection()
        if success:
            print(f"✅ Detection started: {message}")
            
            # Let it run for a moment
            import time
            time.sleep(2)
            
            # Get detected faces
            detected_faces = face_detector.get_detected_faces()
            print(f"🔍 Currently detected faces: {len(detected_faces)}")
            
            # Stop detection
            success, message = face_detector.stop_detection()
            if success:
                print(f"✅ Detection stopped: {message}")
            else:
                print(f"❌ Failed to stop detection: {message}")
        else:
            print(f"❌ Failed to start detection: {message}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Advanced Face Detection not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Advanced Face Detection: {e}")
        return False

def test_dnn_models():
    """Test DNN model availability"""
    print("\n🧠 Testing DNN Models...")
    print("-" * 30)
    
    models_dir = "models"
    prototxt_path = os.path.join(models_dir, "deploy.prototxt")
    model_path = os.path.join(models_dir, "res10_300x300_ssd_iter_140000.caffemodel")
    
    if os.path.exists(prototxt_path) and os.path.exists(model_path):
        print("✅ DNN models found")
        
        try:
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("✅ DNN models loaded successfully")
            print("🎯 Enhanced face detection available")
            return True
        except Exception as e:
            print(f"❌ Failed to load DNN models: {e}")
            return False
    else:
        print("⚠️  DNN models not found")
        print("💡 Run 'python download_models.py' to download enhanced models")
        return False

def create_test_image():
    """Create a test image with a simple face-like pattern"""
    print("\n🖼️  Creating test image...")
    
    # Create a simple test image with a face-like pattern
    test_image = np.zeros((200, 200, 3), dtype=np.uint8)
    
    # Draw a simple face
    cv2.circle(test_image, (100, 100), 80, (200, 200, 200), -1)  # Face
    cv2.circle(test_image, (80, 80), 10, (0, 0, 0), -1)   # Left eye
    cv2.circle(test_image, (120, 80), 10, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(test_image, (100, 120), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    # Save test image
    cv2.imwrite("test_face.jpg", test_image)
    print("✅ Test image created: test_face.jpg")
    
    return "test_face.jpg"

def main():
    print("🚀 Advanced Face Detection System - Comprehensive Test")
    print("=" * 70)
    
    # Test results
    results = {
        'opencv': False,
        'camera': False,
        'advanced_detection': False,
        'dnn_models': False
    }
    
    # Run tests
    results['opencv'] = test_opencv_installation()
    
    if results['opencv']:
        results['camera'] = test_camera_access()
        results['advanced_detection'] = test_advanced_face_detection()
        results['dnn_models'] = test_dnn_models()
    
    # Create test image
    test_image_path = create_test_image()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 40)
    
    if results['opencv']:
        print("✅ OpenCV: Working")
    else:
        print("❌ OpenCV: Failed")
    
    if results['camera']:
        print("✅ Camera: Working")
    else:
        print("❌ Camera: Failed")
    
    if results['advanced_detection']:
        print("✅ Advanced Detection: Working")
    else:
        print("❌ Advanced Detection: Failed")
    
    if results['dnn_models']:
        print("✅ DNN Models: Available")
    else:
        print("⚠️  DNN Models: Not available (using Haar cascades)")
    
    # Overall status
    print("\n🎯 Overall Status:")
    if results['opencv'] and results['camera'] and results['advanced_detection']:
        print("🎉 Advanced Face Detection System is READY!")
        print("\n💡 Next Steps:")
        print("   1. Run: python app_simple.py")
        print("   2. Register students with photos")
        print("   3. Test face recognition in Mark Attendance")
        
        if not results['dnn_models']:
            print("\n🔧 Optional Enhancement:")
            print("   - Run: python download_models.py")
            print("   - This will enable DNN-based detection for better accuracy")
    else:
        print("❌ System not ready - please fix the failed components")
        
        if not results['opencv']:
            print("\n🔧 Fix OpenCV:")
            print("   pip install opencv-python opencv-contrib-python")
        
        if not results['camera']:
            print("\n🔧 Fix Camera:")
            print("   - Check camera permissions")
            print("   - Ensure camera is not used by other applications")
    
    # Cleanup
    if os.path.exists(test_image_path):
        os.remove(test_image_path)
        print(f"\n🧹 Cleaned up test image: {test_image_path}")

if __name__ == "__main__":
    main()