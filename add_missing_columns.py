#!/usr/bin/env python3
"""
Add missing columns to existing users table
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_missing_columns():
    """Add missing columns to users table"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Adding missing columns to users table...")
    
    with engine.connect() as conn:
        try:
            # Add is_active column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE
            """))
            print("  ✅ Added is_active column")
            
            # Add otp_secret column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS otp_secret VARCHAR
            """))
            print("  ✅ Added otp_secret column")
            
            # Add otp_enabled column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS otp_enabled BOOLEAN DEFAULT FALSE
            """))
            print("  ✅ Added otp_enabled column")
            
            # Add last_login column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE
            """))
            print("  ✅ Added last_login column")
            
            conn.commit()
            print("✅ All missing columns added successfully!")
            
        except Exception as e:
            print(f"❌ Error adding columns: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    add_missing_columns()