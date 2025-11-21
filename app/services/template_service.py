import os
import shutil
from typing import List, Optional, Dict
from sqlalchemy.orm import Session, joinedload
from fastapi import UploadFile, HTTPException
from app.models.template import Template
from app.models.project import Project
from app.models.report import Report, ReportType
from app.utils.template_converter import (
    convert_docx_to_fillable, 
    generate_report_from_template,
    ConversionError,
    ReportGenerationError
)
import logging

logger = logging.getLogger(__name__)

class TemplateService:
    
    @staticmethod
    def upload_template(db: Session, file: UploadFile, appraisal_type: str, 
                       description: str, user_id: int) -> Template:
        """Upload and convert template file"""
        try:
            if not file.filename.endswith('.docx'):
                raise HTTPException(status_code=400, detail="Only .docx files are supported")
            
            if file.size and file.size > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
            
            template_dir = os.path.join("templates")
            original_dir = os.path.join(template_dir, "original")
            fillable_dir = os.path.join(template_dir, "fillable")
            
            os.makedirs(original_dir, exist_ok=True)
            os.makedirs(fillable_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time() * 1000)
            base_name = os.path.splitext(file.filename)[0]
            
            original_filename = f"{timestamp}_{base_name}_original.docx"
            original_path = os.path.join(original_dir, original_filename)
            
            with open(original_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            fillable_filename = f"{timestamp}_{base_name}_fillable.docx"
            fillable_path = os.path.join(fillable_dir, fillable_filename)
            
            try:
                conversion_result = convert_docx_to_fillable(original_path, fillable_path)
                field_mappings = conversion_result["field_mappings"]
            except ConversionError as e:
                field_mappings = {}
                logger.warning(f"Template conversion failed for {file.filename}: {str(e)}")
            
            template = Template(
                name=base_name,
                appraisal_type=appraisal_type,
                file_path=original_path,
                fillable_file_path=fillable_path if os.path.exists(fillable_path) else None,
                description=description,
                field_mappings=field_mappings,
                created_by=user_id
            )
            
            db.add(template)
            db.commit()
            db.refresh(template)
            
            return template
            
        except Exception as e:
            db.rollback()
            logger.error(f"Template upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Template upload failed: {str(e)}")
    
    @staticmethod
    def get_templates(db: Session, appraisal_type: str = None, 
                     is_active: bool = True) -> List[Template]:
        """Get filtered templates"""
        query = db.query(Template).filter(Template.is_active == is_active)
        
        if appraisal_type:
            query = query.filter(Template.appraisal_type == appraisal_type)
        
        return query.order_by(Template.created_at.desc()).all()
    
    @staticmethod
    def get_template_by_id(db: Session, template_id: int) -> Optional[Template]:
        """Get template by ID"""
        return db.query(Template).filter(Template.id == template_id).first()
    
    @staticmethod
    def update_field_mappings(db: Session, template_id: int, 
                             field_mappings: Dict) -> Template:
        """Update template field mappings"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template.field_mappings = field_mappings
        db.commit()
        db.refresh(template)
        
        return template
    
    @staticmethod
    def generate_report(db: Session, template_id: int, project_id: int, 
                       report_type: str = "final", did_inspect: Optional[bool] = None) -> str:
        """Generate report from template and project data"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            project = db.query(Project).options(joinedload(Project.account)).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Get appraisal items for this project
            from app.models.appraisal_item import AppraisalItem
            appraisal_items = db.query(AppraisalItem).filter(
                AppraisalItem.project_id == project_id
            ).order_by(AppraisalItem.sort_order).all()
            
            # Get all photos for this project
            from app.models.photo import Photo
            all_project_photos = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(Photo.sort_order.asc()).all()
            
            # Calculate total value from items
            total_value = sum(item.appraised_value or 0 for item in appraisal_items)
            
            # Debug client data
            logger.info(f"Client data from database:")
            if project.client:
                logger.info(f"  - case_name: '{project.client.case_name}'")
                logger.info(f"  - case_number: '{project.client.case_number}'")
                logger.info(f"  - date_of_death: '{project.client.date_of_death}'")
                logger.info(f"  - attorney_name: '{project.client.attorney_name}'")
            else:
                logger.warning("No client data found for project")
            
            # Extract template type from template name BEFORE creating project_data
            template_type = project.appraisal_type.value if project.appraisal_type else ""
            
            # Try to extract the actual item type from template name
            import re
            template_name_lower = template.name.lower()
            keywords = ['wine', 'wines', 'coin', 'coins', 'jewellery', 'jewelry', 'artwork', 'art', 
                       'auto', 'automobile', 'firearms', 'firearm', 'handbag', 'handbags', 'watch', 
                       'watches', 'content', 'contents', 'inventory']
            
            words = re.split(r'[\s\-_]+', template_name_lower)
            for word in words:
                if word in keywords:
                    template_type = word.capitalize() if word != 'jewelry' else 'Jewellery'
                    if word in ['wines']: template_type = 'Wine'
                    elif word in ['coins']: template_type = 'Coins'
                    elif word in ['contents', 'inventory']: template_type = 'Contents'
                    elif word in ['watches']: template_type = 'Watches'
                    elif word in ['art']: template_type = 'Artwork'
                    elif word in ['auto', 'automobile']: template_type = 'Auto'
                    elif word in ['firearms', 'firearm']: template_type = 'Firearms'
                    elif word in ['handbags']: template_type = 'Handbag'
                    break
            
            logger.info(f"Detected template_type: '{template_type}' from template name: '{template.name}'")
            
            # Load account data
            logger.info(f"Loading account data for project.account_id: {project.account_id}")
            account_dict = {}
            if project.account_id:
                if project.account:
                    account_dict = {
                        "id": project.account.id,
                        "name": project.account.name,
                        "account_type": project.account.account_type.value if project.account.account_type else "",
                        "address": project.account.address or "",
                        "city": project.account.city or "",
                        "state": project.account.state or "",
                        "zip_code": project.account.zip_code or "",
                        "phone": project.account.phone or "",
                        "email": project.account.email or ""
                    }
                    logger.info(f"✅ Account loaded from relationship: name='{account_dict.get('name', '')}'")
                else:
                    # Fallback: manual query if relationship didn't load
                    from app.models.account import Account
                    account = db.query(Account).filter(Account.id == project.account_id).first()
                    if account:
                        account_dict = {
                            "id": account.id,
                            "name": account.name,
                            "account_type": account.account_type.value if account.account_type else "",
                            "address": account.address or "",
                            "city": account.city or "",
                            "state": account.state or "",
                            "zip_code": account.zip_code or "",
                            "phone": account.phone or "",
                            "email": account.email or ""
                        }
                        logger.info(f"✅ Account loaded manually: name='{account_dict.get('name', '')}'")
                    else:
                        logger.warning(f"❌ Account with ID {project.account_id} not found")
            else:
                logger.warning("⚠️  No account_id set for this project")
            
            project_data = {
                "project_name": project.project_name,
                "case_number": project.case_number,
                "appraisal_type": template_type,  # Use detected template type instead of domain
                "appraisal_domain": project.appraisal_type.value if project.appraisal_type else "",  # Keep domain separate
                "inspection_date": str(project.inspection_date) if project.inspection_date else "",
                "report_date": str(project.report_date) if project.report_date else "",
                "effective_date": str(project.effective_date) if project.effective_date else "",
                "appraisal_location": project.appraisal_location if project.appraisal_location else "",
                "total_value": str(total_value),
                "item_count": str(len(appraisal_items)),
                "did_inspect": did_inspect,
                "account": account_dict,  # Add account data here
                "client": {
                    "name": project.client.name if project.client else "",
                    "attorney_name": project.client.attorney_name if project.client else "",
                    "address": f"{project.client.address or ''} {project.client.city or ''} {project.client.state or ''} {project.client.zip_code or ''}" if project.client else "",
                    "email": project.client.email if project.client else "",
                    "phone": project.client.phone if project.client else "",
                    "date_of_death": str(project.client.date_of_death) if project.client and project.client.date_of_death else "",
                    "case_name": project.client.case_name if project.client else "",
                    "case_number": project.client.case_number if project.client else "",
                    "attorney_email": project.client.attorney_email if project.client else "",
                    "attorney_phone": project.client.attorney_phone if project.client else ""
                },
                "appraisal_items": [
                    {
                        "id": item.id,
                        "description": item.description or "",
                        "appraised_value": item.appraised_value or 0,
                        "room_area": getattr(item, 'room_area', None),
                        "floor_building": getattr(item, 'floor_building', None),
                        "item_type": item.item_type,
                        "attributes": getattr(item, 'attributes', {}) or {},
                        "photos": getattr(item, 'photos', []) or [],
                        "photo_path": item.photo.file_path if item.photo else None,
                        "photo_thumbnail": item.photo.thumbnail_path if item.photo else None
                    } for item in appraisal_items
                ],
                "all_project_photos": [
                    {
                        "id": photo.id,
                        "file_path": photo.file_path,
                        "thumbnail_path": photo.thumbnail_path,
                        "original_filename": photo.original_filename,
                        "sort_order": photo.sort_order
                    } for photo in all_project_photos
                ]
            }
            
            generated_dir = os.path.join("templates", "generated")
            os.makedirs(generated_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time() * 1000)
            output_filename = f"{project_id}_{template_id}_{report_type}_{timestamp}.docx"
            output_path = os.path.join(generated_dir, output_filename)
            
            template_path = template.fillable_file_path or template.file_path
            
            # Detect template category and extract template type
            from app.utils.template_detector import detect_template_category
            template_category = detect_template_category(template.name)
            
            # Extract template type (wine, jewellery, coin, etc.) from template name
            template_type = project.appraisal_type.value if project.appraisal_type else ""
            
            # Try to extract the actual item type from template name
            import re
            template_name_lower = template.name.lower()
            keywords = ['wine', 'wines', 'coin', 'coins', 'jewellery', 'jewelry', 'artwork', 'art', 
                       'auto', 'automobile', 'firearms', 'firearm', 'handbag', 'handbags', 'watch', 
                       'watches', 'content', 'contents', 'inventory']
            
            words = re.split(r'[\s\-_]+', template_name_lower)
            for word in words:
                if word in keywords:
                    template_type = word.capitalize() if word != 'jewelry' else 'Jewellery'
                    if word in ['wines']: template_type = 'Wine'
                    elif word in ['coins']: template_type = 'Coins'
                    elif word in ['contents', 'inventory']: template_type = 'Contents'
                    elif word in ['watches']: template_type = 'Watches'
                    elif word in ['art']: template_type = 'Artwork'
                    elif word in ['auto', 'automobile']: template_type = 'Auto'
                    elif word in ['firearms', 'firearm']: template_type = 'Firearms'
                    elif word in ['handbags']: template_type = 'Handbag'
                    break
            
            logger.info(f"Generating report with category='{template_category.value}', template_type='{template_type}', report_type='{report_type}', add_watermark={report_type == 'draft'}")
            logger.info(f"📊 Using {len(appraisal_items)} items from JSONB attributes (scalable approach)")
            
            generated_path = generate_report_from_template(
                template_path, output_path, 
                template.field_mappings or {}, project_data,
                template_category=template_category.value,
                add_watermark=(report_type == "draft"),
                did_inspect=did_inspect
            )
            
            report = Report(
                project_id=project_id,
                template_id=template_id,
                template_name=template.name,
                report_type=ReportType.DRAFT if report_type == "draft" else ReportType.FINAL,
                word_path=generated_path,
                has_watermark=report_type == "draft"
            )
            
            db.add(report)
            db.commit()
            
            return generated_path
            
        except Exception as e:
            db.rollback()
            logger.error(f"Report generation failed: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
    
    @staticmethod
    def generate_template_with_mappings(db: Session, template_id: int) -> str:
        """Generate template with current field mappings applied"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Create mock project data using field mapping defaults
        mock_data = {}
        if template.field_mappings:
            for field_name, field_config in template.field_mappings.items():
                mock_data[field_name] = field_config.get('default_value', f'[{field_name}]')
        
        # Generate output path
        generated_dir = os.path.join("templates", "generated")
        os.makedirs(generated_dir, exist_ok=True)
        
        import time
        timestamp = int(time.time() * 1000)
        output_filename = f"{template_id}_updated_{timestamp}.docx"
        output_path = os.path.join(generated_dir, output_filename)
        
        # Use fillable template if available, otherwise original
        template_path = template.fillable_file_path or template.file_path
        
        # Generate template with field mappings
        from app.utils.template_converter import generate_report_from_template
        generated_path = generate_report_from_template(
            template_path, output_path, 
            template.field_mappings or {}, {'field_mappings': mock_data},
            add_watermark=False  # No watermark for template generation
        )
        
        return generated_path
    
    @staticmethod
    def delete_template(db: Session, template_id: int) -> bool:
        """Soft delete template"""
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        template.is_active = False
        db.commit()
        
        return True