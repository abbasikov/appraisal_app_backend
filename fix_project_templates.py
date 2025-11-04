#!/usr/bin/env python3
"""
Script to assign templates to existing projects based on appraisal type
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db
from app.models.project import Project
from app.models.template import Template

def fix_project_templates():
    """Assign templates to projects based on appraisal type"""
    db = next(get_db())
    
    try:
        # Get all projects without templates
        projects = db.query(Project).filter(Project.template_id.is_(None)).all()
        print(f"Found {len(projects)} projects without templates")
        
        # Get available templates
        templates = db.query(Template).filter(Template.is_active == True).all()
        template_map = {t.appraisal_type: t.id for t in templates}
        print(f"Available templates: {template_map}")
        
        updated_count = 0
        for project in projects:
            appraisal_type = project.appraisal_type if isinstance(project.appraisal_type, str) else project.appraisal_type.value
            if appraisal_type in template_map:
                project.template_id = template_map[appraisal_type]
                print(f"Updated project {project.id} ({project.project_name}) with template {template_map[appraisal_type]}")
                updated_count += 1
            else:
                print(f"No template found for {appraisal_type} (project {project.id})")
        
        db.commit()
        print(f"✅ Updated {updated_count} projects with templates")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_project_templates()