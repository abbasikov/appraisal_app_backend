#!/usr/bin/env python3
"""
Fix enum constraint in database
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def fix_enum_constraint():
    """Fix the UserRole enum constraint"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Fixing enum constraint...")
    
    with engine.connect() as conn:
        try:
            # Drop the old enum type and recreate
            conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            print("  🗑️  Dropped old enum type")
            
            # Create new enum type
            conn.execute(text("CREATE TYPE userrole AS ENUM ('admin', 'editor', 'reader')"))
            print("  ✅ Created new enum type")
            
            # First update the case of existing roles
            conn.execute(text("UPDATE users SET role = LOWER(role)"))
            print("  🔄 Updated role case to lowercase")
            
            # Update the column to use the new enum
            conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole"))
            print("  ✅ Updated column to use new enum")
            
            # Show current roles
            result = conn.execute(text("SELECT username, role FROM users"))
            print("  📊 Current users:")
            for row in result:
                print(f"    - {row[0]}: {row[1]}")
            
            conn.commit()
            print("✅ Enum constraint fixed successfully!")
            
        except Exception as e:
            print(f"❌ Error fixing enum: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    fix_enum_constraint()