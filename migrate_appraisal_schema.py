#!/usr/bin/env python3
"""
Migration script to update appraisal_items table with new schema
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings

def run_migration():
    """Update appraisal_items table with new schema fields"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Updating appraisal_items table schema...")
    
    # Add floor_building column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN floor_building VARCHAR
            """))
            conn.commit()
            print("✅ Successfully added floor_building column")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column floor_building already exists")
        else:
            print(f"❌ Error adding floor_building column: {e}")
    
    # Add photos JSON column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN photos JSON DEFAULT '[]'
            """))
            conn.commit()
            print("✅ Successfully added photos column")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column photos already exists")
        else:
            print(f"❌ Error adding photos column: {e}")
    
    # Add attributes JSON column
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE appraisal_items 
                ADD COLUMN attributes JSON DEFAULT '{}'
            """))
            conn.commit()
            print("✅ Successfully added attributes column")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column attributes already exists")
        else:
            print(f"❌ Error adding attributes column: {e}")
    
    print("✅ Schema migration completed!")

if __name__ == "__main__":
    run_migration()