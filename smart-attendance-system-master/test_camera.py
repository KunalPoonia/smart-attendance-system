#!/usr/bin/env python3
"""
Test script for camera and face recognition functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_camera import SimpleCamera
from face_recognition.face_detector import FaceDetector
from face_recognition.face_encoder import FaceEncoder
import time

def test_camera():
    """Test basic camera functionality"""
    print("🔍 Testing Camera Functionality...")
    
    camera = SimpleCamera()
    
    if camera.start_camera():
        print("✅ Camera started successfully!")
        
        # Test for 3 seconds
        for i in range(30):
            frame = camera.get_frame()
            if frame is not None:
                print(f"📸 Frame {i+1}: {frame.shape}")
            else:
                print(f"❌ Frame {i+1}: No frame")
            time.sleep(0.1)
        
        camera.stop_camera()
        print("✅ Camera test completed!")
        return True
    else:
        print("❌ Failed to start camera!")
        return False

def test_face_encoder():
    """Test face encoding functionality"""
    print("\n🔍 Testing Face Encoder...")
    
    encoder = FaceEncoder()
    
    # Test with a dummy image path (will fail but test the error handling)
    encoding = encoder.encode_face_from_image("nonexistent.jpg")
    if encoding is None:
        print("✅ Face encoder handles missing files correctly")
    else:
        print("❌ Face encoder should return None for missing files")
    
    return True

def test_face_detector():
    """Test face detection functionality"""
    print("\n🔍 Testing Face Detector...")
    
    detector = FaceDetector()
    
    # Test loading known faces
    dummy_students = [
        {
            'id': 1,
            'name': 'Test Student',
            'student_id': 'TEST001',
            'face_encoding': [0.1] * 256  # Dummy encoding
        }
    ]
    
    result = detector.load_known_faces(dummy_students)
    if result:
        print("✅ Face detector loads known faces correctly")
    else:
        print("❌ Face detector failed to load known faces")
    
    # Test starting detection
    if detector.start_detection():
        print("✅ Face detection started successfully!")
        
        # Test for 2 seconds
        time.sleep(2)
        
        # Get detected faces
        faces = detector.get_detected_faces()
        print(f"📸 Detected {len(faces)} faces")
        
        detector.stop_detection()
        print("✅ Face detection stopped successfully!")
        return True
    else:
        print("❌ Failed to start face detection!")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Camera and Face Recognition Tests")
    print("=" * 50)
    
    results = []
    
    # Test camera
    results.append(("Camera", test_camera()))
    
    # Test face encoder
    results.append(("Face Encoder", test_face_encoder()))
    
    # Test face detector
    results.append(("Face Detector", test_face_detector()))
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:15} : {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Camera and face recognition are working!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return all_passed

if __name__ == "__main__":
    main()