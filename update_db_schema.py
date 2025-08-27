import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def update_database_schema():
    """Update database schema with SQL commands"""
    
    print("🔄 Updating database schema for Dropbox integration...")
    
    # SQL commands to ensure tables exist
    sql_commands = [
        # Ensure photos table exists
        """
        CREATE TABLE IF NOT EXISTS photos (
            id SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL REFERENCES projects(id),
            original_filename VARCHAR NOT NULL,
            file_path VARCHAR,
            thumbnail_path VARCHAR,
            file_size INTEGER,
            mime_type VARCHAR,
            width INTEGER,
            height INTEGER,
            exif_date TIMESTAMP WITH TIME ZONE,
            sort_order INTEGER DEFAULT 0,
            is_deleted BOOLEAN DEFAULT FALSE,
            dropbox_file_id VARCHAR,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE
        );
        """,
        
        # Ensure projects table has dropbox columns
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS dropbox_folder_link VARCHAR;
        """,
        
        """
        ALTER TABLE projects 
        ADD COLUMN IF NOT EXISTS dropbox_folder_id VARCHAR;
        """,
        
        # Create indexes for better performance
        """
        CREATE INDEX IF NOT EXISTS idx_photos_project_id ON photos(project_id);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_photos_is_deleted ON photos(is_deleted);
        """,
        
        """
        CREATE INDEX IF NOT EXISTS idx_photos_exif_date ON photos(exif_date);
        """
    ]
    
    # Write SQL to file for manual execution
    with open('update_schema.sql', 'w') as f:
        f.write("-- Database schema update for Dropbox integration\\n\\n")
        for i, cmd in enumerate(sql_commands, 1):
            f.write(f"-- Command {i}\\n")
            f.write(cmd.strip() + "\\n\\n")
    
    print("✅ SQL commands written to 'update_schema.sql'")
    print("📋 Run these commands in your PostgreSQL database:")
    print()
    
    for i, cmd in enumerate(sql_commands, 1):
        print(f"-- Command {i}")
        print(cmd.strip())
        print()
    
    print("🔧 Or run: psql -d appraisal_db -f update_schema.sql")

if __name__ == "__main__":
    update_database_schema()