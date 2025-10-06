"""
Add TaskStatus table to database for background task tracking
"""

from sqlalchemy import create_engine, text
from app.core.config import settings
from app.db.database import Base
from app.models.task_status import TaskStatus
from sqlalchemy import inspect

def add_task_status_table():
    """Add TaskStatus table to the database"""
    
    # Create engine
    engine = create_engine(settings.DATABASE_URL)
    
    # Check if table exists
    inspector = inspect(engine)
    table_exists = inspector.has_table("task_status")
    
    if not table_exists:
        print("Creating TaskStatus table...")
        
        # Create the TaskStatus table
        TaskStatus.__table__.create(engine, checkfirst=True)
        
        print("✅ TaskStatus table created successfully")
    else:
        print("TaskStatus table already exists")
    
    # List all tables to verify
    tables = inspector.get_table_names()
    print(f"Database tables: {tables}")

if __name__ == "__main__":
    add_task_status_table()
