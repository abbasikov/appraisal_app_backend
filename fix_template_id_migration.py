#!/usr/bin/env python3
"""
Migration script to ensure template_id column exists in projects table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def run_migration():
    """Add template_id column to projects table if missing"""
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
                    AND column_name = 'template_id'
                """))
                
                if result.fetchone():
                    print("✅ template_id column already exists in projects table")
                    return True
                    
            except Exception as e:
                print(f"⚠️ Could not check existing columns (might be SQLite): {e}")
            
            # Add the template_id column
            try:
                connection.execute(text("""
                    ALTER TABLE projects 
                    ADD COLUMN template_id INTEGER REFERENCES templates(id)
                """))
                connection.commit()
                print("✅ Successfully added template_id column to projects table")
                return True
                
            except OperationalError as e:
                if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                    print("✅ template_id column already exists in projects table")
                    return True
                else:
                    print(f"❌ Error adding template_id column: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Running template_id migration...")
    success = run_migration()
    
    if success:
        print("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("❌ Migration failed!")
        sys.exit(1)