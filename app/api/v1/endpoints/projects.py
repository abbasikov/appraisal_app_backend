from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.schemas.photo import PhotoResponse, PaginatedPhotosResponse
from app.schemas.task import TaskStatusResponse, BackgroundPhotoImportRequest, BackgroundPhotoImportResponse
from app.services.project_service import ProjectService
from app.services.photo_service import PhotoService
from app.services.template_service import TemplateService
from app.core.deps import get_current_user
from app.models.user import User, UserRole
from app.models.photo import Photo
from app.models.task_status import TaskStatus
from app.tasks.photo_tasks import import_photos_background, import_photos_recurring_batches
import os

router = APIRouter()

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Only Admin/Editor can create projects
        if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        

        
        db_project = ProjectService.create_project(db, project, current_user.id)
        if not db_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project creation failed. Client may not exist."
            )
        
        # Return project with joined data
        project_data = ProjectService.get_project_by_id(db, db_project.id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created project"
            )
        
        return project_data
    except HTTPException:
        raise
    except Exception as e:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during project creation"
        )

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    client_id: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # All roles can view projects
        projects = ProjectService.get_projects(db, skip=skip, limit=limit, client_id=client_id)
        return projects if projects is not None else []
    except Exception as e:
        print(f"Error in get_projects endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )

@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Only Admin/Editor can update
        if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        project = ProjectService.update_project(db, project_id, project_update, current_user.id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Return updated project with joined data
        project_data = ProjectService.get_project_by_id(db, project_id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve updated project"
            )
        
        return project_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR: Project update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during project update"
        )

@router.post("/{project_id}/dropbox-links")
async def update_dropbox_links(
    project_id: int,
    folder_links: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admin/Editor can update Dropbox links
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    project = ProjectService.update_dropbox_links(db, project_id, folder_links, current_user.id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {"message": "Dropbox links updated successfully", "links_count": len(folder_links)}

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only Admin can delete
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    success = ProjectService.delete_project(db, project_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {"message": "Project deleted successfully"}

@router.get("/{project_id}/photos", response_model=PaginatedPhotosResponse)
async def get_project_photos(
    project_id: int,
    skip: int = Query(0, ge=0, description="Number of photos to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of photos to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = PhotoService.get_photos_by_project_with_pagination(db, project_id, skip, limit)
    return PaginatedPhotosResponse(**result)

@router.get("/{project_id}/photos/{photo_id}/thumbnail")
async def get_photo_thumbnail(
    project_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from fastapi.responses import FileResponse
    
    photo = db.query(Photo).filter(
        Photo.id == photo_id,
        Photo.project_id == project_id,
        Photo.is_deleted == False
    ).first()
    
    if not photo or not photo.thumbnail_path or not os.path.exists(photo.thumbnail_path):
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(photo.thumbnail_path, media_type=photo.mime_type)

@router.post("/{project_id}/import-photos")
async def import_photos(
    project_id: int,
    batch_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    dropbox_links = project.get('dropbox_links', [])
    if not dropbox_links:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Dropbox links configured for this project"
        )
    
    result = PhotoService.import_photos_from_dropbox_batched(
        db, project_id, dropbox_links, current_user.id, batch_size
    )
    
    # Handle the new detailed result format
    if not result["success"] and result["imported_count"] == 0:
        # If completely failed, return error response
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": result["message"],
                "errors": result["errors"],
                "warnings": result["warnings"]
            }
        )
    
    # Return success response with details
    return {
        "message": result["message"],
        "imported_count": result["imported_count"],
        "total_found": result.get("total_found", 0),
        "errors": result["errors"],
        "warnings": result["warnings"],
        "success": result["success"],
        "has_more": result.get("has_more", False)
    }

@router.post("/{project_id}/generate-report/{template_id}")
async def generate_project_report(
    project_id: int,
    template_id: int,
    report_type: str = "final",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate report for project using specified template"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        report_path = TemplateService.generate_report(
            db, template_id, project_id, report_type
        )
        
        return {
            "message": "Report generated successfully",
            "report_path": report_path,
            "template_id": template_id,
            "project_id": project_id,
            "download_url": f"/api/v1/projects/{project_id}/download-report/{template_id}?report_type={report_type}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Report generation failed: {str(e)}"
        )

@router.get("/{project_id}/download-report/{template_id}")
async def download_project_report(
    project_id: int,
    template_id: int,
    report_type: str = "final",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download generated report"""
    from fastapi.responses import FileResponse
    from app.models.report import Report, ReportType
    
    # Find the most recent report
    report_type_enum = ReportType.DRAFT if report_type == "draft" else ReportType.FINAL
    
    report = db.query(Report).filter(
        Report.template_id == template_id,
        Report.project_id == project_id,
        Report.report_type == report_type_enum
    ).order_by(Report.created_at.desc()).first()
    
    if not report or not report.word_path or not os.path.exists(report.word_path):
        raise HTTPException(status_code=404, detail="Generated report not found")
    
    filename = f"appraisal_report_{project_id}_{template_id}_{report_type}.docx"
    return FileResponse(
        report.word_path, 
        filename=filename, 
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

@router.post("/{project_id}/import-photos-background", response_model=BackgroundPhotoImportResponse)
async def import_photos_background_endpoint(
    project_id: int,
    request: BackgroundPhotoImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import photos from Dropbox in the background to prevent server blocking
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    dropbox_links = project.get('dropbox_links', [])
    if not dropbox_links:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No Dropbox links configured for this project"
        )
    
    # Choose the appropriate background task (batch_size will be calculated automatically)
    if request.recurring:
        # Use recurring batches to process all photos
        task = import_photos_recurring_batches.delay(
            project_id, dropbox_links, current_user.id, None  # None = auto-calculate batch size
        )
        estimated_duration = "Duration varies based on optimal batch sizing"
        auto_batching_info = "Large photos will use smaller batches, small photos will use larger batches"
    else:
        # Use single batch processing
        task = import_photos_background.delay(
            project_id, dropbox_links, current_user.id, None  # None = auto-calculate batch size
        )
        estimated_duration = "Duration varies based on optimal batch sizing"
        auto_batching_info = "Batch size calculated automatically based on file sizes and server load"
    
    return BackgroundPhotoImportResponse(
        task_id=task.id,
        message=f"Photo import task started{' (recurring batches)' if request.recurring else ''}",
        project_id=project_id,
        recurring=request.recurring,
        estimated_duration=estimated_duration,
        auto_batching_info=auto_batching_info
    )

@router.get("/{project_id}/task-status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    project_id: int,
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a background photo import task
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify the project exists
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get task status
    task_status = db.query(TaskStatus).filter(
        TaskStatus.task_id == task_id,
        TaskStatus.project_id == project_id,
        TaskStatus.user_id == current_user.id
    ).first()
    
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task_status

@router.get("/{project_id}/tasks", response_model=List[TaskStatusResponse])
async def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all background tasks for a project
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Verify the project exists
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all tasks for the project
    tasks = db.query(TaskStatus).filter(
        TaskStatus.project_id == project_id,
        TaskStatus.user_id == current_user.id
    ).order_by(TaskStatus.created_at.desc()).all()
    
    return tasks

