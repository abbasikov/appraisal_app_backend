import os
import shutil
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
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
                       report_type: str = "draft") -> str:
        """Generate report from template and project data"""
        try:
            template = db.query(Template).filter(Template.id == template_id).first()
            if not template:
                raise HTTPException(status_code=404, detail="Template not found")
            
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            
            project_data = {
                "project_name": project.project_name,
                "case_number": project.case_number,
                "appraisal_type": project.appraisal_type.value if project.appraisal_type else "",
                "inspection_date": str(project.inspection_date) if project.inspection_date else "",
                "report_date": str(project.report_date) if project.report_date else "",
                "total_value": str(project.total_value) if project.total_value else "",
                "item_count": str(project.item_count) if project.item_count else "",
                "client": {
                    "name": project.client.name if project.client else "",
                    "attorney_name": project.client.attorney_name if project.client else "",
                    "address": f"{project.client.address or ''} {project.client.city or ''} {project.client.state or ''} {project.client.zip_code or ''}" if project.client else "",
                    "email": project.client.email if project.client else "",
                    "phone": project.client.phone if project.client else ""
                }
            }
            
            generated_dir = os.path.join("templates", "generated")
            os.makedirs(generated_dir, exist_ok=True)
            
            import time
            timestamp = int(time.time() * 1000)
            output_filename = f"{project_id}_{template_id}_{report_type}_{timestamp}.docx"
            output_path = os.path.join(generated_dir, output_filename)
            
            template_path = template.fillable_file_path or template.file_path
            
            generated_path = generate_report_from_template(
                template_path, output_path, 
                template.field_mappings or {}, project_data
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
            template.field_mappings or {}, {'field_mappings': mock_data}
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