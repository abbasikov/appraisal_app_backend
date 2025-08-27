import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_test_users():
    """Create test users with different roles"""
    db: Session = SessionLocal()
    
    try:
        # Test users data
        test_users = [
            # Admin Users
            {
                "username": "admin",
                "email": "admin@appraisal.com",
                "password": "admin123",
                "first_name": "System",
                "last_name": "Administrator",
                "phone": "+1-555-0001",
                "role": UserRole.ADMIN
            },
            {
                "username": "john_admin",
                "email": "john.admin@appraisal.com",
                "password": "password123",
                "first_name": "John",
                "last_name": "Smith",
                "phone": "+1-555-0002",
                "role": UserRole.ADMIN
            },
            
            # Editor Users
            {
                "username": "editor",
                "email": "editor@appraisal.com",
                "password": "editor123",
                "first_name": "Lead",
                "last_name": "Editor",
                "phone": "+1-555-0101",
                "role": UserRole.EDITOR
            },
            {
                "username": "sarah_editor",
                "email": "sarah.jones@appraisal.com",
                "password": "password123",
                "first_name": "Sarah",
                "last_name": "Jones",
                "phone": "+1-555-0102",
                "role": UserRole.EDITOR
            },
            {
                "username": "mike_editor",
                "email": "mike.wilson@appraisal.com",
                "password": "password123",
                "first_name": "Michael",
                "last_name": "Wilson",
                "phone": "+1-555-0103",
                "role": UserRole.EDITOR
            },
            {
                "username": "lisa_editor",
                "email": "lisa.brown@appraisal.com",
                "password": "password123",
                "first_name": "Lisa",
                "last_name": "Brown",
                "phone": "+1-555-0104",
                "role": UserRole.EDITOR
            },
            
            # Reader Users
            {
                "username": "reader",
                "email": "reader@appraisal.com",
                "password": "reader123",
                "first_name": "Report",
                "last_name": "Reader",
                "phone": "+1-555-0201",
                "role": UserRole.READER
            },
            {
                "username": "david_reader",
                "email": "david.clark@appraisal.com",
                "password": "password123",
                "first_name": "David",
                "last_name": "Clark",
                "phone": "+1-555-0202",
                "role": UserRole.READER
            },
            {
                "username": "emma_reader",
                "email": "emma.davis@appraisal.com",
                "password": "password123",
                "first_name": "Emma",
                "last_name": "Davis",
                "phone": "+1-555-0203",
                "role": UserRole.READER
            },
            {
                "username": "james_reader",
                "email": "james.miller@appraisal.com",
                "password": "password123",
                "first_name": "James",
                "last_name": "Miller",
                "phone": "+1-555-0204",
                "role": UserRole.READER
            }
        ]
        
        created_users = []
        skipped_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(
                (User.username == user_data["username"]) | 
                (User.email == user_data["email"])
            ).first()
            
            if existing_user:
                skipped_users.append(user_data["username"])
                continue
            
            # Create new user
            hashed_password = get_password_hash(user_data["password"])
            
            db_user = User(
                username=user_data["username"],
                email=user_data["email"],
                password_hash=hashed_password,
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                phone=user_data.get("phone"),
                role=user_data["role"],
                is_active=True,
                is_email_verified=True
            )
            
            db.add(db_user)
            created_users.append(user_data)
        
        db.commit()
        
        # Print results
        print(f"\nSeed Results:")
        print(f"Created: {len(created_users)} users")
        print(f"⏭Skipped: {len(skipped_users)} existing users")
        
        if skipped_users:
            print(f"\nSkipped existing users: {', '.join(skipped_users)}")
        
        if created_users:
            print(f"\nNew User Credentials:")
            print(f"{'='*60}")
            
            # Group by role
            roles = {"ADMIN": [], "EDITOR": [], "READER": []}
            for user in created_users:
                roles[user["role"].value.upper()].append(user)
            
            for role_name, users in roles.items():
                if users:
                    print(f"\n{role_name} USERS:")
                    print(f"{'-'*20}")
                    for user in users:
                        print(f"Username: {user['username']}")
                        print(f"Password: {user['password']}")
                        print(f"Email: {user['email']}")
                        print(f"Name: {user['first_name']} {user['last_name']}")
                        print()
        
    except Exception as e:
        db.rollback()
        print(f"Error creating test users: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating test users for Appraisal Report Management System...")
    create_test_users()
    print("\nSeed process completed!")