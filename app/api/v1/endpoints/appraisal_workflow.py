from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.appraisal_service import AppraisalService
from app.schemas.appraisal_item import AppraisalItemCreate, AppraisalItemUpdate, AppraisalItemReorder, AppraisalSchemaResponse
from app.schemas.appraisal_constants import ROOM_AREA_OPTIONS, FLOOR_BUILDING_OPTIONS, ITEM_TYPE_OPTIONS, TYPE_ATTRIBUTES, REQUIRED_ATTRIBUTES
from app.schemas.item_description_templates import get_description_template, ITEM_DESCRIPTION_TEMPLATES

router = APIRouter()

@router.get("/schema", response_model=AppraisalSchemaResponse)
async def get_appraisal_schema():
    """Get appraisal schema with dropdown options and type attributes"""
    return AppraisalSchemaResponse(
        room_area_options=ROOM_AREA_OPTIONS,
        floor_building_options=FLOOR_BUILDING_OPTIONS,
        item_type_options=ITEM_TYPE_OPTIONS,
        type_attributes=TYPE_ATTRIBUTES,
        required_attributes=REQUIRED_ATTRIBUTES,
        description_templates=ITEM_DESCRIPTION_TEMPLATES
    )

@router.get("/description-template/{item_type}")
async def get_description_template_for_type(item_type: str):
    """Get description template for specific item type"""
    template = get_description_template(item_type)
    return {"template": template, "item_type": item_type}

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

@router.post("/appraisal-items")
async def create_appraisal_item(
    item_create: AppraisalItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new appraisal item"""
    try:
        item = AppraisalService.create_appraisal_item(db, item_create)
        return {
            "id": item.id,
            "project_id": item.project_id,
            "item_type": item.item_type,
            "line_number": item.line_number,
            "sort_order": item.sort_order,
            "attributes": item.attributes,
            "message": "Item created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create appraisal item: {str(e)}"
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