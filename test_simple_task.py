#!/usr/bin/env python3
"""
Simple test task to isolate the NoneType error
"""

from celery import Celery
import tempfile

# Create a simple Celery instance
celery_app = Celery(
    "test_app",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery_app.task(bind=True, name="test_simple_task")
def test_simple_task(self, project_id: int, user_id: int):
    """Simple test task to verify we can handle int parameters"""
    task_id = self.request.id
    
    print(f"🧪 Test task started: task_id={task_id}, project_id={project_id}, user_id={user_id}")
    
    # Test string formatting
    try:
        message = f"Test task for project {project_id}, user {user_id}"
        print(f"✅ Message creation successful: {message}")
        return {"success": True, "message": message, "task_id": task_id}
    except Exception as e:
        print(f"❌ Error in message creation: {e}")
        return {"success": False, "error": str(e), "task_id": task_id}

if __name__ == "__main__":
    print("🧪 Testing simple task...")
    result = test_simple_task.delay(1, 1)
    print(f"Task submitted: {result.id}")
