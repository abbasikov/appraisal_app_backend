#!/usr/bin/env python3
"""
Add appraisal_items table for the appraisal workflow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings

def add_appraisal_items_table():
    """Add appraisal_items table to database"""
    
    print("🔄 Adding appraisal_items table...")
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    # SQL to create appraisal_items table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS appraisal_items (
        id SERIAL PRIMARY KEY,
        project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        photo_id INTEGER REFERENCES photos(id) ON DELETE SET NULL,
        line_number INTEGER NOT NULL,
        room_area VARCHAR,
        item_type VARCHAR,
        description TEXT,
        appraised_value NUMERIC(12, 2) DEFAULT 0.00,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    """
    
    # Create indexes
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_appraisal_items_project_id ON appraisal_items(project_id);",
        "CREATE INDEX IF NOT EXISTS idx_appraisal_items_sort_order ON appraisal_items(sort_order);",
        "CREATE INDEX IF NOT EXISTS idx_appraisal_items_photo_id ON appraisal_items(photo_id);"
    ]
    
    try:
        with engine.connect() as connection:
            # Create table
            connection.execute(text(create_table_sql))
            print("✅ Created appraisal_items table")
            
            # Create indexes
            for index_sql in create_indexes_sql:
                connection.execute(text(index_sql))
            print("✅ Created indexes")
            
            connection.commit()
            
        print("🎉 Successfully added appraisal_items table!")
        
    except Exception as e:
        print(f"❌ Error adding appraisal_items table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    add_appraisal_items_table()