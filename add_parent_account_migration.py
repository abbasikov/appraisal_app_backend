#!/usr/bin/env python3
"""
Migration script to add parent_account_id column to clients table
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings

def run_migration():
    """Add parent_account_id columns to clients and accounts tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Handle clients table
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE clients 
                ADD COLUMN parent_account_id INTEGER REFERENCES accounts(id)
            """))
            conn.commit()
            print("✅ Successfully added parent_account_id column to clients table")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column parent_account_id already exists in clients table")
        else:
            print(f"❌ Error adding to clients table: {e}")
            
    # Handle accounts table
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                ALTER TABLE accounts 
                ADD COLUMN parent_account_id INTEGER REFERENCES accounts(id)
            """))
            conn.commit()
            print("✅ Successfully added parent_account_id column to accounts table")
    except ProgrammingError as e:
        if "already exists" in str(e):
            print("✅ Column parent_account_id already exists in accounts table")
        else:
            print(f"❌ Error adding to accounts table: {e}")


if __name__ == "__main__":
    run_migration()