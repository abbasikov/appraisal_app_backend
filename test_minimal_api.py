#!/usr/bin/env python3
"""
Test the minimal photo import task
"""

from app.tasks.photo_tasks_minimal import import_photos_minimal

if __name__ == "__main__":
    print("🧪 Testing minimal photo import task...")
    
    # Test with the same parameters that were failing
    result = import_photos_minimal.delay(
        project_id=2,
        dropbox_links=["https://dropbox.com/test"],
        user_id=1
    )
    
    print(f"Task ID: {result.id}")
    print("Task submitted successfully. Check Celery worker logs for detailed output.")
