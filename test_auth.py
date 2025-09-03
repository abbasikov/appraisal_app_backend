#!/usr/bin/env python3
"""
Test authentication to debug login issues
"""

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.user_service import UserService
from app.models.user import User
from app.core.security import verify_password

def test_authentication():
    """Test authentication with existing users"""
    print("=== Testing Authentication ===")
    
    db = SessionLocal()
    try:
        # List all users
        users = db.query(User).all()
        print(f"Found {len(users)} users in database:")
        
        for user in users:
            print(f"- {user.username} ({user.email}) - Role: {user.role.value} - Active: {user.is_active} - Verified: {user.is_email_verified}")
        
        if not users:
            print("No users found in database!")
            return
        
        # Test with first user
        test_user = users[0]
        print(f"\nTesting authentication with user: {test_user.username}")
        
        # Get password from user input
        import getpass
        password = getpass.getpass("Enter password for this user: ")
        
        # Test authentication
        authenticated_user = UserService.authenticate_user(db, test_user.username, password)
        
        if authenticated_user:
            print("✅ Authentication successful!")
            print(f"User ID: {authenticated_user.id}")
            print(f"Username: {authenticated_user.username}")
            print(f"Email: {authenticated_user.email}")
            print(f"Role: {authenticated_user.role.value}")
            print(f"Active: {authenticated_user.is_active}")
            print(f"Email Verified: {authenticated_user.is_email_verified}")
        else:
            print("❌ Authentication failed!")
            
            # Test password hash directly
            print(f"Testing password hash directly...")
            is_valid = verify_password(password, test_user.password_hash)
            print(f"Password hash verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_authentication()