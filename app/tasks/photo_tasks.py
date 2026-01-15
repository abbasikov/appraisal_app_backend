import json
import traceback
from typing import List, Dict
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.celery_app import celery_app
from app.core.config import settings
from app.services.photo_service import PhotoService
from app.services.email_service import EmailService
from app.models.task_status import TaskStatus
from app.models.project import Project
from app.db.database import get_db

@celery_app.task(bind=True, name="import_photos_background")
def import_photos_background(self, project_id: int, dropbox_links: List[str], user_id: int, batch_size: int = None):
    """
    Background task to import photos from Dropbox
    
    Args:
        project_id: ID of the project to import photos to
        dropbox_links: List of Dropbox share links
        user_id: ID of the user initiating the import
        batch_size: Number of photos to process in each batch
    """
    task_id = self.request.id
    
    try:
        # Update task status to processing
        update_task_status(task_id, "processing", 0, f"Starting import from {len(dropbox_links)} Dropbox links")
        
        # Create database session
        db = get_session()
        
        # Calculate optimal batch size if not provided
        if batch_size is None:
            try:
                batch_size = calculate_optimal_batch_size(db, dropbox_links)
                # Ensure batch_size is a valid integer
                if batch_size is None:
                    batch_size = 15  # Safe default
                
                update_task_status(
                    task_id, 
                    "processing", 
                    10, 
                    f"Calculated optimal batch size: {batch_size}. Starting photo discovery..."
                )
            except Exception as calc_error:
                print(f"❌ Batch size calculation failed: {calc_error}")
                batch_size = 15  # Safe default
        
        # Get or create task status record
        task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
        if not task_status:
            task_status = TaskStatus(
                task_id=task_id,
                task_type="photo_import",
                project_id=project_id,
                user_id=user_id,
                status="processing",
                progress=0
            )
            db.add(task_status)
            db.commit()
        
        # Import photos using existing PhotoService
        result = PhotoService.import_photos_from_dropbox_batched(
            db=db,
            project_id=project_id,
            dropbox_links=dropbox_links,
            user_id=user_id,
            batch_size=batch_size
        )
        
        # Update progress based on result
        progress = 100 if result["success"] else 0
        status = "completed" if result["success"] else "failed"
        
        # Update final task status
        update_task_status(
            task_id, 
            status, 
            progress, 
            json.dumps(result),  # Store full result
            result.get("imported_count", 0),
            result.get("total_found", 0) if "total_found" in result else result.get("imported_count", 0)
        )
        
        # Send email notification ONLY if notification_email is explicitly provided
        if result["success"] and result.get("imported_count", 0) > 0:
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                
                # Only send email if notification_email is explicitly set
                if project and project.notification_email and project.notification_email.strip():
                    print(f"📧 Sending import completion email to: {project.notification_email}")
                    EmailService.send_import_completion_email(
                        project.notification_email,
                        project.project_name,
                        result.get("imported_count", 0),
                        result.get("total_found")
                    )
                else:
                    print(f"ℹ️ No notification_email configured for project - skipping email notification")
            except Exception as email_error:
                print(f"⚠️ Email notification failed: {email_error}")
                import traceback
                traceback.print_exc()
        
        return result
        
    except Exception as e:
        error_msg = f"Task failed: {str(e)}\n{traceback.format_exc()}"
        
        # Update task status to failed
        update_task_status(task_id, "failed", 0, error_msg)
        
        # Log the error
        print(f"❌ Background photo import task failed: {error_msg}")
        
        return {
            "success": False,
            "error": error_msg,
            "task_id": task_id
        }
    
    finally:
        db.close()

@celery_app.task(bind=True, name="import_photos_recurring_batches")
def import_photos_recurring_batches(self, project_id: int, dropbox_links: List[str], user_id: int, batch_size: int = None):
    """
    Background task to handle recurring batches of photo imports
    This continues processing until all photos are imported
    """
    task_id = self.request.id
    
    try:
        # Validate input parameters
        if project_id is None:
            raise ValueError("project_id cannot be None")
        if user_id is None:
            raise ValueError("user_id cannot be None")
        
        print(f"🔄 Starting recurring import task: project_id={project_id}, user_id={user_id}, links={len(dropbox_links)}")
        
        try:
            # Update task status to processing
            update_task_status(task_id, "processing", 0, f"Starting recurring import from {len(dropbox_links)} Dropbox links")
            print("✅ Initial task status updated")
        except Exception as status_error:
            print(f"❌ Error updating initial task status: {status_error}")
            raise status_error
        
        # Create database session
        db = get_session()
        
        # Calculate optimal batch size if not provided
        if batch_size is None:
            try:
                batch_size = calculate_optimal_batch_size(db, dropbox_links)
                print(f"📊 Calculated batch size: {batch_size}")
                # Ensure batch_size is a valid integer
                if batch_size is None:
                    batch_size = 15  # Safe default
                
                try:
                    update_task_status(
                        task_id, 
                        "processing", 
                        5, 
                        f"Calculated optimal batch size: {batch_size}. Starting photo discovery..."
                    )
                    print("✅ Batch size calculation status updated")
                except Exception as update_error:
                    print(f"⚠️ Batch size status update failed: {update_error}")
                    # Continue anyway
                    
            except Exception as calc_error:
                print(f"❌ Batch size calculation failed: {calc_error}")
                batch_size = 15  # Safe default
        
        # Get or create task status record
        task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
        if not task_status:
            print(f"🆕 Creating new task status record for task_id: {task_id}")
            task_status = TaskStatus(
                task_id=task_id,
                task_type="photo_import_recurring",
                project_id=project_id,
                user_id=user_id,
                status="processing",
                progress=0,
                total_items=0,
                processed_items=0
            )
            db.add(task_status)
            db.commit()
        
        total_imported = 0
        batch_number = 1
        has_more = True
        
        while has_more:
            # Update progress message
            update_task_status(
                task_id, 
                "processing", 
                int((total_imported / max(total_imported + batch_size, 1)) * 100),
                f"Processing batch {batch_number}"
            )
            
            # Import next batch
            result = PhotoService.import_photos_from_dropbox_batched(
                db=db,
                project_id=project_id,
                dropbox_links=dropbox_links,
                user_id=user_id,
                batch_size=batch_size
            )
            
            if result["success"]:
                total_imported += result.get("imported_count", 0)
                has_more = result.get("has_more", False)
                batch_number += 1
                
                # Update task progress
                progress_message = f"Processed {total_imported} photos across {batch_number-1} batches"
                progress_percent = int((total_imported / max(total_imported + batch_size, 1)) * 100)
                
                update_task_status(
                    task_id,
                    "processing",
                    progress_percent,
                    progress_message,
                    result.get("total_found", total_imported),
                    total_imported
                )
                
                # Small delay between batches to prevent overwhelming the server
                import time
                time.sleep(2)
            else:
                # If batch failed, stop processing
                errors = result.get('errors', ['Unknown error'])
                if isinstance(errors, str):
                    error_list = [errors]
                elif isinstance(errors, list):
                    error_list = errors
                else:
                    error_list = ['Unknown error']
                
                error_msg = f"Batch {batch_number} failed: {error_list}"
                update_temp_status(task_id, "failed", error_msg)
                break
        
        # Final update
        final_result = {
            "success": not has_more,  # Success if we processed all batches
            "imported_count": total_imported,
            "total_batches": batch_number - 1,
            "task_id": task_id
        }
        
        update_task_status(
            task_id,
            "completed" if final_result["success"] else "failed",
            100 if final_result["success"] else 70,  # 70% if failed partway
            json.dumps(final_result)
        )
        
        # Send email notification ONLY if notification_email is explicitly provided
        if final_result["success"] and total_imported > 0:
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                
                # Only send email if notification_email is explicitly set
                if project and project.notification_email and project.notification_email.strip():
                    print(f"📧 Sending import completion email to: {project.notification_email}")
                    EmailService.send_import_completion_email(
                        project.notification_email,
                        project.project_name,
                        total_imported
                    )
                else:
                    print(f"ℹ️ No notification_email configured for project - skipping email notification")
            except Exception as email_error:
                print(f"⚠️ Email notification failed: {email_error}")
                import traceback
                traceback.print_exc()
        
        return final_result
        
    except Exception as e:
        try:
            error_msg = f"Recurring batch task failed: {str(e)}\n{traceback.format_exc()}"
            update_task_status(task_id, "failed", 0, error_msg)
            print(f"❌ Recurring background photo import task failed: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "task_id": task_id
            }
        except Exception as update_error:
            # Fallback if even the error handling fails
            print(f"❌ Critical error in task error handling: {update_error}")
            return {
                "success": False,
                "error": f"Critical error: {str(e)}",
                "task_id": task_id
            }
    
    finally:
        db.close()

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

def update_task_status(task_id: str, status: str, progress: int, message: str, total_items: int = 0, processed_items: int = 0):
    """Update task status in database"""
    try:
        db = get_session()
        task_status = db.query(TaskStatus).filter(TaskStatus.task_id == task_id).first()
        
        if task_status:
            task_status.status = status
            task_status.progress = progress
            task_status.result_data = message
            task_status.total_items = total_items
            task_status.processed_items = processed_items
            
            if status in ["completed", "failed"]:
                from sqlalchemy.sql import func
                task_status.completed_at = func.now()
            
            db.commit()
            
        db.close()
    except Exception as e:
        print(f"❌ Error updating task status: {e}")

def update_temp_status(task_id: str, status: str, message: str):
    """Temporary status update (used during processing)"""
    update_task_status(task_id, status, 0, message)

def calculate_optimal_batch_size(db: Session, dropbox_links: List[str]) -> int:
    """
    Calculate optimal batch size based on:
    - Total number of files to download
    - Average file sizes
    - Current server load
    - Database performance
    """
    try:
        from app.services.dropbox_service import DropboxService
        
        dropbox_service = DropboxService()
        
        # Count total images across all links
        total_images = 0
        total_size_estimate = 0
        
        for link in dropbox_links:
            if dropbox_service.validate_folder_access(link):
                files = dropbox_service.list_folder_contents(link)
                for file_info in files:
                    if PhotoService.is_image_file(file_info['name']):
                        total_images += 1
                        file_size = file_info.get('size') or 0
                        if isinstance(file_size, (int, float)) and file_size > 0:
                            total_size_estimate += file_size
                        # Ignore None or invalid sizes
        
        # Calculate optimal batch size based on different factors
        if total_images == 0:
            return 10  # Default batch size
        
        # Base batch size calculation
        if total_images <= 50:
            # Small collections: smaller batches for faster processing
            base_batch_size = max(5, total_images // 10)
        elif total_images <= 200:
            # Medium collections: moderate batch size
            base_batch_size = max(10, total_images // 15)
        else:
            # Large collections: larger batches for efficiency
            base_batch_size = max(15, min(25, total_images // 20))
        
        # Adjust based on average file size
        avg_file_size = total_size_estimate / total_images if total_images > 0 else 0
        
        if avg_file_size > 5 * 1024 * 1024:  # > 5MB average
            # Large files: reduce batch size to prevent memory issues
            base_batch_size = max(3, base_batch_size // 2)
        elif avg_file_size < 1024 * 1024:  # < 1MB average
            # Small files: can increase batch size
            base_batch_size = min(30, base_batch_size * 2)
        
        # Check current database load (simple heuristic)
        active_tasks = db.query(TaskStatus).filter(TaskStatus.status == "processing").count()
        if active_tasks > 3:
            # High load: reduce batch size
            base_batch_size = max(5, base_batch_size // 2)
        
        # Final bounds checking
        optimal_batch_size = max(3, min(50, base_batch_size))
        
        print(f"📊 Batch size calculation: {total_images} images, avg {avg_file_size/1024/1024:.1f}MB, {active_tasks} active tasks → batch_size={optimal_batch_size}")
        
        return optimal_batch_size
        
    except Exception as e:
        print(f"❌ Error calculating batch size: {e}")
        return 15  # Safe default
