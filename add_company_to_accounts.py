import sys
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def add_company_column():
    """Add company column to accounts table"""
    print("🔄 Adding company column to accounts table...")
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        try:
            # Check if column exists first
            result = connection.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='accounts' AND column_name='company'"
            ))
            
            if result.fetchone():
                print("⚠️ Column 'company' already exists in 'accounts' table.")
            else:
                connection.execute(text("ALTER TABLE accounts ADD COLUMN company VARCHAR"))
                connection.commit()
                print("✅ Successfully added 'company' column to 'accounts' table.")
                
        except Exception as e:
            print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_company_column()
