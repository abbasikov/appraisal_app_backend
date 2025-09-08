from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.appraisal_service import AppraisalService
from app.schemas.appraisal_item import AppraisalItemUpdate, AppraisalItemReorder

router = APIRouter()

@router.post("/projects/{project_id}/appraisal-items/initialize")
async def initialize_appraisal_items(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize appraisal items from project photos"""
    try:
        items = AppraisalService.create_items_from_photos(db, project_id, current_user.id)
        return {"message": f"Initialized {len(items)} appraisal items", "count": len(items)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize appraisal items: {str(e)}"
        )

@router.get("/projects/{project_id}/appraisal-items")
async def get_appraisal_items(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all appraisal items for a project"""
    try:
        items = AppraisalService.get_appraisal_items(db, project_id)
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch appraisal items: {str(e)}"
        )

@router.put("/appraisal-items/{item_id}")
async def update_appraisal_item(
    item_id: int,
    item_update: AppraisalItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an appraisal item"""
    try:
        item = AppraisalService.update_appraisal_item(db, item_id, item_update)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appraisal item not found"
            )
        return {"message": "Item updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update appraisal item: {str(e)}"
        )

@router.post("/projects/{project_id}/appraisal-items/reorder")
async def reorder_appraisal_items(
    project_id: int,
    reorder_data: List[AppraisalItemReorder],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reorder appraisal items"""
    try:
        success = AppraisalService.reorder_items(db, project_id, reorder_data)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to reorder items"
            )
        return {"message": "Items reordered successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder appraisal items: {str(e)}"
        )

@router.delete("/projects/{project_id}/appraisal-items/{item_id}")
async def delete_appraisal_item(
    project_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an appraisal item"""
    try:
        success = AppraisalService.delete_appraisal_item(db, item_id, project_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Appraisal item not found"
            )
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete appraisal item: {str(e)}"
        )