#!/usr/bin/env python3
"""
Test client creation directly
"""
import os
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal
from schemas.client import ClientCreate
from services.client_service import ClientService

def test_client_creation():
    """Test creating a client directly"""
    print("Testing client creation...")
    
    db = SessionLocal()
    try:
        # Create test client data
        client_data = ClientCreate(
            name="Test Client",
            parent_account_id=2,
            email="test@example.com",
            phone="555-1234",
            case_name="Test Case",
            case_number="TEST-001"
        )
        
        print(f"Client data: {client_data.model_dump()}")
        
        # Try to create client
        client = ClientService.create_client(db, client_data, user_id=1)
        
        if client:
            print(f"✅ Client created successfully: {client.id} - {client.name}")
            return True
        else:
            print("❌ Client creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error creating client: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_client_creation()