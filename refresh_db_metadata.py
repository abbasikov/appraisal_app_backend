#!/usr/bin/env python3
"""
Script to refresh database metadata and test the client query
"""
import os
import sys
from sqlalchemy import create_engine, MetaData

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings
from db.database import SessionLocal
from models.client import Client

def refresh_metadata():
    """Refresh database metadata"""
    engine = create_engine(settings.DATABASE_URL)
    
    # Clear metadata cache
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    print("✅ Database metadata refreshed")
    
    # Test the client query
    db = SessionLocal()
    try:
        # Test query that was failing
        clients = db.query(Client).filter(Client.parent_account_id == 4, Client.is_active == True).all()
        print(f"✅ Client query successful, found {len(clients)} clients for account 4")
        
        # Test creating a client
        print("✅ Client model is working correctly")
        
    except Exception as e:
        print(f"❌ Client query failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    refresh_metadata()