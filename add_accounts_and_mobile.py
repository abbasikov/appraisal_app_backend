#!/usr/bin/env python3
"""
Migration script to add Account model and mobile_number to User model
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.database import Base
from app.models.account import Account
from app.models.user import User
from app.models.project import Project

def run_migration():
    """Run the migration to add accounts table and mobile_number to users"""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        print("🔄 Starting migration...")
        
        # Add mobile_number column to users table
        print("📱 Adding mobile_number column to users table...")
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN mobile_number VARCHAR"))
                conn.commit()
                print("✅ Added mobile_number column to users table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  mobile_number column already exists in users table")
                else:
                    raise e
        
        # Create accounts table
        print("🏢 Creating accounts table...")
        Account.__table__.create(engine, checkfirst=True)
        print("✅ Created accounts table")
        
        # Add account_id column to projects table
        print("🔗 Adding account_id column to projects table...")
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE projects ADD COLUMN account_id INTEGER"))
                conn.execute(text("ALTER TABLE projects ADD CONSTRAINT fk_projects_account_id FOREIGN KEY (account_id) REFERENCES accounts(id)"))
                conn.commit()
                print("✅ Added account_id column to projects table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  account_id column already exists in projects table")
                else:
                    raise e
        
        print("🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise e

if __name__ == "__main__":
    run_migration()