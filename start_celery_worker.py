#!/usr/bin/env python3
"""
Script to start Celery worker for background tasks
Usage: python start_celery_worker.py
"""

import subprocess
import sys
import os

def start_celery_worker():
    """Start Celery worker process"""
    
    print("🚀 Starting Celery worker...")
    
    # Check if Redis is running
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("Please make sure Redis is running: brew install redis && redis-server")
        sys.exit(1)
    
    # Start Celery worker
    cmd = [
        "celery", 
        "-A", "app.core.celery_app.celery_app", 
        "worker", 
        "--loglevel=info",
        "--concurrency=2",
        "--time-limit=1800",  # 30 minutes max per task
        "--soft-time-limit=1500"  # 25 minutes soft limit
    ]
    
    try:
        print(f"Starting worker with command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Celery worker: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Celery worker stopped")

if __name__ == "__main__":
    start_celery_worker()
