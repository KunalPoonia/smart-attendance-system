#!/usr/bin/env python3
"""
Migrate existing students to enhanced face recognition system
"""

import sqlite3
import os
from face_recognition_enhanced import EnhancedFaceRecognition

def migrate_students():
    print("🔄 Migrating students to enhanced face recognition...")
    
    # Connect to database
    conn = sqlite3.connect('instance/attendance.db')
    cursor = conn.cursor()
    
    # Get all students with images
    cursor.execute("SELECT student_id, name, image_path FROM student WHERE image_path IS NOT NULL")
    students = cursor.fetchall()
    
    print(f"📊 Found {len(students)} students with images")
    
    # Initialize enhanced face recognition
    face_rec = EnhancedFaceRecognition()
    
    success_count = 0
    for student_id, name, image_path in students:
        print(f"\n🎯 Processing {name} (ID: {student_id})")
        print(f"   Image: {image_path}")
        
        if os.path.exists(image_path):
            success, message = face_rec.add_student_face(student_id, name, image_path)
            if success:
                print(f"   ✅ {message}")
                success_count += 1
            else:
                print(f"   ❌ {message}")
        else:
            print(f"   ❌ Image file not found: {image_path}")
    
    print(f"\n📈 Migration complete: {success_count}/{len(students)} students migrated")
    
    # Show final stats
    stats = face_rec.get_recognition_stats()
    print(f"\n📊 Enhanced System Stats:")
    print(f"   Total students: {stats['total_students']}")
    print(f"   Total face samples: {stats['total_face_samples']}")
    print(f"   Training status: {stats['is_trained']}")
    
    conn.close()

if __name__ == "__main__":
    migrate_students()