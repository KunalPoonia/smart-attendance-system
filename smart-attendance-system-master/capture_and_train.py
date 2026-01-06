#!/usr/bin/env python3
"""
Capture current face from camera and add to training
"""

import cv2
import os
from face_recognition_enhanced import EnhancedFaceRecognition

def capture_and_train():
    print("📷 Capturing face from camera for training...")
    
    # Initialize face recognition
    face_rec = EnhancedFaceRecognition()
    
    # Start camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Could not open camera")
        return
    
    print("📸 Position your face in front of the camera and press SPACE to capture, ESC to exit")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Show preview
        cv2.imshow('Face Capture - Press SPACE to capture, ESC to exit', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            # Save the captured frame
            timestamp = str(int(cv2.getTickCount()))
            image_path = f"student_images/captured_face_{timestamp}.jpg"
            cv2.imwrite(image_path, frame)
            print(f"📸 Captured image saved: {image_path}")
            
            # Add to face recognition system
            student_id = "12407649"  # Your existing student ID
            student_name = "Kunal Poonia"
            
            success, message = face_rec.add_student_face(student_id, student_name, image_path)
            if success:
                print(f"✅ {message}")
                print("🎯 Face training updated! Try the recognition again.")
            else:
                print(f"❌ {message}")
            
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    capture_and_train()