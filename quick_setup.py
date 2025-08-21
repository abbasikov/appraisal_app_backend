#!/usr/bin/env python3
"""
Quick setup script - Run this first!
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🏢 Appraisal App - Quick Setup")
    print("=" * 40)
    
    # Step 1: Migrate database
    print("\n📊 Step 1: Database Migration")
    if not run_command("python migrate_db.py", "Database migration"):
        print("Please check your database connection and try again.")
        return
    
    # Step 2: Create admin user
    print("\n👤 Step 2: Admin User Creation")
    print("Please run: python create_admin.py")
    print("This will create an admin account with automatic email verification.")
    
    print("\n✅ Setup preparation completed!")
    print("\nNext steps:")
    print("1. python create_admin.py  # Create admin account")
    print("2. python main.py          # Start backend")
    print("3. cd ../appraisal-app-frontend && npm install && npm run dev  # Start frontend")

if __name__ == "__main__":
    main()