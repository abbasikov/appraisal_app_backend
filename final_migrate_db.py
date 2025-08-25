#!/usr/bin/env python3
"""
Final database migration script to sync with your 21-day project requirements
"""

import os
import sys
from sqlalchemy import create_engine
from app.core.config import settings
from app.db.database import Base

# Import all models to ensure they're registered with SQLAlchemy
from app.models import *

def run_migration():
    """Run the complete database migration"""
    print("🚀 Starting final database migration for your appraisal project...")
    
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables based on the new models
        print("🏗️  Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database migration completed successfully!")
        print("\n📋 Created tables for your project requirements:")
        print("   • Users (Admin, Editor, Reader roles + OTP MFA)")
        print("   • Clients (with sub-accounts)")
        print("   • Projects (appraisals with Dropbox integration)")
        print("   • Photos (with EXIF data and thumbnails)")
        print("   • Items (appraisal line items)")
        print("   • Reports (Word/PDF generation)")
        print("   • Templates (dynamic field mappings)")
        print("   • Metals Prices (API integration)")
        print("   • Activity Log (audit trail)")
        print("   • Verification Codes (for authentication)")
        
        print("\n🔧 Next steps:")
        print("   1. Run: python create_admin.py (to create admin user)")
        print("   2. Run: python main.py (to start the API server)")
        print("   3. Access API docs at: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()