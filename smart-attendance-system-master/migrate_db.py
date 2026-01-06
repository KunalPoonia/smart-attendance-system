#!/usr/bin/env python3
"""
Database Migration Script for Smart Attendance System
Adds new columns to existing database tables
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migrate existing database to new schema"""
    db_path = 'attendance.db'
    
    if not os.path.exists(db_path):
        print("No existing database found. New database will be created automatically.")
        return
    
    print("🔄 Starting database migration...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if migration is needed
        cursor.execute("PRAGMA table_info(student)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns to Student table if they don't exist
        new_student_columns = [
            ('phone', 'VARCHAR(15)'),
            ('course', 'VARCHAR(100)'),
            ('semester', 'VARCHAR(10)'),
            ('roll_number', 'VARCHAR(20)'),
            ('batch', 'VARCHAR(20)'),
            ('is_active', 'BOOLEAN DEFAULT 1'),
            ('updated_at', 'DATETIME')
        ]
        
        for column_name, column_type in new_student_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE student ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column '{column_name}' to student table")
                except sqlite3.Error as e:
                    print(f"⚠️  Could not add column '{column_name}': {e}")
        
        # Update existing students to be active
        cursor.execute("UPDATE student SET is_active = 1 WHERE is_active IS NULL")
        cursor.execute("UPDATE student SET updated_at = ? WHERE updated_at IS NULL", (datetime.now(),))
        
        # Set default course for existing students if empty
        cursor.execute("UPDATE student SET course = 'B.Tech' WHERE course IS NULL OR course = ''")
        
        # Check AttendanceRecord table
        cursor.execute("PRAGMA table_info(attendance_record)")
        attendance_columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns to AttendanceRecord table if they don't exist
        new_attendance_columns = [
            ('attendance_type', 'VARCHAR(20) DEFAULT "Regular"'),
            ('subject', 'VARCHAR(100)'),
            ('class_period', 'VARCHAR(20)'),
            ('teacher_name', 'VARCHAR(100)'),
            ('remarks', 'TEXT'),
            ('marked_by', 'VARCHAR(50) DEFAULT "System"'),
            ('updated_at', 'DATETIME')
        ]
        
        for column_name, column_type in new_attendance_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE attendance_record ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column '{column_name}' to attendance_record table")
                except sqlite3.Error as e:
                    print(f"⚠️  Could not add column '{column_name}': {e}")
        
        # Update existing attendance records
        cursor.execute("UPDATE attendance_record SET marked_by = 'System' WHERE marked_by IS NULL")
        cursor.execute("UPDATE attendance_record SET updated_at = created_at WHERE updated_at IS NULL")
        
        # Create ClassSchedule table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS class_schedule (
                id INTEGER PRIMARY KEY,
                subject_name VARCHAR(100) NOT NULL,
                subject_code VARCHAR(20) NOT NULL,
                department VARCHAR(50) NOT NULL,
                course VARCHAR(100) NOT NULL,
                year VARCHAR(10) NOT NULL,
                section VARCHAR(5) NOT NULL,
                semester VARCHAR(10) NOT NULL,
                teacher_name VARCHAR(100) NOT NULL,
                class_time VARCHAR(20),
                class_days VARCHAR(50),
                room_number VARCHAR(20),
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Created class_schedule table")
        
        conn.commit()
        conn.close()
        
        print("🎉 Database migration completed successfully!")
        print("📊 All new features are now available")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    migrate_database()