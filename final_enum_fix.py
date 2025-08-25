#!/usr/bin/env python3
"""
Final fix for enum issue
"""

from sqlalchemy import create_engine, text
from app.core.config import settings

def final_enum_fix():
    """Final fix for the enum issue"""
    engine = create_engine(settings.DATABASE_URL)
    
    print("🔄 Final enum fix...")
    
    with engine.connect() as conn:
        try:
            # Drop all enum types and recreate cleanly
            conn.execute(text("DROP TYPE IF EXISTS userrole CASCADE"))
            print("  🗑️  Dropped enum type")
            
            # Temporarily change column to text
            conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE TEXT"))
            print("  🔧 Changed role to TEXT")
            
            # Create new enum with lowercase values (matching our Python enum)
            conn.execute(text("CREATE TYPE userrole AS ENUM ('admin', 'editor', 'reader')"))
            print("  ✅ Created new enum type")
            
            # Convert column back to enum
            conn.execute(text("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::userrole"))
            print("  ✅ Applied enum to column")
            
            # Verify data
            result = conn.execute(text("SELECT username, role FROM users"))
            print("  📊 Final data:")
            for row in result:
                print(f"    - {row[0]}: {row[1]}")
            
            conn.commit()
            print("✅ Enum fixed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    final_enum_fix()