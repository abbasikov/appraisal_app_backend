#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def check_database():
    """Check database tables and structure"""
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    
    print("🔍 Checking database structure...")
    print(f"Database URL: {settings.DATABASE_URL}")
    print()
    
    # Get all tables
    tables = inspector.get_table_names()
    print(f"📊 Found {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  ✅ {table}")
    print()
    
    # Check specific tables we need
    required_tables = ['users', 'clients', 'projects', 'photos', 'activity_log']
    missing_tables = []
    
    for table in required_tables:
        if table in tables:
            print(f"✅ {table} table exists")
            
            # Check columns for important tables
            if table == 'projects':
                columns = inspector.get_columns(table)
                col_names = [col['name'] for col in columns]
                print(f"   Columns: {', '.join(col_names)}")
                
                if 'dropbox_folder_link' in col_names:
                    print("   ✅ dropbox_folder_link column exists")
                else:
                    print("   ❌ dropbox_folder_link column missing")
                    
            elif table == 'photos':
                columns = inspector.get_columns(table)
                col_names = [col['name'] for col in columns]
                print(f"   Columns: {', '.join(col_names)}")
                
        else:
            missing_tables.append(table)
            print(f"❌ {table} table missing")
    
    if missing_tables:
        print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
        print("Run: python3 migrate_db.py")
    else:
        print(f"\n✅ All required tables exist!")
    
    # Check if there's any data
    with engine.connect() as conn:
        if 'projects' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM projects")).scalar()
            print(f"📊 Projects count: {result}")
            
            if result > 0:
                # Check dropbox links
                result = conn.execute(text("SELECT id, project_name, dropbox_folder_link FROM projects LIMIT 5")).fetchall()
                print("📋 Sample projects:")
                for row in result:
                    dropbox_status = "✅ Has link" if row[2] else "❌ No link"
                    print(f"   {row[0]}: {row[1]} - {dropbox_status}")
        
        if 'photos' in tables:
            result = conn.execute(text("SELECT COUNT(*) FROM photos")).scalar()
            print(f"📸 Photos count: {result}")

if __name__ == "__main__":
    check_database()