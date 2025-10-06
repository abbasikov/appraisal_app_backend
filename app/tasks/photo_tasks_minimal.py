import json
import traceback
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.photo_service import PhotoService
from app.models.task_status import TaskStatus

def get_session() -> Session:
    """Create a database session for background tasks"""
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
    )
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

@celery_app.task(bind=True, name="import_photos_minimal")
def import_photos_minimal(self, project_id: int, dropbox_links: list, user_id: int):
    """Minimal version of photo import to isolate the issue"""
    task_id = self.request.id
    
    print(f"🧪 MINIMAL Task started: task_id={task_id}")
    print(f"📝 Parameters: project_id={project_id} (type: {type(project_id)})")
    print(f"📝 Parameters: user_id={user_id} (type: {type(user_id)})")
    print(f"📧 Parameters: dropbox_links={dropbox_links} (length: {len(dropbox_links)})")
    
    try:
        # Test basic functionality
        print("✅ Step 1: Basic parameters ok")
        
        # Test database connection
        db = get_session()
        print("✅ Step 2: Database session created")
        
        # Test TaskStatus creation with minimal data
        task_status = TaskStatus(
            task_id=str(task_id),  # Convert to string to be safe
            task_type="test_minimal",
            project_id=int(project_id),  # Explicit int conversion
            user_id=int(user_id),  # Explicit int conversion
            status="processing",
            progress=0,
            total_items=0,
            processed_items=0
        )
        print("✅ Step 3: TaskStatus object created")
        
        db.add(task_status)
        print("✅ Step 4: TaskStatus added to session")
        
        db.commit()
        print("✅ Step 5: Changes committed to database")
        
        db.close()
        print("✅ Step 6: Database session closed")
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Minimal task completed successfully"
        }
        
    except Exception as e:
        print(f"❌ Error in minimal task: {e}")
        print(f"❌ Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "task_id": task_id
        }
