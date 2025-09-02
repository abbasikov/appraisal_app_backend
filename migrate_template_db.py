#!/usr/bin/env python3
"""
Database migration script for template system
Adds missing columns to templates table
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in environment variables")
    sys.exit(1)

def migrate_templates_table():
    """Add missing columns to templates table"""
    engine = create_engine(DATABASE_URL)
    
    migrations = [
        "ALTER TABLE templates ADD COLUMN IF NOT EXISTS fillable_file_path VARCHAR;",
        "ALTER TABLE templates ADD COLUMN IF NOT EXISTS created_by INTEGER REFERENCES users(id);"
    ]
    
    try:
        with engine.connect() as conn:
            for migration in migrations:
                try:
                    conn.execute(text(migration))
                    print(f"✓ Executed: {migration}")
                except OperationalError as e:
                    if "already exists" in str(e).lower():
                        print(f"⚠ Column already exists: {migration}")
                    else:
                        print(f"✗ Failed: {migration} - {e}")
            
            conn.commit()
            print("✓ Template table migration completed successfully")
            
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_templates_table()