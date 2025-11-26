"""
Database Migration: Add estate_of and date_of_death fields to projects table
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import sys

def run_migration():
    """Add estate_of and date_of_death columns to projects table"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    migrations = [
        # Add estate_of column
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS estate_of VARCHAR;
        """,
        
        # Add date_of_death column
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS date_of_death DATE;
        """
    ]
    
    try:
        with engine.connect() as conn:
            for i, migration in enumerate(migrations, 1):
                print(f"Running migration {i}/{len(migrations)}...")
                conn.execute(text(migration))
                conn.commit()
                print(f"✅ Migration {i} completed successfully")
        
        print("\n✅ All migrations completed successfully!")
        print("✅ Added estate_of (VARCHAR) column to projects table")
        print("✅ Added date_of_death (DATE) column to projects table")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
