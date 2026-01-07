"""
Migration script to add Leave Management tables.
Run this script to update the database schema.
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from database.models import LeaveRequest

def migrate():
    """Create leave_requests table if it doesn't exist"""
    with app.app_context():
        # Create all tables (will only create new ones)
        db.create_all()
        print("✅ Database migration completed!")
        print("   - LeaveRequest table created/verified")
        
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'leave_requests' in tables:
            print("✅ leave_requests table exists")
        else:
            print("❌ leave_requests table not found - please check for errors")

if __name__ == '__main__':
    print("🔄 Running Leave Management migration...")
    migrate()
