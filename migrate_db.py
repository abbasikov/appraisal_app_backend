#!/usr/bin/env python3
"""
Database migration script to add missing columns and tables
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.init_db import create_tables

def migrate_database():
    """Add missing columns to existing tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Starting database migration...")
    
    with engine.connect() as conn:
        try:
            # Add is_email_verified column to users table if it doesn't exist
            print("📝 Adding is_email_verified column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_email_verified BOOLEAN DEFAULT FALSE
            """))
            
            # Update existing users to have verified emails (for backward compatibility)
            print("✅ Setting existing users as email verified...")
            conn.execute(text("""
                UPDATE users 
                SET is_email_verified = TRUE 
                WHERE is_email_verified IS NULL OR is_email_verified = FALSE
            """))
            
            conn.commit()
            print("✅ Users table migration completed!")
            
        except Exception as e:
            print(f"❌ Error migrating users table: {e}")
            conn.rollback()
    
    # Create any missing tables
    print("🏗️  Creating missing tables...")
    create_tables()
    
    print("✅ Database migration completed successfully!")

if __name__ == "__main__":
    migrate_database()