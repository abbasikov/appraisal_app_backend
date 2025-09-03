#!/usr/bin/env python3
"""
Test script for Account module functionality
"""

import os
import sys
from sqlalchemy.orm import sessionmaker

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.db.database import engine
from app.models.account import Account, AccountType
from app.services.account_service import AccountService
from app.schemas.account import AccountCreate

def test_account_operations():
    """Test basic Account CRUD operations"""
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("🧪 Testing Account operations...")
        
        # Test creating an account
        print("📝 Creating test account...")
        account_data = AccountCreate(
            name="Test Law Firm",
            account_type=AccountType.ATTORNEY,
            address="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            phone="555-123-4567",
            email="test@lawfirm.com"
        )
        
        account = AccountService.create_account(db, account_data)
        print(f"✅ Created account: {account.name} (ID: {account.id})")
        
        # Test getting accounts
        print("📋 Fetching accounts...")
        accounts = AccountService.get_accounts(db)
        print(f"✅ Found {len(accounts)} accounts")
        
        # Test getting account by ID
        print("🔍 Getting account by ID...")
        retrieved_account = AccountService.get_account_by_id(db, account.id)
        print(f"✅ Retrieved account: {retrieved_account.name}")
        
        # Clean up
        print("🧹 Cleaning up test data...")
        AccountService.delete_account(db, account.id)
        print("✅ Test account deleted")
        
        print("🎉 All Account tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    test_account_operations()