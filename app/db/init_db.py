from sqlalchemy import create_engine
from app.core.config import settings
from app.db.database import Base
from app.models import *

def create_tables():
    """Create all database tables if they don't exist"""
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()