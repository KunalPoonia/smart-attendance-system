#!/usr/bin/env python3
"""
Test script for face recognition system
"""

import sys
import os

def test_face_recognition():
    print("🧪 Testing Face Recognition System...")
    print("=" * 50)
    
    # Test 1: Try importing face_recognition library
    print("📦 Testing face_recognition library...")
    try:
        import face_recognition
        print("✅ face_recognition library available")
        
        # Test basic functionality
        import numpy as np
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        try:
            encodings = face_recognition.face_encodings(test_image)
            print(f"✅ face_recognition basic test passed (found {len(encodings)} faces in test image)")
        except Exception as e:
            print(f"⚠️  face_recognition library has issues: {e}")
            print("🔄 Will use fallback system...")
        
        from face_recognition_simple import SimpleFaceRecognition
        face_system = SimpleFaceRecognition()
        print("✅ SimpleFaceRecognition system initialized")
        
        return "advanced"
        
    except ImportError as e:
        print(f"❌ face_recognition library not available: {e}")
        print("🔄 Falling back to OpenCV system...")
        
        # Test 2: Try fallback system
        try:
            import cv2
            from face_recognition_fallback import FallbackFaceRecognition
            face_system = FallbackFaceRecognition()
            print("✅ FallbackFaceRecognition system initialized")
            return "fallback"
            
        except ImportError as e:
            print(f"❌ Fallback system also failed: {e}")
            return "none"
    
    except Exception as e:
        print(f"❌ Error testing face recognition: {e}")
        return "error"

def test_camera():
    print("\n📹 Testing Camera Access...")
    print("-" * 30)
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ Camera access successful")
                print(f"📐 Frame size: {frame.shape}")
            else:
                print("❌ Could not read from camera")
            cap.release()
        else:
            print("❌ Could not open camera")
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")

def main():
    print("🚀 Smart Attendance System - Face Recognition Test")
    print("=" * 60)
    
    # Test face recognition
    face_result = test_face_recognition()
    
    # Test camera
    test_camera()
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 30)
    
    if face_result == "advanced":
        print("🎉 Advanced face recognition system available")
        print("   - Uses face_recognition library")
        print("   - High accuracy face detection and recognition")
        print("   - Recommended for production use")
        
    elif face_result == "fallback":
        print("⚠️  Fallback face recognition system available")
        print("   - Uses OpenCV LBPH recognizer")
        print("   - Basic face detection and recognition")
        print("   - Suitable for testing and development")
        
    elif face_result == "none":
        print("❌ No face recognition system available")
        print("   - Install required dependencies")
        print("   - Run: python install_requirements.py")
        
    else:
        print("❌ Face recognition system error")
        print("   - Check dependencies and installation")
    
    print("\n💡 Next Steps:")
    if face_result in ["advanced", "fallback"]:
        print("   1. Run: python app_simple.py")
        print("   2. Open browser to http://127.0.0.1:5000")
        print("   3. Register students with photos")
        print("   4. Test face recognition in Mark Attendance")
    else:
        print("   1. Install dependencies: python install_requirements.py")
        print("   2. Re-run this test: python test_face_recognition.py")

if __name__ == "__main__":
    main()