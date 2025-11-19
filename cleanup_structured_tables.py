"""
Database Cleanup: Drop structured tables (coin_items, wine_items, content_items)
These tables are no longer needed with the enhanced JSONB approach
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
import sys

def run_cleanup():
    """Drop structured tables that are no longer needed"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    cleanup_steps = [
        # Drop tables in correct order (respect foreign keys)
        """
        DROP TABLE IF EXISTS coin_items CASCADE;
        """,
        
        """
        DROP TABLE IF EXISTS wine_items CASCADE;
        """,
        
        """
        DROP TABLE IF EXISTS content_items CASCADE;
        """,
        
        """
        DROP TABLE IF EXISTS image_items CASCADE;
        """,
    ]
    
    try:
        with engine.connect() as conn:
            print("🧹 Starting cleanup of structured tables...")
            print("=" * 80)
            print("⚠️  NOTE: This will drop coin_items, wine_items, content_items tables")
            print("⚠️  These tables are replaced by JSONB attributes approach")
            print("=" * 80)
            
            # Check if tables exist and have data
            print("\n📊 Checking for data in tables...")
            
            for table_name in ['coin_items', 'wine_items', 'content_items']:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    print(f"  - {table_name}: {count} records")
                    
                    if count > 0:
                        print(f"\n⚠️  WARNING: {table_name} has {count} records!")
                        print("  These will be lost. Make sure data is in appraisal_items.attributes")
                        
                        response = input(f"\n  Continue with dropping {table_name}? (yes/no): ")
                        if response.lower() != 'yes':
                            print("❌ Cleanup cancelled")
                            return
                except Exception as e:
                    print(f"  - {table_name}: does not exist or cannot be accessed")
            
            print("\n🗑️  Dropping tables...")
            for i, step in enumerate(cleanup_steps, 1):
                print(f"\n📝 Step {i}/{len(cleanup_steps)}...")
                try:
                    conn.execute(text(step))
                    conn.commit()
                    print(f"✅ Step {i} completed")
                except Exception as e:
                    print(f"⚠️  Step {i}: {str(e)} (table may not exist)")
            
            print("\n" + "=" * 80)
            print("🎉 Cleanup completed successfully!")
            print("\n✅ Removed tables:")
            print("  - coin_items")
            print("  - wine_items")
            print("  - content_items")
            print("  - image_items")
            print("\n✅ System now uses scalable JSONB approach!")
            print("✅ All data stored in appraisal_items.attributes")
            
    except Exception as e:
        print(f"\n❌ Cleanup failed: {str(e)}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    print("=" * 80)
    print("DATABASE CLEANUP: Remove Structured Tables")
    print("=" * 80)
    print("\nThis script will drop the following tables:")
    print("  - coin_items")
    print("  - wine_items")
    print("  - content_items")
    print("  - image_items")
    print("\nThese are replaced by the enhanced JSONB approach.")
    print("=" * 80)
    
    response = input("\nProceed with cleanup? (yes/no): ")
    if response.lower() == 'yes':
        run_cleanup()
    else:
        print("❌ Cleanup cancelled")

