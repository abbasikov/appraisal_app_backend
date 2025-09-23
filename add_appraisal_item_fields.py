#!/usr/bin/env python3
"""
Migration script to add missing fields to appraisal_items table
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings

def run_migration():
    """Add missing fields to appraisal_items table"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Adding missing fields to appraisal_items table...")
    
    # Add gold_price column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN gold_price NUMERIC(10, 2)
            """))
            conn.commit()
            print("✅ Successfully added gold_price column to appraisal_items table")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column gold_price already exists in appraisal_items table")
        else:
            print(f"❌ Error adding gold_price column: {e}")
    
    # Add photo_path column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN photo_path VARCHAR
            """))
            conn.commit()
            print("✅ Successfully added photo_path column to appraisal_items table")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column photo_path already exists in appraisal_items table")
        else:
            print(f"❌ Error adding photo_path column: {e}")
    
    # Add is_active column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN is_active BOOLEAN DEFAULT TRUE
            """))
            conn.commit()
            print("✅ Successfully added is_active column to appraisal_items table")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column is_active already exists in appraisal_items table")
        else:
            print(f"❌ Error adding is_active column: {e}")
    
    print("✅ Migration completed!")

if __name__ == "__main__":
    run_migration()