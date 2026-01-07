#!/usr/bin/env python3
"""
Simple test to check if face detection is working
"""

import cv2
import numpy as np
from face_recognition_enhanced import EnhancedFaceRecognition

def test_detection():
    print("🔍 Testing face detection...")
    
    # Initialize the system
    face_rec = EnhancedFaceRecognition()
    
    # Create a simple test frame (black image)
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    try:
        # Test detection on empty frame
        faces = face_rec.detect_faces_enhanced(test_frame)
        print(f"✅ Detection works - found {len(faces)} faces in empty frame")
        
        # Test with camera
        print("📷 Testing camera access...")
        success, message = face_rec.start_detection()
        if success:
            print(f"✅ {message}")
            
            # Wait a moment for detection to start
            import time
            time.sleep(2)
            
            # Check if frames are being captured
            frame = face_rec.get_current_frame_with_annotations()
            if frame is not None:
                print("✅ Camera frames are being captured")
                
                # Check detected faces
                detected = face_rec.get_detected_faces()
                print(f"📊 Currently detected faces: {len(detected)}")
                
            else:
                print("❌ No camera frames available")
            
            # Stop detection
            face_rec.stop_detection()
            print("🛑 Detection stopped")
            
        else:
            print(f"❌ Camera error: {message}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_detection()