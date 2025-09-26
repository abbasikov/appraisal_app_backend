#!/usr/bin/env python3
"""
Script to add the Estate Template Jewelry Appraisal as a default template
"""

import os
import sys
import shutil
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine, text
from core.config import settings
from utils.template_converter import convert_docx_to_fillable

def add_estate_template():
    """Process and add the Estate Template Jewelry Appraisal as default"""
    engine = create_engine(settings.DATABASE_URL)
    
    template_filename = "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"
    
    # Check multiple possible locations for the template file
    possible_paths = [
        template_filename,  # Current directory
        os.path.join("templates", "seed", template_filename),  # Seed directory
        os.path.join("..", template_filename),  # Parent directory
    ]
    
    template_path = None
    for path in possible_paths:
        if os.path.exists(path):
            template_path = path
            break
    
    if not template_path:
        print(f"❌ Template file '{template_filename}' not found in any of these locations:")
        for path in possible_paths:
            print(f"   - {os.path.abspath(path)}")
        return
    
    print(f"🔄 Processing template: {template_path}")
    
    try:
        # Create directories
        os.makedirs("templates/original", exist_ok=True)
        os.makedirs("templates/fillable", exist_ok=True)
        
        # File paths
        original_path = f"templates/original/{template_filename}"
        fillable_path = f"templates/fillable/{template_filename}"
        
        # Copy to original directory
        shutil.copy2(template_path, original_path)
        
        # Process template to extract fields
        conversion_result = convert_docx_to_fillable(original_path, fillable_path)
        field_mappings = conversion_result.get("field_mappings", {})
        
        print(f"✅ Extracted {len(field_mappings)} fields from template")
        
        # Add to database
        with engine.connect() as conn:
            # Check if already exists
            result = conn.execute(text("""
                SELECT id FROM templates WHERE name = 'Estate Jewelry Appraisal Template'
            """))
            
            if result.fetchone():
                print("✅ Template already exists in database")
                return
            
            # Insert template
            conn.execute(text("""
                INSERT INTO templates (
                    name, description, appraisal_type, file_path, fillable_file_path,
                    field_mappings, is_active, version, created_at
                ) VALUES (
                    :name, :description, :appraisal_type, :file_path, :fillable_file_path,
                    :field_mappings, :is_active, :version, :created_at
                )
            """), {
                "name": "Estate Jewelry Appraisal Template",
                "description": "Professional estate jewelry appraisal template - available to all users",
                "appraisal_type": "ESTATE",
                "file_path": original_path,
                "fillable_file_path": fillable_path,
                "field_mappings": json.dumps(field_mappings),
                "is_active": True,
                "version": "1.0",
                "created_at": datetime.now()
            })
            
            conn.commit()
            print("✅ Successfully added Estate Jewelry template to database")
            print("📋 Template is now available to all users")
            
    except Exception as e:
        print(f"❌ Error processing template: {e}")

if __name__ == "__main__":
    add_estate_template()