#!/usr/bin/env python3
"""
Script to start Flower (Celery monitoring tool)
Usage: python start_celery_flower.py
"""

import subprocess
import sys
import webbrowser
import time
import threading

def open_flower_ui():
    """Open Flower UI in browser after a short delay"""
    time.sleep(3)
    webbrowser.open("http://localhost:5555")

def start_flower():
    """Start Flower monitoring tool"""
    
    print("🌸 Starting Flower (Celery monitoring)...")
    
    # Open browser in separate thread
    threading.Thread(target=open_flower_ui, daemon=True).start()
    
    # Start Flower
    cmd = [
        "celery", 
        "-A", "app.core.celery_app.celery_app", 
        "flower",
        "--port=5555",
        "--address=0.0.0.0"
    ]
    
    try:
        print("Brower will open automatically at http://localhost:5555")
        print(f"Starting Flower with command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start Flower: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Flower stopped")

if __name__ == "__main__":
    start_flower()
