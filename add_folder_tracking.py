#!/usr/bin/env python3
"""
Add folder tracking fields to photos table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import SessionLocal, engine

def add_folder_tracking_fields():
    """Add dropbox_folder_path and source_folder_link columns to photos table"""
    
    db = SessionLocal()
    try:
        print("Adding folder tracking fields to photos table...")
        
        # Add dropbox_folder_path column
        db.execute(text("""
            ALTER TABLE photos 
            ADD COLUMN IF NOT EXISTS dropbox_folder_path VARCHAR
        """))
        
        # Add source_folder_link column  
        db.execute(text("""
            ALTER TABLE photos 
            ADD COLUMN IF NOT EXISTS source_folder_link VARCHAR
        """))
        
        db.commit()
        print("✅ Successfully added folder tracking fields")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding fields: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_folder_tracking_fields()