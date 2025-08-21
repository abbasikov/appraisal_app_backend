#!/usr/bin/env python3
"""
Script to create admin user accounts
Usage: python create_admin.py
"""

import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import SessionLocal
from app.services.user_service import UserService
from app.models.user import UserRole
from app.schemas.user import UserCreate
from getpass import getpass

def create_admin_user():
    """Interactive script to create admin user"""
    print("=== Create Admin User ===")
    
    # Get user input
    username = input("Enter admin username: ").strip()
    email = input("Enter admin email: ").strip()
    first_name = input("Enter first name: ").strip()
    last_name = input("Enter last name: ").strip()
    password = getpass("Enter password: ")
    confirm_password = getpass("Confirm password: ")
    
    # Validate input
    if not all([username, email, first_name, last_name, password]):
        print("❌ All fields are required!")
        return False
    
    if password != confirm_password:
        print("❌ Passwords don't match!")
        return False
    
    if len(password) < 6:
        print("❌ Password must be at least 6 characters!")
        return False
    
    # Create user data
    user_data = UserCreate(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=UserRole.ADMIN
    )
    
    # Create user in database
    db = SessionLocal()
    try:
        # Check if username exists
        if UserService.get_user_by_username(db, username):
            print(f"❌ Username '{username}' already exists!")
            return False
        
        # Check if email exists
        if UserService.get_user_by_email(db, email):
            print(f"❌ Email '{email}' already exists!")
            return False
        
        # Create admin user with auto-verified email
        admin_user = UserService.create_user(db, user_data)
        if not admin_user:
            print("❌ Failed to create admin user!")
            return False
        
        # Automatically verify admin email (no verification code needed)
        UserService.verify_email(db, email)
        
        print(f"✅ Admin user '{username}' created successfully!")
        print(f"📧 Email: {email}")
        print(f"👤 Name: {first_name} {last_name}")
        print(f"🔑 Role: Admin")
        print(f"✉️  Email verification: Automatically verified")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        db.close()

def list_admin_users():
    """List all admin users"""
    print("\n=== Current Admin Users ===")
    
    db = SessionLocal()
    try:
        from app.models.user import User
        admin_users = db.query(User).filter(User.role == UserRole.ADMIN).all()
        
        if not admin_users:
            print("No admin users found.")
            return
        
        for user in admin_users:
            status = "✅ Verified" if user.is_email_verified else "❌ Not Verified"
            print(f"👤 {user.username} ({user.email}) - {status}")
            
    except Exception as e:
        print(f"❌ Error listing admin users: {e}")
    finally:
        db.close()

def main():
    print("🏢 Appraisal App - Admin User Management")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Create new admin user")
        print("2. List existing admin users")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            list_admin_users()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()