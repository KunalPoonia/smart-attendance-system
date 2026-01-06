#!/usr/bin/env python3
"""
Check registered students and their face data
"""

import sqlite3
import os

def check_students():
    print("🔍 Checking registered students...")
    
    # Connect to database
    db_path = 'instance/attendance.db'
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check what tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"📋 Available tables: {[table[0] for table in tables]}")
    
    # Try to get students from the correct table
    try:
        cursor.execute("SELECT * FROM student")
        students = cursor.fetchall()
        
        print(f"📊 Found {len(students)} students:")
        for student in students:
            print(f"   - Student: {student}")
            print()
    except Exception as e:
        print(f"Error querying students: {e}")
        
        # Try alternative table structure
        try:
            cursor.execute("PRAGMA table_info(student)")
            columns = cursor.fetchall()
            print(f"📋 Student table columns: {columns}")
        except:
            pass
    
    conn.close()
    return students

if __name__ == "__main__":
    check_students()