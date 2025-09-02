#!/usr/bin/env python3
"""
Add user management fields to users table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import SessionLocal

def add_user_fields():
    """Add invitation and password fields to users table"""
    
    db = SessionLocal()
    try:
        print("Adding user management fields to users table...")
        
        # Add invitation_token column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS invitation_token VARCHAR
        """))
        
        # Add invitation_expires_at column  
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP WITH TIME ZONE
        """))
        
        # Add invited_by column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS invited_by INTEGER
        """))
        
        # Add password_set column
        db.execute(text("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS password_set BOOLEAN DEFAULT FALSE
        """))
        
        # Update existing users to have password_set = true
        db.execute(text("""
            UPDATE users 
            SET password_set = TRUE 
            WHERE password_hash IS NOT NULL AND password_hash != ''
        """))
        
        db.commit()
        print("✅ Successfully added user management fields")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding fields: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    add_user_fields()