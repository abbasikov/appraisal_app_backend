"""
Database Migration: Add appraisal_location and effective_date fields to projects table
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import sys

def run_migration():
    """Add appraisal_location and effective_date columns to projects table"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    migrations = [
        # Add appraisal_location column
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS appraisal_location VARCHAR;
        """,
        
        # Add effective_date column
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS effective_date DATE;
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
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)

