from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from app.models.appraisal_item import AppraisalItem
from app.models.photo import Photo
from app.models.project import Project
from app.schemas.appraisal_item import AppraisalItemCreate, AppraisalItemUpdate, AppraisalItemReorder

class AppraisalService:
    
    @staticmethod
    def create_items_from_photos(db: Session, project_id: int, user_id: int) -> List[AppraisalItem]:
        """Create appraisal items from project photos"""
        try:
            # Get all photos for the project
            photos = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(Photo.sort_order.asc()).all()
            
            # Check if items already exist
            existing_items = db.query(AppraisalItem).filter(
                AppraisalItem.project_id == project_id
            ).count()
            
            if existing_items > 0:
                # Return existing items
                return db.query(AppraisalItem).filter(
                    AppraisalItem.project_id == project_id
                ).order_by(AppraisalItem.sort_order.asc()).all()
            
            # Create new items from photos
            items = []
            for index, photo in enumerate(photos):
                item = AppraisalItem(
                    project_id=project_id,
                    photo_id=photo.id,
                    line_number=index + 1,
                    sort_order=index + 1,
                    description=f"Item from {photo.original_filename}"
                )
                db.add(item)
                items.append(item)
            
            db.commit()
            return items
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_appraisal_items(db: Session, project_id: int) -> List[dict]:
        """Get all appraisal items for a project with photo data"""
        try:
            items = db.query(AppraisalItem, Photo).outerjoin(
                Photo, AppraisalItem.photo_id == Photo.id
            ).filter(
                AppraisalItem.project_id == project_id
            ).order_by(AppraisalItem.sort_order.asc()).all()
            
            result = []
            for item, photo in items:
                item_data = {
                    "id": item.id,
                    "project_id": item.project_id,
                    "photo_id": item.photo_id,
                    "line_number": item.line_number,
                    "room_area": item.room_area,
                    "item_type": item.item_type,
                    "description": item.description,
                    "appraised_value": float(item.appraised_value) if item.appraised_value else 0.0,
                    "sort_order": item.sort_order,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "photo_thumbnail": photo.thumbnail_path if photo else None,
                    "photo_filename": photo.original_filename if photo else None
                }
                

                
                result.append(item_data)
            
            return result
            
        except Exception as e:
            raise e
    
    @staticmethod
    def update_appraisal_item(db: Session, item_id: int, item_update: AppraisalItemUpdate) -> Optional[AppraisalItem]:
        """Update an appraisal item"""
        try:
            item = db.query(AppraisalItem).filter(AppraisalItem.id == item_id).first()
            if not item:
                return None
            
            update_data = item_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            
            db.commit()
            db.refresh(item)
            return item
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def reorder_items(db: Session, project_id: int, reorder_data: List[AppraisalItemReorder]) -> bool:
        """Reorder appraisal items"""
        try:
            for reorder in reorder_data:
                item = db.query(AppraisalItem).filter(
                    AppraisalItem.id == reorder.item_id,
                    AppraisalItem.project_id == project_id
                ).first()
                
                if item:
                    item.sort_order = reorder.new_sort_order
            
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_appraisal_item(db: Session, item_id: int, project_id: int) -> bool:
        """Delete an appraisal item"""
        try:
            item = db.query(AppraisalItem).filter(
                AppraisalItem.id == item_id,
                AppraisalItem.project_id == project_id
            ).first()
            
            if not item:
                return False
            
            db.delete(item)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            raise e