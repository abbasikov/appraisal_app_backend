#!/usr/bin/env python3
"""
Complete project setup script
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings
from migrate_db import migrate_database
from create_admin import create_admin_user

def check_database_connection():
    """Check if database connection works"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def setup_project():
    """Complete project setup"""
    print("🏢 Appraisal App - Project Setup")
    print("=" * 40)
    
    # Check database connection
    if not check_database_connection():
        print("Please check your database configuration in .env file")
        return False
    
    # Run database migration
    print("\n📊 Setting up database...")
    migrate_database()
    
    # Create admin user
    print("\n👤 Creating admin user...")
    print("Please provide admin user details:")
    
    success = create_admin_user()
    if success:
        print("\n✅ Project setup completed successfully!")
        print("\nNext steps:")
        print("1. Start backend: python main.py")
        print("2. Start frontend: cd ../appraisal-app-frontend && npm install && npm run dev")
        print("3. Login at: http://localhost:5173/login")
        return True
    else:
        print("\n❌ Admin user creation failed. You can create it later using: python create_admin.py")
        return False

if __name__ == "__main__":
    setup_project()