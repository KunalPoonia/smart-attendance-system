#!/usr/bin/env python3
"""
Quick test to verify system functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_camera import SimpleCamera
from face_recognition.face_detector import FaceDetector
from face_recognition.face_encoder import FaceEncoder

def main():
    print("🔍 Quick System Test")
    print("=" * 30)
    
    # Test 1: Camera
    print("1. Testing Camera...")
    camera = SimpleCamera()
    if camera.start_camera():
        print("   ✅ Camera: Working")
        camera.stop_camera()
    else:
        print("   ❌ Camera: Failed")
    
    # Test 2: Face Encoder
    print("2. Testing Face Encoder...")
    encoder = FaceEncoder()
    if encoder.face_cascade is not None:
        print("   ✅ Face Encoder: Working")
    else:
        print("   ❌ Face Encoder: Failed")
    
    # Test 3: Face Detector
    print("3. Testing Face Detector...")
    detector = FaceDetector()
    if detector.face_cascade is not None:
        print("   ✅ Face Detector: Working")
    else:
        print("   ❌ Face Detector: Failed")
    
    print("\n🎉 Quick test completed!")
    print("✨ You can now start the main app with: python app.py")

if __name__ == "__main__":
    main()