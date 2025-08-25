#!/usr/bin/env python3
"""
Fix existing user roles in database
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_user_roles():
    """Update existing user roles to match new enum values"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Fixing user roles in database...")
    
    with engine.connect() as conn:
        try:
            # First, change column to VARCHAR to allow updates
            conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR"))
            print("  🔧 Changed role column to VARCHAR")
            
            # Update APPRAISER to EDITOR
            result = conn.execute(text("""
                UPDATE users 
                SET role = 'editor' 
                WHERE role = 'appraiser'
            """))
            print(f"  ✅ Updated {result.rowcount} APPRAISER roles to EDITOR")
            
            # Update CLIENT to READER
            result = conn.execute(text("""
                UPDATE users 
                SET role = 'reader' 
                WHERE role = 'client'
            """))
            print(f"  ✅ Updated {result.rowcount} CLIENT roles to READER")
            
            # Show current roles
            result = conn.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role"))
            print("  📊 Current role distribution:")
            for row in result:
                print(f"    - {row[0]}: {row[1]} users")
            
            conn.commit()
            print("✅ User roles fixed successfully!")
            
        except Exception as e:
            print(f"❌ Error fixing roles: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    fix_user_roles()