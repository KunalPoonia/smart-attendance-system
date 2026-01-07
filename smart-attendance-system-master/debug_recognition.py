#!/usr/bin/env python3
"""
Debug script to test face recognition functionality
"""

import os
import sys
from face_recognition_enhanced import EnhancedFaceRecognition

def test_recognition():
    print("🔍 Testing Enhanced Face Recognition System...")
    
    # Initialize the system
    face_rec = EnhancedFaceRecognition()
    
    # Check system status
    stats = face_rec.get_recognition_stats()
    print(f"📊 System Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Check if we have any known faces
    print(f"\n👥 Known faces: {len(face_rec.known_faces)}")
    for student_id, data in face_rec.known_faces.items():
        print(f"   - {student_id}: {data['name']} ({len(data['images'])} samples)")
    
    # Check face labels
    print(f"\n🏷️  Face labels: {len(face_rec.face_labels)}")
    for label_id, info in face_rec.face_labels.items():
        print(f"   - Label {label_id}: {info['student_id']} ({info['name']})")
    
    print(f"\n✅ Training status: {face_rec.is_trained}")
    
    return face_rec

if __name__ == "__main__":
    test_recognition()