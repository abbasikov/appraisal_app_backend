from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime
from app.models.appraisal_item import AppraisalItem
from app.models.photo import Photo
from app.models.project import Project
from app.schemas.appraisal_item import AppraisalItemCreate, AppraisalItemUpdate, AppraisalItemReorder

class AppraisalService:
    
    @staticmethod
    def _touch_project_updated_at(db: Session, project_id: int) -> None:
        """Update the project's updated_at timestamp to reflect changes"""
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.updated_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def create_items_from_photos(db: Session, project_id: int, user_id: int) -> List[AppraisalItem]:
        """Create appraisal items from project photos"""
        try:
            # Get all photos for the project
            photos = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(Photo.sort_order.asc()).all()
            
            # Get existing items to avoid duplicates
            existing_photo_ids = set(
                item.photo_id for item in db.query(AppraisalItem).filter(
                    AppraisalItem.project_id == project_id,
                    AppraisalItem.photo_id.isnot(None)
                ).all()
            )
            
            # Filter out photos that already have items
            photos_to_process = [photo for photo in photos if photo.id not in existing_photo_ids]
            
            # Create new items from photos that don't have items yet
            items = []
            existing_count = db.query(AppraisalItem).filter(AppraisalItem.project_id == project_id).count()
            
            for index, photo in enumerate(photos_to_process):
                item = AppraisalItem(
                    project_id=project_id,
                    photo_id=photo.id,
                    line_number=existing_count + index + 1,
                    sort_order=existing_count + index + 1,
                    description=f"Item from {photo.original_filename}"
                )
                db.add(item)
                items.append(item)
            
            db.commit()
            
            # Update project's updated_at if new items were created
            if items:
                AppraisalService._touch_project_updated_at(db, project_id)
            
            # Return all items for the project (existing + new)
            return db.query(AppraisalItem).filter(
                AppraisalItem.project_id == project_id
            ).order_by(AppraisalItem.sort_order.asc()).all()
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_appraisal_items(db: Session, project_id: int) -> List[dict]:
        """Get all appraisal items for a project with photo data, excluding items with deleted photos"""
        try:
            items = db.query(AppraisalItem, Photo).outerjoin(
                Photo, AppraisalItem.photo_id == Photo.id
            ).filter(
                AppraisalItem.project_id == project_id
            ).order_by(Photo.exif_date.asc().nullslast(), AppraisalItem.sort_order.asc()).all()
            
            result = []
            line_number = 1  # Sequential numbering
            
            for item, photo in items:
                # Skip items that have a photo_id but the photo is deleted
                if item.photo_id and photo and photo.is_deleted:
                    continue
                
                # Skip items that have a photo_id but the photo doesn't exist
                if item.photo_id and not photo:
                    continue
                
                item_data = {
                    "id": item.id,
                    "project_id": item.project_id,
                    "photo_id": item.photo_id,
                    "line_number": line_number,  # Sequential numbering
                    "room_area": item.room_area,
                    "floor_building": getattr(item, 'floor_building', None),
                    "item_type": item.item_type,
                    "description": item.description,
                    "appraised_value": float(item.appraised_value) if item.appraised_value else 0.0,
                    "photos": getattr(item, 'photos', []) or [],
                    "attributes": getattr(item, 'attributes', {}) or {},
                    "sort_order": item.sort_order,
                    "created_at": item.created_at,
                    "updated_at": item.updated_at,
                    "photo_thumbnail": photo.thumbnail_path if photo else None,
                    "photo_filename": photo.original_filename if photo else None
                }
                
                result.append(item_data)
                line_number += 1  # Increment for next item
            
            return result
            
        except Exception as e:
            raise e
    
    @staticmethod
    def create_appraisal_item(db: Session, item_create: AppraisalItemCreate) -> AppraisalItem:
        """Create a new appraisal item"""
        try:
            # Create new item
            item = AppraisalItem(
                project_id=item_create.project_id,
                photo_id=item_create.photo_id,
                line_number=item_create.line_number,
                room_area=item_create.room_area,
                floor_building=item_create.floor_building,
                item_type=item_create.item_type,
                description=item_create.description,
                appraised_value=item_create.appraised_value,
                attributes=item_create.attributes,
                sort_order=item_create.sort_order
            )
            
            db.add(item)
            db.commit()
            db.refresh(item)
            
            # Update project's updated_at to reflect this change
            AppraisalService._touch_project_updated_at(db, item_create.project_id)
            
            return item
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def update_appraisal_item(db: Session, item_id: int, item_update: AppraisalItemUpdate) -> Optional[AppraisalItem]:
        """Update an appraisal item"""
        try:
            item = db.query(AppraisalItem).filter(AppraisalItem.id == item_id).first()
            if not item:
                return None
            
            # Update fields if provided
            if item_update.line_number is not None:
                item.line_number = item_update.line_number
            
            update_data = item_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            
            db.commit()
            db.refresh(item)
            
            # Update project's updated_at to reflect this change
            AppraisalService._touch_project_updated_at(db, item.project_id)
            
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
            
            # Update project's updated_at to reflect this change
            AppraisalService._touch_project_updated_at(db, project_id)
            
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
            
            # Update project's updated_at to reflect this change
            AppraisalService._touch_project_updated_at(db, project_id)
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e