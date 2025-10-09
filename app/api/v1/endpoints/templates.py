from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.template_service import TemplateService
from app.schemas.template import (
    TemplateResponse, 
    FieldMappingUpdate, 
    ReportGenerationRequest,
    TemplateListResponse
)

router = APIRouter()

@router.get("/", response_model=TemplateListResponse)
def list_templates(
    appraisal_type: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List templates with filtering"""
    templates = TemplateService.get_templates(db, appraisal_type, is_active)
    return TemplateListResponse(
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=len(templates)
    )

@router.post("/upload", response_model=TemplateResponse)
def upload_template(
    file: UploadFile = File(...),
    appraisal_type: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload new template"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = TemplateService.upload_template(
        db, file, appraisal_type, description, current_user.id
    )
    return TemplateResponse.model_validate(template)

@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get template details"""
    template = TemplateService.get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return TemplateResponse.model_validate(template)

@router.put("/{template_id}/mappings", response_model=TemplateResponse)
def update_field_mappings(
    template_id: int,
    field_mappings: FieldMappingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update template field mappings"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    template = TemplateService.update_field_mappings(
        db, template_id, field_mappings.field_mappings
    )
    return TemplateResponse.model_validate(template)

@router.post("/{template_id}/generate")
def generate_report(
    template_id: int,
    request: ReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate report from template"""
    report_path = TemplateService.generate_report(
        db, template_id, request.project_id, request.report_type
    )
    
    return {
        "message": "Report generated successfully",
        "report_path": report_path,
        "template_id": template_id,
        "project_id": request.project_id,
        "download_url": f"/api/v1/templates/{template_id}/download-report?project_id={request.project_id}&report_type={request.report_type}"
    }

@router.get("/{template_id}/download-report")
def download_generated_report(
    template_id: int,
    project_id: int,
    report_type: str = "final",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download generated report"""
    from fastapi.responses import FileResponse
    from app.models.report import Report
    import os
    
    # Find the most recent report
    from app.models.report import ReportType
    report_type_enum = ReportType.DRAFT if report_type == "draft" else ReportType.FINAL
    
    report = db.query(Report).filter(
        Report.template_id == template_id,
        Report.project_id == project_id,
        Report.report_type == report_type_enum
    ).order_by(Report.created_at.desc()).first()
    
    if not report or not report.word_path or not os.path.exists(report.word_path):
        raise HTTPException(status_code=404, detail="Generated report not found")
    
    filename = f"report_{project_id}_{template_id}_{report_type}.docx"
    return FileResponse(report.word_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.get("/{template_id}/download")
def download_template(
    template_id: int,
    file_type: str = "original",  # original, fillable, or updated
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download template file"""
    from fastapi.responses import FileResponse
    import os
    
    template = TemplateService.get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if file_type == "updated":
        # Generate template with current field mappings
        updated_path = TemplateService.generate_template_with_mappings(db, template_id)
        filename = f"{template.name}_updated.docx"
        return FileResponse(updated_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    
    file_path = template.fillable_file_path if file_type == "fillable" and template.fillable_file_path else template.file_path
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template file not found")
    
    filename = f"{template.name}_{file_type}.docx"
    return FileResponse(file_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete template"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = TemplateService.delete_template(db, template_id)
    if success:
        return {"message": "Template deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete template")