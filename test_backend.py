#!/usr/bin/env python3
"""
Test script to verify backend functionality
"""
import os
import sys
import requests
import json

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from db.database import SessionLocal
from models.client import Client
from models.account import Account

def test_database():
    """Test database connection and queries"""
    print("Testing database connection...")
    
    db = SessionLocal()
    try:
        # Test account query
        accounts = db.query(Account).filter(Account.is_active == True).all()
        print(f"✅ Found {len(accounts)} active accounts")
        
        # Test client query with parent_account_id
        clients = db.query(Client).filter(Client.parent_account_id.isnot(None)).all()
        print(f"✅ Found {len(clients)} clients with parent accounts")
        
        # Test specific query that was failing
        test_clients = db.query(Client).filter(Client.parent_account_id == 4, Client.is_active == True).all()
        print(f"✅ Query for account 4 clients: {len(test_clients)} found")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    finally:
        db.close()

def test_backend_server():
    """Test if backend server is running"""
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"❌ Backend server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend server is not accessible: {e}")
        return False

if __name__ == "__main__":
    print("=== Backend Test ===")
    
    db_ok = test_database()
    server_ok = test_backend_server()
    
    if db_ok and server_ok:
        print("\n✅ All tests passed! Backend should be working.")
    else:
        print("\n❌ Some tests failed. Check the issues above.")
        
    print("\nTo restart backend server:")
    print("1. Kill existing processes: pkill -f 'python main.py'")
    print("2. Start fresh: source venv/bin/activate && python main.py")