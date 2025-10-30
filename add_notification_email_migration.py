#!/usr/bin/env python3
"""
Migration script to add notification_email column to projects table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def run_migration():
    """Add notification_email column to projects table"""
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as connection:
            # Check if column already exists
            try:
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'projects' 
                    AND column_name = 'notification_email'
                """))
                
                if result.fetchone():
                    print("✅ notification_email column already exists in projects table")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Could not check existing columns (might be SQLite): {e}")
            
            # Add the notification_email column
            try:
                connection.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN notification_email VARCHAR
                """))
                connection.commit()
                print("✅ Successfully added notification_email column to projects table")
                return True
                
            except OperationalError as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ notification_email column already exists in projects table")
                    return True
                else:
                    print(f"❌ Error adding notification_email column: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Running notification_email migration...")
    success = run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)