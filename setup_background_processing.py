#!/usr/bin/env python3
"""
Setup script for background photo processing with Celery and Redis
"""

import subprocess
import sys
import os
import time

def check_redis():
    """Check if Redis is running"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
        return True
    except Exception as e:
        print(f"❌ Redis is not running: {e}")
        return False

def install_redis():
    """Install Redis if not available"""
    print("📦 Installing Redis...")
    
    try:
        # Try to install Redis using brew (macOS)
        subprocess.run(["brew", "install", "redis"], check=True, capture_output=True)
        print("✅ Redis installed successfully")
        
        # Start Redis
        subprocess.Popen(["redis-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        if check_redis():
            print("✅ Redis started successfully")
            return True
        else:
            print("❌ Failed to start Redis")
            return False
    except subprocess.CalledProcessError:
        print("❌ Failed to install Redis. Please install manually:")
        print("  macOS: brew install redis && redis-server")
        print("  Ubuntu/Debian: sudo apt-get install redis-server")
        print("  Windows: Download from GitHub releases")
        return False

def setup_database():
    """Add TaskStatus table to database"""
    print("🗄️ Setting up database...")
    
    try:
        from add_task_status_table import add_task_status_table
        add_task_status_table()
        print("✅ Database setup completed")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def install_dependencies():
    """Install required Python dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up background photo processing...")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Setup failed at dependency installation")
        sys.exit(1)
    
    # Step 2: Setup Redis
    if not check_redis():
        if not install_redis():
            print("❌ Setup failed at Redis installation")
            sys.exit(1)
    
    # Step 3: Setup database
    if not setup_database():
        print("❌ Setup failed at database setup")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("✅ Background processing setup completed!")
    print("\nTo start background processing:")
    print("1. Start Celery worker: python start_celery_worker.py")
    print("2. (Optional) Start Flower monitoring: python start_celery_flower.py")
    print("3. Start your FastAPI server: uvicorn app.main:app --reload")
    print("\nAPI endpoints:")
    print("- POST /api/v1/projects/{project_id}/import-photos-background")
    print("- GET /api/v1/projects/{project_id}/task-status/{task_id}")
    print("- GET /api/v1/projects/{project_id}/tasks")

if __name__ == "__main__":
    main()
