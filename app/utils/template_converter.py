import re
import os
from typing import Dict, List, Tuple, Optional
from docx import Document
from docx.shared import Inches, RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.shared import OxmlElement, qn
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
import logging
from datetime import datetime


logger = logging.getLogger(__name__)

class TemplateError(Exception):
    pass

class ConversionError(TemplateError):
    pass

class ReportGenerationError(TemplateError):
    pass

FIELD_PATTERNS = [
    (r'\{([^{}]+)\}', 'curly_bracket'),                    # {field_name} - ONLY format supported
]

def convert_docx_to_fillable(input_path: str, output_path: str) -> Dict:
    """Convert Word document to fillable template with field extraction"""
    try:
        if not os.path.exists(input_path):
            raise ConversionError(f"Input file not found: {input_path}")
        
        doc = Document(input_path)
        field_mappings = extract_field_mappings(doc)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        return {
            "field_mappings": field_mappings,
            "field_count": len(field_mappings),
            "conversion_status": "success"
        }
        
    except Exception as e:
        logger.error(f"Template conversion failed: {str(e)}")
        raise ConversionError(f"Failed to convert template: {str(e)}")

def extract_field_mappings(doc: Document) -> Dict:
    """Extract field mappings from document - only {field_name} format"""
    field_mappings = {}
    field_counter = 1
    
    # Extract from paragraphs
    for paragraph in doc.paragraphs:
        fields = _extract_fields_from_text(paragraph.text)
        for field_name, field_type in fields:
            if field_name not in field_mappings:
                field_mappings[field_name] = {
                    "id": f"field_{field_counter}",
                    "label": field_name,
                    "type": _determine_field_type(field_name),
                    "required": False,
                    "default_value": "",
                    "options": []
                }
                field_counter += 1
    
    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    fields = _extract_fields_from_text(paragraph.text)
                    for field_name, field_type in fields:
                        if field_name not in field_mappings:
                            field_mappings[field_name] = {
                                "id": f"field_{field_counter}",
                                "label": field_name,
                                "type": _determine_field_type(field_name),
                                "required": False,
                                "default_value": "",
                                "options": []
                            }
                            field_counter += 1
    
    # No common fields auto-added - only extract what's actually in the template
    
    return field_mappings

def _extract_fields_from_text(text: str) -> List[Tuple[str, str]]:
    """Extract field names from text using only {field_name} pattern"""
    fields = []
    
    pattern, pattern_type = FIELD_PATTERNS[0]  # Only curly bracket pattern
    matches = re.finditer(pattern, text)
    for match in matches:
        field_name = match.group(1).strip()
        if field_name and len(field_name) > 0 and field_name not in [f[0] for f in fields]:
            fields.append((field_name, pattern_type))
    
    return fields

def _determine_field_type(field_name: str) -> str:
    """Determine field type based on field name"""
    field_lower = field_name.lower()
    
    if any(word in field_lower for word in ['date', 'inspection', 'report']):
        return 'date'
    elif any(word in field_lower for word in ['value', 'price', 'cost', 'amount', 'appraised']):
        return 'currency'
    elif any(word in field_lower for word in ['count', 'number', 'quantity']):
        return 'number'
    elif any(word in field_lower for word in ['address', 'description', 'notes', 'comments']):
        return 'textarea'
    elif any(word in field_lower for word in ['photo', 'image', 'picture']):
        return 'image'
    else:
        return 'text'

def generate_report_from_template(template_path: str, output_path: str, 
                                field_mappings: Dict, project_data: Dict, 
                                template_category: str = "image_based",
                                add_watermark: bool = False,
                                did_inspect: Optional[bool] = None) -> str:
    """Generate report from template using project data"""
    try:
        doc = Document(template_path)
        logger.info("⭐⭐⭐ DOCUMENT LOADED SUCCESSFULLY ⭐⭐⭐")
        
        # STEP 1: Handle text boxes FIRST (they are most sensitive to document structure changes)
        logger.info("💬💬💬 STEP 1: PROCESSING TEXT BOXES (BEFORE ANY OTHER MODIFICATIONS) 💬💬💬")
        _handle_textboxes_first_page(doc, field_mappings, project_data)
        logger.info("💬💬💬 TEXT BOX PROCESSING COMPLETED 💬💬💬")
        
        # STEP 2: Do a comprehensive placeholder replacement for regular content
        # This ensures placeholders are replaced while document structure is intact
        logger.info("🔍🔍🔍 STEP 2: PERFORMING COMPREHENSIVE PLACEHOLDER REPLACEMENT 🔍🔍🔍")
        _final_placeholder_check(doc, field_mappings, project_data)
        logger.info("🔍🔍🔍 COMPREHENSIVE PLACEHOLDER REPLACEMENT COMPLETED 🔍🔍🔍")
        
        # STEP 3: Additional paragraph processing (backup)
        for paragraph in doc.paragraphs:
            _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # STEP 4: Process tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Replace text fields in headers and footers
        for section in doc.sections:
            # Process header
            if section.header:
                for paragraph in section.header.paragraphs:
                    _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
                # Process tables in header
                for table in section.header.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
            
            # Process footer
            if section.footer:
                for paragraph in section.footer.paragraphs:
                    _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
                # Process tables in footer
                for table in section.footer.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Handle category-specific rendering
        from app.utils.template_detector import TemplateCategory
        
        logger.info(f"📋📋📋 TEMPLATE CATEGORY: {template_category} 📋📋📋")
        
        if template_category == TemplateCategory.IMAGE_BASED.value or template_category == "image_based":
            # Use existing image-based logic (BACKWARD COMPATIBLE)
            logger.info("🖼️ Using IMAGE-BASED rendering (photos + descriptions)")
        _handle_appraisal_items(doc, project_data)
        
#-----
        if template_category == TemplateCategory.COIN.value or template_category == "coin":
            # Use table-based logic for coins
            logger.info("🪙 Using COIN TABLE rendering")
            _handle_coin_table(doc, project_data)
        
        elif template_category == TemplateCategory.CONTENT.value or template_category == "content":
            # Use table-based logic for content/inventory
            logger.info("📦 Using CONTENT INVENTORY TABLE rendering")
            _handle_content_table(doc, project_data)
        
        elif template_category == TemplateCategory.WINE.value or template_category == "wine":
            # Use table-based logic for wine
            logger.info("🍷 Using WINE COLLECTION TABLE rendering")
            _handle_wine_table(doc, project_data)
        
        else:
            # Default to image-based (safe fallback)
            logger.warning(f"⚠️ Unknown category '{template_category}', using IMAGE-BASED as fallback")
            _handle_appraisal_items(doc, project_data)
        
        logger.info("🔥🔥🔥 CATEGORY-SPECIFIC RENDERING COMPLETED 🔥🔥🔥")
        
        # Special pass for headers and footers
        logger.info("🔄🔄🔄 PERFORMING SPECIAL HEADER/FOOTER PLACEHOLDER CHECK 🔄🔄🔄")
        _ensure_headers_footers_replaced(doc, field_mappings, project_data)
        logger.info("🔄🔄🔄 HEADER/FOOTER PLACEHOLDER CHECK COMPLETED 🔄🔄🔄")
        
        # ALWAYS remove any existing watermarks from the template first
        logger.info("🚫🚫🚫 REMOVING EXISTING WATERMARKS FROM TEMPLATE 🚫🚫🚫")
        _remove_existing_watermarks(doc)
        logger.info("🚫🚫🚫 WATERMARK REMOVAL COMPLETED 🚫🚫🚫")
        
        # Add watermark if requested (for draft reports)
        logger.info(f"📝 add_watermark parameter value: {add_watermark}")
        if add_watermark:
            logger.info("💧💧💧 ADDING DRAFT WATERMARK (add_watermark=True) 💧💧💧")
            watermark_success = _add_watermark(doc)
            if watermark_success:
                logger.info("✅✅✅ DRAFT WATERMARK SUCCESSFULLY ADDED ✅✅✅")
            else:
                logger.error("❌❌❌ DRAFT WATERMARK ADDITION FAILED ❌❌❌")
        else:
            logger.info("⏭️ SKIPPING WATERMARK (add_watermark=False) - Final Report ⏭️")
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise ReportGenerationError(f"Failed to generate report: {str(e)}")

def _get_inspection_placeholders(did_inspect: Optional[bool]) -> Dict[str, str]:
    """Get inspection-related placeholder values based on did_inspect flag"""
    if did_inspect is True:
        return {
            'did_personally_inspect': 'did personally inspected',
            'was_present': 'was present'
        }
    elif did_inspect is False:
        return {
            'did_personally_inspect': 'did not personally inspect',
            'was_present': 'was not present'
        }
    else:
        # If not specified, leave empty (placeholder will remain)
        return {
            'did_personally_inspect': '',
            'was_present': ''
        }

def _ensure_headers_footers_replaced(doc: Document, field_mappings: Dict, project_data: Dict):
    """Special pass to ensure all header and footer placeholders are replaced"""
    import re
    pattern = r'\{([^{}]+)\}'
    
    # Special handling for problematic fields
    client_data = project_data.get('client', {})
    account_data = project_data.get('account', {})
    did_inspect = project_data.get('did_inspect')
    inspection_placeholders = _get_inspection_placeholders(did_inspect)
    
    # Ensure we have values for commonly problematic fields

    special_fields = {
        'case_name': client_data.get('case_name', 'Estate Appraisal'),
        'inspection_date': _format_date(project_data.get('inspection_date', '')),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'effective_date': _format_date(project_data.get('effective_date', '')),
        'appraisal_location': project_data.get('appraisal_location', ''),
        'appraisal_type': project_data.get('appraisal_type', ''),
        'client_name': client_data.get('name', 'Client'),
        'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        'death_date': _format_date(client_data.get('date_of_death', '')),
        'project_name': project_data.get('project_name', 'Appraisal Project'),
        'estate_of': client_data.get('name', ''),
            'law_firm': account_data.get('name', ''),  # law_firm uses name from account table
        **inspection_placeholders
    }
    
    logger.info(f"Special field values for header/footer check: {special_fields}")
    
    # Log the number of sections in the document
    section_count = len(doc.sections)
    logger.info(f"Document has {section_count} sections (pages with potentially different headers/footers)")
    
    # Process each section individually to ensure we don't miss any headers
    for section_idx, section in enumerate(doc.sections):
        logger.info(f"Processing section {section_idx+1} of {section_count}")
        
        # Process header
        if section.header:
            # First, get all text from header to check for any placeholders
            header_text = ''
            for paragraph in section.header.paragraphs:
                header_text += paragraph.text
            
            # Check if there are any placeholders in the header
            if '{' in header_text and '}' in header_text:
                logger.info(f"Found potential placeholders in header: '{header_text}'")
                
                # Process each paragraph in the header
                for paragraph in section.header.paragraphs:
                    # Get all text from the paragraph
                    full_text = paragraph.text
                    
                    # Find all placeholders in this paragraph
                    matches = re.findall(pattern, full_text)
                    if matches:
                        logger.info(f"Found placeholders in header paragraph: {matches}")
                        
                        # Process each run individually to preserve formatting
                        if len(paragraph.runs) > 0:
                            # First, check if placeholders span across runs
                            has_split_placeholders = False
                            for field_name in matches:
                                placeholder = '{' + field_name + '}'
                                if placeholder not in paragraph.text:
                                    has_split_placeholders = True
                                    break
                            
                            if has_split_placeholders:
                                # Use our new function that preserves formatting
                                logger.info(f"Found split placeholders in header, using formatting-preserving approach")
                                _replace_split_placeholders_preserve_formatting(paragraph, field_mappings, project_data, special_fields, matches)
                            else:
                                # For non-split placeholders, process each run individually
                                logger.info(f"Processing each run individually in header paragraph")
                                for run in paragraph.runs:
                                    if '{' in run.text and '}' in run.text:
                                        run_text = run.text
                                        for field_name in matches:
                                            placeholder = '{' + field_name + '}'
                                            if placeholder in run_text:
                                                # Check special fields first
                                                if field_name in special_fields:
                                                    value = special_fields[field_name]
                                                    logger.info(f"Using special field value for {field_name} in header run: {value}")
                                                else:
                                                    # Get replacement value
                                                    value = _get_field_value_from_project(field_name, project_data)
                                                    if value is None and field_name in field_mappings:
                                                        value = _get_field_value(field_name, field_mappings[field_name], project_data)
                                                
                                                if value is None:
                                                    value = ''
                                                
                                                # Replace in this run only
                                                run_text = run_text.replace(placeholder, str(value))
                                        
                                        # Update the run text
                                        run.text = run_text
                
                # Process tables in header
                for table in section.header.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                # Similar process for table cells
                                full_text = paragraph.text
                                matches = re.findall(pattern, full_text)
                                
                                if matches:
                                    logger.info(f"Found placeholders in header table: {matches}")
                                    
                                    # Process each run individually to preserve formatting
                                    if len(paragraph.runs) > 0:
                                        # First, check if placeholders span across runs
                                        has_split_placeholders = False
                                        for field_name in matches:
                                            placeholder = '{' + field_name + '}'
                                            if placeholder not in paragraph.text:
                                                has_split_placeholders = True
                                                break
                                        
                                        if has_split_placeholders:
                                            # Use our new function that preserves formatting
                                            logger.info(f"Found split placeholders in header table, using formatting-preserving approach")
                                            _replace_split_placeholders_preserve_formatting(paragraph, field_mappings, project_data, special_fields, matches)
                                        else:
                                            # For non-split placeholders, process each run individually
                                            logger.info(f"Processing each run individually in header table cell")
                                            for run in paragraph.runs:
                                                if '{' in run.text and '}' in run.text:
                                                    run_text = run.text
                                                    for field_name in matches:
                                                        placeholder = '{' + field_name + '}'
                                                        if placeholder in run_text:
                                                            # Check special fields first
                                                            if field_name in special_fields:
                                                                value = special_fields[field_name]
                                                                logger.info(f"Using special field value for {field_name} in header table run: {value}")
                                                            else:
                                                                # Get replacement value
                                                                value = _get_field_value_from_project(field_name, project_data)
                                                                if value is None and field_name in field_mappings:
                                                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                                                            
                                                            if value is None:
                                                                value = ''
                                                            
                                                            # Replace in this run only
                                                            run_text = run_text.replace(placeholder, str(value))
                                                    
                                                    # Update the run text
                                                    run.text = run_text
        
        # Process footer (similar to header)
        if section.footer:
            # First, get all text from footer to check for any placeholders
            footer_text = ''
            for paragraph in section.footer.paragraphs:
                footer_text += paragraph.text
            
            # Check if there are any placeholders in the footer
            if '{' in footer_text and '}' in footer_text:
                logger.info(f"Found potential placeholders in footer: '{footer_text}'")
                
                # Process each paragraph in the footer
                for paragraph in section.footer.paragraphs:
                    # Get all text from the paragraph
                    full_text = paragraph.text
                    
                    # Find all placeholders in this paragraph
                    matches = re.findall(pattern, full_text)
                    if matches:
                        logger.info(f"Found placeholders in footer paragraph: {matches}")
                        
                        # Process each run individually to preserve formatting
                        if len(paragraph.runs) > 0:
                            # First, check if placeholders span across runs
                            has_split_placeholders = False
                            for field_name in matches:
                                placeholder = '{' + field_name + '}'
                                if placeholder not in paragraph.text:
                                    has_split_placeholders = True
                                    break
                            
                            if has_split_placeholders:
                                # Use our new function that preserves formatting
                                logger.info(f"Found split placeholders in footer, using formatting-preserving approach")
                                _replace_split_placeholders_preserve_formatting(paragraph, field_mappings, project_data, special_fields, matches)
                            else:
                                # For non-split placeholders, process each run individually
                                logger.info(f"Processing each run individually in footer paragraph")
                                for run in paragraph.runs:
                                    if '{' in run.text and '}' in run.text:
                                        run_text = run.text
                                        for field_name in matches:
                                            placeholder = '{' + field_name + '}'
                                            if placeholder in run_text:
                                                # Check special fields first
                                                if field_name in special_fields:
                                                    value = special_fields[field_name]
                                                    logger.info(f"Using special field value for {field_name} in footer run: {value}")
                                                else:
                                                    # Get replacement value
                                                    value = _get_field_value_from_project(field_name, project_data)
                                                    if value is None and field_name in field_mappings:
                                                        value = _get_field_value(field_name, field_mappings[field_name], project_data)
                                                
                                                if value is None:
                                                    value = ''
                                                
                                                # Replace in this run only
                                                run_text = run_text.replace(placeholder, str(value))
                                        
                                        # Update the run text
                                        run.text = run_text
                
                # Process tables in footer
                for table in section.footer.tables:
                    for row in table.rows:
                        for cell in row.cells:
                            for paragraph in cell.paragraphs:
                                # Similar process for table cells
                                full_text = paragraph.text
                                matches = re.findall(pattern, full_text)
                                
                                if matches:
                                    logger.info(f"Found placeholders in footer table: {matches}")
                                    
                                    # Process each run individually to preserve formatting
                                    if len(paragraph.runs) > 0:
                                        # First, check if placeholders span across runs
                                        has_split_placeholders = False
                                        for field_name in matches:
                                            placeholder = '{' + field_name + '}'
                                            if placeholder not in paragraph.text:
                                                has_split_placeholders = True
                                                break
                                        
                                        if has_split_placeholders:
                                            # Use our new function that preserves formatting
                                            logger.info(f"Found split placeholders in footer table, using formatting-preserving approach")
                                            _replace_split_placeholders_preserve_formatting(paragraph, field_mappings, project_data, special_fields, matches)
                                        else:
                                            # For non-split placeholders, process each run individually
                                            logger.info(f"Processing each run individually in footer table cell")
                                            for run in paragraph.runs:
                                                if '{' in run.text and '}' in run.text:
                                                    run_text = run.text
                                                    for field_name in matches:
                                                        placeholder = '{' + field_name + '}'
                                                        if placeholder in run_text:
                                                            # Check special fields first
                                                            if field_name in special_fields:
                                                                value = special_fields[field_name]
                                                                logger.info(f"Using special field value for {field_name} in footer table run: {value}")
                                                            else:
                                                                # Get replacement value
                                                                value = _get_field_value_from_project(field_name, project_data)
                                                                if value is None and field_name in field_mappings:
                                                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                                                            
                                                            if value is None:
                                                                value = ''
                                                            
                                                            # Replace in this run only
                                                            run_text = run_text.replace(placeholder, str(value))
                                                    
                                                    # Update the run text
                                                    run.text = run_text

def _final_placeholder_check(doc: Document, field_mappings: Dict, project_data: Dict):
    """Final pass to catch any remaining placeholders in the document"""
    pattern = r'\{([^{}]+)\}'
    
    # Special handling for problematic fields
    client_data = project_data.get('client', {})
    account_data = project_data.get('account', {})
    did_inspect = project_data.get('did_inspect')
    inspection_placeholders = _get_inspection_placeholders(did_inspect)
    
    # Ensure we have values for commonly problematic fields

    special_fields = {
        'case_name': client_data.get('case_name', 'Estate Appraisal'),
        'inspection_date': _format_date(project_data.get('inspection_date', '')),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'effective_date': _format_date(project_data.get('effective_date', '')),
        'appraisal_location': project_data.get('appraisal_location', ''),
        'appraisal_type': project_data.get('appraisal_type', ''),
        'client_name': client_data.get('name', 'Client'),
        'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        'death_date': _format_date(client_data.get('date_of_death', '')),
        'project_name': project_data.get('project_name', 'Appraisal Project'),
        'estate_of': client_data.get('name', ''),
            'law_firm': account_data.get('name', ''),  # law_firm uses name from account table
        **inspection_placeholders
    }
    
    logger.info(f"Special field values for final check: {special_fields}")
    
    # Check all paragraphs in the document
    for paragraph in doc.paragraphs:
        if '{' in paragraph.text and '}' in paragraph.text:
            logger.warning(f"Found potential remaining placeholder in paragraph: '{paragraph.text}'")
            
            # Extract all placeholders
            matches = re.findall(pattern, paragraph.text)
            if matches:
                logger.info(f"Found {len(matches)} remaining placeholders: {matches}")
                
                # Get the full paragraph text
                full_text = paragraph.text
                
                # Replace each placeholder
                for field_name in matches:
                    placeholder = '{' + field_name + '}'
                    
                    # Check special fields first
                    if field_name in special_fields:
                        value = special_fields[field_name]
                        logger.info(f"Using special field value for {field_name}: {value}")
                    else:
                        # Get replacement value
                        value = _get_field_value_from_project(field_name, project_data)
                        if value is None and field_name in field_mappings:
                            value = _get_field_value(field_name, field_mappings[field_name], project_data)
                    
                    if value is None:
                        value = ''
                    
                    # Replace in the full text
                    full_text = full_text.replace(placeholder, str(value))
                    logger.info(f"   → Replaced {placeholder} with: {str(value)[:50]}")
                
                logger.info(f"Full text after replacements: {full_text[:200]}")
                logger.info(f"Paragraph has {len(paragraph.runs)} runs")
                
                # Special handling for the entire paragraph
                # This is a more aggressive approach that replaces the entire paragraph text
                # It may lose some formatting but ensures placeholders are replaced
                if paragraph.runs:
                    logger.info(f"Setting first run text to replaced full_text")
                    # Put all text in the first run
                    paragraph.runs[0].text = full_text
                    logger.info(f"First run text set successfully")
                    
                    # Clear all other runs
                    for i in range(1, len(paragraph.runs)):
                        paragraph.runs[i].text = ''
                    logger.info(f"Cleared {len(paragraph.runs) - 1} additional runs")
                else:
                    logger.warning(f"Paragraph has no runs! Cannot apply replacement.")
    
    # Check all tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if '{' in paragraph.text and '}' in paragraph.text:
                        logger.warning(f"Found potential remaining placeholder in table cell: '{paragraph.text}'")
                        
                        # Extract all placeholders
                        matches = re.findall(pattern, paragraph.text)
                        if matches:
                            logger.info(f"Found {len(matches)} remaining placeholders in table: {matches}")
                            
                            # Get the full paragraph text
                            full_text = paragraph.text
                            
                            # Replace each placeholder
                            for field_name in matches:
                                placeholder = '{' + field_name + '}'
                                
                                # Check special fields first
                                if field_name in special_fields:
                                    value = special_fields[field_name]
                                    logger.info(f"Using special field value for {field_name} in table: {value}")
                                else:
                                    # Get replacement value
                                    value = _get_field_value_from_project(field_name, project_data)
                                    if value is None and field_name in field_mappings:
                                        value = _get_field_value(field_name, field_mappings[field_name], project_data)
                                
                                if value is None:
                                    value = ''
                                
                                # Replace in the full text
                                full_text = full_text.replace(placeholder, str(value))
                                logger.info(f"   → Replaced {placeholder} in table with: {str(value)[:50]}")
                            
                            logger.info(f"Table cell full text after replacements: {full_text[:200]}")
                            logger.info(f"Table cell paragraph has {len(paragraph.runs)} runs")
                            
                            # Special handling for the entire paragraph
                            if paragraph.runs:
                                logger.info(f"Setting table cell first run text to replaced full_text")
                                paragraph.runs[0].text = full_text
                                logger.info(f"Table cell first run text set successfully")
                                for i in range(1, len(paragraph.runs)):
                                    paragraph.runs[i].text = ''
                                logger.info(f"Cleared {len(paragraph.runs) - 1} additional runs in table cell")
                            else:
                                logger.warning(f"Table cell paragraph has no runs! Cannot apply replacement.")
    
    # Check headers and footers
    for section in doc.sections:
        # Process header
        if section.header:
            for paragraph in section.header.paragraphs:
                if '{' in paragraph.text and '}' in paragraph.text:
                    logger.warning(f"Found potential remaining placeholder in header: '{paragraph.text}'")
                    
                    # Extract all placeholders
                    matches = re.findall(pattern, paragraph.text)
                    if matches:
                        logger.info(f"Found {len(matches)} remaining placeholders in header: {matches}")
                        
                        # Get the full paragraph text
                        full_text = paragraph.text
                        
                        # Replace each placeholder
                        for field_name in matches:
                            placeholder = '{' + field_name + '}'
                            
                            # Check special fields first
                            if field_name in special_fields:
                                value = special_fields[field_name]
                                logger.info(f"Using special field value for {field_name} in header: {value}")
                            else:
                                # Get replacement value
                                value = _get_field_value_from_project(field_name, project_data)
                                if value is None and field_name in field_mappings:
                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                            
                            if value is None:
                                value = ''
                            
                            # Replace in the full text
                            full_text = full_text.replace(placeholder, str(value))
                        
                        # Special handling for the entire paragraph
                        if paragraph.runs:
                            paragraph.runs[0].text = full_text
                            for i in range(1, len(paragraph.runs)):
                                paragraph.runs[i].text = ''
        
        # Process footer
        if section.footer:
            for paragraph in section.footer.paragraphs:
                if '{' in paragraph.text and '}' in paragraph.text:
                    logger.warning(f"Found potential remaining placeholder in footer: '{paragraph.text}'")
                    
                    # Extract all placeholders
                    matches = re.findall(pattern, paragraph.text)
                    if matches:
                        logger.info(f"Found {len(matches)} remaining placeholders in footer: {matches}")
                        
                        # Get the full paragraph text
                        full_text = paragraph.text
                        
                        # Replace each placeholder
                        for field_name in matches:
                            placeholder = '{' + field_name + '}'
                            
                            # Check special fields first
                            if field_name in special_fields:
                                value = special_fields[field_name]
                                logger.info(f"Using special field value for {field_name} in footer: {value}")
                            else:
                                # Get replacement value
                                value = _get_field_value_from_project(field_name, project_data)
                                if value is None and field_name in field_mappings:
                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                            
                            if value is None:
                                value = ''
                            
                            # Replace in the full text
                            full_text = full_text.replace(placeholder, str(value))
                        
                        # Special handling for the entire paragraph
                        if paragraph.runs:
                            paragraph.runs[0].text = full_text
                            for i in range(1, len(paragraph.runs)):
                                paragraph.runs[i].text = ''

def _replace_fields_in_paragraph(paragraph, field_mappings: Dict, project_data: Dict):
    """Replace field placeholders with actual data - only {field_name} format, preserving formatting"""
    # Check if this is field mappings data (for template generation)
    field_mapping_data = project_data.get('field_mappings', {})
    
    # First, check if we need to handle placeholders that span multiple runs
    # Get the full paragraph text to check for complete placeholders
    full_text = paragraph.text
    import re
    pattern = r'\{([^{}]+)\}'
    
    # Find all complete placeholders in the paragraph
    complete_placeholders = re.findall(pattern, full_text)
    logger.info(f"Complete placeholders in paragraph: {complete_placeholders}")
    
    # If there are no complete placeholders but there are '{' or '}' characters,
    # we might have placeholders split across runs
    has_open_brace = '{' in full_text
    has_close_brace = '}' in full_text
    
    if has_open_brace and has_close_brace and not complete_placeholders:
        logger.info(f"Potential split placeholders detected in: '{full_text}'")
        # Try to reconstruct the paragraph text from runs
        reconstructed_text = ''
        for run in paragraph.runs:
            reconstructed_text += run.text
        
        # Find placeholders in the reconstructed text
        split_placeholders = re.findall(pattern, reconstructed_text)
        logger.info(f"Split placeholders found: {split_placeholders}")
        
        if split_placeholders:
            # We have placeholders split across runs, handle them specially
            return _replace_split_placeholders(paragraph, field_mappings, project_data, split_placeholders)
    
    # Define field replacement function
    def replace_field(match):
        field_name = match.group(1).strip()
        
        # Get value from project data mapping
        value = _get_field_value_from_project(field_name, project_data)
        
        # Log the field name and value for debugging
        logger.info(f"Field: {field_name}, Value from project data: {value}")
        
        # Fallback to field mappings if no direct mapping found
        if value is None and field_name in field_mappings:
            if field_mapping_data:
                value = field_mapping_data.get(field_name, field_mappings[field_name].get('default_value', ''))
                logger.info(f"Field: {field_name}, Value from field_mapping_data: {value}")
            else:
                value = _get_field_value(field_name, field_mappings[field_name], project_data)
                logger.info(f"Field: {field_name}, Value from _get_field_value: {value}")
        
        # Final fallback - empty string instead of keeping placeholder
        if value is None or value == f'[{field_name}]':
            logger.warning(f"No value found for field: {field_name}, using empty string")
            value = ''
        
        return str(value) if value is not None else ''
    
    # Process each run to preserve formatting
    for run in paragraph.runs:
        if run.text:
            # Replace all {field_name} patterns in this run
            new_text = re.sub(pattern, replace_field, run.text)
            if new_text != run.text:
                logger.info(f"Replaced text in run: '{run.text}' -> '{new_text}'")
                run.text = new_text

def _replace_split_placeholders(paragraph, field_mappings: Dict, project_data: Dict, placeholders: List[str]):
    """Handle placeholders that are split across multiple runs"""
    logger.info("Handling split placeholders across runs")
    
    # Get the full paragraph text
    full_text = ''
    for run in paragraph.runs:
        full_text += run.text
    
    # For each placeholder, find its value and the positions in the full text
    replacements = []
    for field_name in placeholders:
        # Find the placeholder in the full text
        placeholder = '{' + field_name + '}'
        start_pos = full_text.find(placeholder)
        if start_pos >= 0:
            end_pos = start_pos + len(placeholder)
            
            # Get the replacement value
            value = _get_field_value_from_project(field_name, project_data)
            if value is None and field_name in field_mappings:
                value = _get_field_value(field_name, field_mappings[field_name], project_data)
            
            if value is None:
                value = ''
            
            replacements.append((start_pos, end_pos, str(value)))
    
    # Sort replacements by position (descending) to avoid position shifts
    replacements.sort(key=lambda x: x[0], reverse=True)
    
    # Apply replacements to the full text
    for start_pos, end_pos, value in replacements:
        full_text = full_text[:start_pos] + value + full_text[end_pos:]
    
    # Now distribute the modified text back to the runs
    current_pos = 0
    for run in paragraph.runs:
        run_length = len(run.text)
        if run_length > 0:
            # Replace this run's text with the corresponding portion of the modified full text
            run.text = full_text[current_pos:current_pos + run_length]
            current_pos += run_length
    
    logger.info(f"Split placeholder replacement complete")
    return True

def _handle_textboxes_first_page(doc: Document, field_mappings: Dict, project_data: Dict):
    """Handle placeholders in text boxes on the first page only"""
    logger.info("🔠🔠🔠 Processing text boxes on first page only 🔠🔠🔠")
    
    try:
        # Get special fields for replacement
        client_data = project_data.get('client', {})
        account_data = project_data.get('account', {})
        did_inspect = project_data.get('did_inspect')
        inspection_placeholders = _get_inspection_placeholders(did_inspect)

        # DEBUG: Log the raw data we're working with
        logger.info("=" * 80)
        logger.info("📊 TEXT BOX DATA DEBUG:")
        logger.info(f"client_data keys: {list(client_data.keys())}")
        logger.info(f"account_data keys: {list(account_data.keys())}")
        logger.info(f"account_data content: {account_data}")
        logger.info(f"law_firm value will be: '{account_data.get('name', '')}'")
        logger.info("=" * 80)
        
        special_fields = {
            'case_name': client_data.get('case_name', 'Estate Appraisal'),
            'inspection_date': _format_date(project_data.get('inspection_date', '')),
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
            'effective_date': _format_date(project_data.get('effective_date', '')),
            'appraisal_location': project_data.get('appraisal_location', ''),
            'appraisal_type': project_data.get('appraisal_type', ''),
            'client_name': client_data.get('name', 'Client'),
            'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
            'attorney_name': client_data.get('attorney_name', ''),
            'attorney_phone': client_data.get('attorney_phone', ''),
            'attorney_email': client_data.get('attorney_email', ''),
            'death_date': _format_date(client_data.get('date_of_death', '')),
            'project_name': project_data.get('project_name', 'Appraisal Project'),
            'estate_of': client_data.get('name', ''),
            'law_firm': account_data.get('name', ''),  # law_firm uses name from account table
            **inspection_placeholders
        }
        
        logger.info(f"✅ Special fields prepared: {list(special_fields.keys())}")
        logger.info(f"   law_firm = '{special_fields.get('law_firm', 'NOT SET')}'")
        
        # Access the document's XML directly to find text boxes
        import re
        pattern = r'\{([^{}]+)\}'
        
        # Get the main document part
        document_part = doc.part
        
        # Find all shape elements (which include text boxes)
        shape_elements = []
        
        # Define namespaces for XPath queries
        namespaces = {
            'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
            'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
            'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
            'wps': 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape',
            'mc': 'http://schemas.openxmlformats.org/markup-compatibility/2006',
            'v': 'urn:schemas-microsoft-com:vml',
            'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture'
        }
        
        # Look for shape elements in the document XML - multiple possible structures
        xpath_patterns = [
            './/w:drawing//wp:inline//a:graphic//a:graphicData//wps:txbx//w:p',  # Standard inline text boxes
            './/w:drawing//wp:anchor//a:graphic//a:graphicData//wps:txbx//w:p',   # Anchored text boxes
            './/mc:AlternateContent//w:drawing//wp:anchor//a:graphic//a:graphicData//wps:txbx//w:p',  # Alternate content
            './/w:pict//v:shape//v:textbox//w:p',  # VML text boxes (older format)
            './/w:drawing//wp:inline//a:graphic//a:graphicData//v:shape//v:textbox//w:p',  # Mixed format
            './/w:drawing//wp:anchor//a:graphic//a:graphicData//v:shape//v:textbox//w:p',  # Mixed format anchored
        ]
        
        # Try each XPath pattern with proper namespaces
        for xpath_pattern in xpath_patterns:
            try:
                elements = document_part.element.xpath(xpath_pattern, namespaces=namespaces)
                logger.info(f"Found {len(elements)} text box paragraphs using pattern: {xpath_pattern}")
                shape_elements.extend(elements)
            except Exception as e:
                logger.warning(f"Error with XPath pattern {xpath_pattern}: {str(e)}")
                continue
            
        logger.info(f"Found {len(shape_elements)} text box paragraphs in the document")
        
        # Check if we can access sections to limit to first page
        first_page_only = True
        try:
            # Try to identify elements that are on the first page only
            # This is an approximation since it's hard to determine exact page location
            # We'll use the first section as a proxy for the first page
            if len(doc.sections) > 0:
                logger.info(f"Limiting text box processing to first page (first section)")
            else:
                logger.info(f"Cannot determine sections, processing all text boxes")
                first_page_only = False
        except Exception as e:
            logger.warning(f"Error determining sections: {str(e)}")
            first_page_only = False
        
        # Also try to find text frames (another type of text container)
        try:
            # Look for text frames in the document
            frame_elements = document_part.element.xpath('.//w:txbxContent//w:p', namespaces=namespaces)
            logger.info(f"Found {len(frame_elements)} text frame paragraphs")
            shape_elements.extend(frame_elements)
        except Exception as e:
            logger.warning(f"Error finding text frames: {str(e)}")
            
        # Try a direct XML approach for text boxes - LIMITED TO FIRST PAGE ONLY
        try:
            # Find text elements in the first page only
            # Strategy: Find elements up to the first page break
            body = document_part.element.find('.//w:body', namespaces=namespaces)
            if body is None:
                logger.warning("Could not find document body")
                return False
            
            # Collect text elements until we hit a page break
            text_elements = []
            first_page_break_found = False
            
            for child in body:
                # Check if this element or its descendants contain a page break
                page_breaks = child.findall('.//w:br[@w:type="page"]', namespaces=namespaces)
                if page_breaks:
                    logger.info(f"Found first page break, stopping text element collection")
                    first_page_break_found = True
                    break
                
                # Collect all text elements from this paragraph/element
                child_text_elements = child.findall('.//w:t', namespaces=namespaces)
                text_elements.extend(child_text_elements)
            
            logger.info(f"Found {len(text_elements)} text elements on FIRST PAGE ONLY to check for placeholders")
            
            # DEBUG: Sample the first 10 text elements to see what we're working with
            logger.info("📝 SAMPLE OF TEXT ELEMENTS (first 10):")
            for idx, elem in enumerate(text_elements[:10]):
                text_sample = (elem.text or "")[:100]
                logger.info(f"   [{idx}] {text_sample}")
            
            # First check for malformed placeholders like {}case_name and fix them
            for text_element in text_elements:
                text_content = text_element.text
                if text_content and '{}' in text_content:
                    # Fix malformed placeholders
                    malformed_pattern = r'\{\}([a-zA-Z0-9_]+)'
                    malformed_matches = re.findall(malformed_pattern, text_content)
                    if malformed_matches:
                        logger.warning(f"Found malformed placeholders: {malformed_matches}")
                        fixed_text = text_content
                        for field_name in malformed_matches:
                            malformed = '{}' + field_name
                            correct = '{' + field_name + '}'
                            logger.info(f"Fixing malformed placeholder: {malformed} -> {correct}")
                            fixed_text = fixed_text.replace(malformed, correct)
                        text_element.text = fixed_text
            
            # Check each text element for placeholders
            for text_element in text_elements:
                text_content = text_element.text
                if text_content and '{' in text_content and '}' in text_content:
                    # Find all placeholders in this text element
                    matches = re.findall(pattern, text_content)
                    if matches:
                        logger.info(f"Found placeholders in text element: {matches}")
                        
                        # Replace each placeholder
                        modified_text = text_content
                        for field_name in matches:
                            placeholder = '{' + field_name + '}'
                            
                            # First check special fields
                            if field_name in special_fields:
                                value = special_fields[field_name]
                                logger.info(f"Using special field value for {field_name} in text element: {value}")
                            else:
                                # Get replacement value
                                value = _get_field_value_from_project(field_name, project_data)
                                if value is None and field_name in field_mappings:
                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                            
                            if value is None:
                                value = ''
                            
                            # Replace directly in the text content
                            old_modified = modified_text
                            modified_text = modified_text.replace(placeholder, str(value))
                            logger.info(f"   ✏️  Replaced in text: '{old_modified}' -> '{modified_text}'")
                        
                        # Update the text element directly
                        logger.info(f"   💾 Setting text element to: '{modified_text}'")
                        text_element.text = modified_text
                        logger.info(f"   ✅ Text element updated successfully")
            
            # Summary
            logger.info("=" * 80)
            logger.info("📊 TEXT BOX REPLACEMENT SUMMARY:")
            logger.info(f"   Total text elements checked: {len(text_elements)}")
            placeholders_found = sum(1 for elem in text_elements if elem.text and '{' in elem.text and '}' in elem.text)
            logger.info(f"   Text elements with placeholders: {placeholders_found}")
            logger.info("=" * 80)
        except Exception as e:
            logger.error(f"❌ Error with direct XML approach: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Process each shape element
        for i, shape_element in enumerate(shape_elements):
            try:
                # Convert the shape element to a paragraph object
                from docx.text.paragraph import Paragraph
                paragraph = Paragraph(shape_element, document_part)
                
                # Check if the paragraph contains placeholders
                full_text = paragraph.text
                if '{' in full_text and '}' in full_text:
                    logger.info(f"Found placeholders in text box {i+1}: '{full_text}'")
                    
                    # Find all placeholders in the text
                    matches = re.findall(pattern, full_text)
                    if matches:
                        logger.info(f"Placeholders in text box {i+1}: {matches}")
                        
                        # For text boxes, use a direct approach instead of _replace_fields_in_paragraph
                        # This prevents issues with malformed placeholders
                        logger.info(f"Using direct replacement for text box placeholders")
                        
                        # Get the full text and replace all placeholders directly
                        modified_text = full_text
                        
                        for field_name in matches:
                            placeholder = '{' + field_name + '}'
                            
                            # First check special fields
                            if field_name in special_fields:
                                value = special_fields[field_name]
                                logger.info(f"Using special field value for {field_name} in text box: {value}")
                            else:
                                # Get replacement value
                                value = _get_field_value_from_project(field_name, project_data)
                                if value is None and field_name in field_mappings:
                                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                            
                            if value is None:
                                value = ''
                                
                            # Replace the placeholder with its value
                            logger.info(f"Replacing '{placeholder}' with '{value}' in text box")
                            modified_text = modified_text.replace(placeholder, str(value))
                        
                        # Apply the modified text directly to the paragraph
                        if len(paragraph.runs) > 0:
                            # If there are multiple runs, put all text in the first run
                            paragraph.runs[0].text = modified_text
                            for i in range(1, len(paragraph.runs)):
                                paragraph.runs[i].text = ''
                        else:
                            # If there are no runs, we need to create one
                            paragraph.add_run(modified_text)
            except Exception as e:
                logger.warning(f"Error processing text box {i+1}: {str(e)}")
                continue
        
        logger.info("🔠🔠🔠 Text box processing completed 🔠🔠🔠")
        return True
    except Exception as e:
        logger.error(f"Error processing text boxes: {str(e)}")
        return False

def _replace_split_placeholders_preserve_formatting(paragraph, field_mappings: Dict, project_data: Dict, special_fields: Dict, matches: List[str]):
    """Handle placeholders that are split across multiple runs while preserving formatting"""
    logger.info("Handling split placeholders with formatting preservation")
    
    # First, identify which runs contain parts of the placeholder
    placeholder_runs = []
    for i, run in enumerate(paragraph.runs):
        if '{' in run.text or '}' in run.text:
            placeholder_runs.append(i)
    
    if not placeholder_runs:
        logger.info("No placeholder runs found")
        return False
    
    # Get the full placeholder text from the affected runs
    placeholder_text = ''
    for i in placeholder_runs:
        placeholder_text += paragraph.runs[i].text
    
    logger.info(f"Combined placeholder text: '{placeholder_text}'")
    
    # Replace placeholders in the combined text
    modified_text = placeholder_text
    for field_name in matches:
        placeholder = '{' + field_name + '}'
        if placeholder in modified_text:
            # Get replacement value
            if field_name in special_fields:
                value = special_fields[field_name]
                logger.info(f"Using special field value for {field_name}: {value}")
            else:
                # Get replacement value
                value = _get_field_value_from_project(field_name, project_data)
                if value is None and field_name in field_mappings:
                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
            
            if value is None:
                value = ''
                
            modified_text = modified_text.replace(placeholder, str(value))
    
    logger.info(f"Modified text: '{modified_text}'")
    
    # If the placeholder spans multiple runs, we need to be careful about how we distribute the text
    if len(placeholder_runs) > 1:
        # Find the first and last run containing the placeholder
        first_run_idx = placeholder_runs[0]
        last_run_idx = placeholder_runs[-1]
        
        # Get the text before the placeholder in the first run
        first_run = paragraph.runs[first_run_idx]
        first_run_text = first_run.text
        prefix = ''
        for i in range(len(first_run_text)):
            if first_run_text[i] == '{':
                prefix = first_run_text[:i]
                break
        
        # Get the text after the placeholder in the last run
        last_run = paragraph.runs[last_run_idx]
        last_run_text = last_run.text
        suffix = ''
        for i in range(len(last_run_text)-1, -1, -1):
            if last_run_text[i] == '}':
                suffix = last_run_text[i+1:]
                break
        
        # Put the modified text in the first run, preserving text before the placeholder
        first_run.text = prefix + modified_text
        
        # Clear intermediate runs
        for i in placeholder_runs[1:-1]:
            paragraph.runs[i].text = ''
        
        # Update the last run to only include text after the placeholder if it's not the same as the first run
        if first_run_idx != last_run_idx:
            last_run.text = suffix
    else:
        # If the placeholder is contained within a single run, just replace it
        run_idx = placeholder_runs[0]
        run = paragraph.runs[run_idx]
        run_text = run.text
        
        # Replace the placeholder portion while preserving text before and after
        start_idx = run_text.find('{')
        end_idx = run_text.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            prefix = run_text[:start_idx]
            suffix = run_text[end_idx:]
            run.text = prefix + modified_text + suffix
    
    logger.info(f"Split placeholder replacement with formatting preservation complete")
    return True

# Shape processing functions removed - not needed

def _handle_appraisal_items(doc: Document, project_data: Dict):
    """Handle appraisal items and images insertion with all project photos"""
    try:
        appraisal_items = project_data.get('appraisal_items', [])
        all_project_photos = project_data.get('all_project_photos', [])
        
        logger.info(f"Processing {len(appraisal_items)} appraisal items, {len(all_project_photos)} photos")
        
        if not appraisal_items and not all_project_photos:
            logger.info("No items or photos found, returning early")
            return
        
        # Find and process the template item section
        template_item_paragraph = None
        
        # Look for "Item 1" paragraph
        for i, paragraph in enumerate(doc.paragraphs):
            if 'item 1' in paragraph.text.lower():
                template_item_paragraph = paragraph
                logger.info(f"*** FOUND ITEM 1 at paragraph {i}: '{paragraph.text.strip()}' ***")
                break
        
        if template_item_paragraph:
            logger.info("Item 1 found, proceeding with clearing...")
            
            # Save the position BEFORE clearing (since Item 1 will be deleted)
            parent = template_item_paragraph._element.getparent()
            item1_index = list(parent).index(template_item_paragraph._element)
            logger.info(f"Saved Item 1 position: {item1_index}")
            
            # Clear all content between Item 1 and last Fair Market Value FIRST
            logger.info("*** CALLING CLEARING FUNCTION ***")
            try:
                _clear_content_between_item1_and_last_fmv(doc, template_item_paragraph)
                logger.info("*** CLEARING COMPLETED ***")
            except Exception as clear_error:
                logger.error(f"*** CLEARING FAILED: {str(clear_error)} ***")
            
            # Use the saved position for insertions (Item 1 no longer exists)
            # Start inserting items directly at the saved position (no page break before)
            current_index = item1_index
            
            # Process all project photos as items
            
            # Use appraisal items if available (they have descriptions), otherwise use all project photos
            items_to_process = appraisal_items if appraisal_items else all_project_photos
            
            logger.info(f"Processing {len(items_to_process)} items for template generation")
            logger.info(f"Using {'appraisal_items' if appraisal_items else 'all_project_photos'} as data source")
            
            for i, item in enumerate(items_to_process, 1):
                
                # Insert item paragraph for ALL items (including Item 1)
                current_index += 1
                new_item_p = doc.add_paragraph()._element
                parent.remove(new_item_p)
                parent.insert(current_index, new_item_p)
                
                # Find the paragraph and format it with bold, larger font
                for p in doc.paragraphs:
                    if p._element == new_item_p:
                        run = p.add_run(f"Item {i}")
                        run.bold = True
                        run.font.size = Pt(14)  # Larger font size
                        break
                
                # Get description and appraised value
                description = item.get('description', '')
                appraised_value = 0
                if 'appraised_value' in item:
                    appraised_value = item.get('appraised_value', 0)
                elif appraisal_items and i <= len(appraisal_items):
                    appraised_value = appraisal_items[i-1].get('appraised_value', 0)
                
                # Insert image and description side-by-side using text wrapping
                photo_path = item.get('file_path') if 'file_path' in item else item.get('photo_path')
                
                if photo_path and os.path.exists(photo_path) and description and description.strip():
                    # Create table layout with image on left, description on right
                    try:
                        if _is_valid_image(photo_path):
                            current_index += 1
                            
                            # Create a placeholder paragraph and then replace it with a table
                            placeholder_p = doc.add_paragraph()._element
                            parent.remove(placeholder_p)
                            parent.insert(current_index, placeholder_p)
                            
                            # Find the placeholder and replace with table
                            for p_idx, p in enumerate(doc.paragraphs):
                                if p._element == placeholder_p:
                                    # Get the parent element
                                    p_parent = p._element.getparent()
                                    p_index = list(p_parent).index(p._element)
                                    
                                    # Remove the placeholder
                                    p_parent.remove(p._element)
                                    
                                    # Create table at the exact position
                                    table = doc.add_table(rows=1, cols=2)
                                    
                                    # Move the table to the correct position
                                    table_element = table._element
                                    doc._body._element.remove(table_element)
                                    p_parent.insert(p_index, table_element)
                                    break
                            
                            # Set column widths: 2.5" for image, rest for description
                            table.columns[0].width = Inches(2.5)
                            table.columns[1].width = Inches(4.0)
                            
                            # Configure table style - no borders
                            table.style = 'Table Grid'
                            for row in table.rows:
                                for cell in row.cells:
                                    # Remove all borders
                                    tc = cell._element.get_or_add_tcPr()
                                    tcBorders = tc.find(qn('w:tcBorders'))
                                    if tcBorders is not None:
                                        tc.remove(tcBorders)
                                    
                                    # Add invisible borders
                                    tcBorders = OxmlElement('w:tcBorders')
                                    for border_name in ['top', 'left', 'bottom', 'right']:
                                        border = OxmlElement(f'w:{border_name}')
                                        border.set(qn('w:val'), 'nil')
                                        tcBorders.append(border)
                                    tc.append(tcBorders)
                            
                            # Add image to first cell (left-aligned)
                            img_cell = table.cell(0, 0)
                            img_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            img_paragraph = img_cell.paragraphs[0]
                            img_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            
                            img_run = img_paragraph.add_run()
                            img_run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                            
                            # Add description to second cell
                            desc_cell = table.cell(0, 1)
                            desc_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            desc_paragraph = desc_cell.paragraphs[0]
                            desc_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            
                            desc_run = desc_paragraph.add_run(description.strip())
                            
                            logger.info(f"Added table layout for Item {i}: {description[:50]}...")
                                    
                    except Exception as img_error:
                        logger.error(f"Failed to create table layout {photo_path}: {str(img_error)}")
                        # Fallback to simple paragraph layout
                        current_index += 1
                        fallback_p = doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}] {description.strip()}")._element
                        parent.remove(fallback_p)
                        parent.insert(current_index, fallback_p)
                
                elif photo_path and os.path.exists(photo_path):
                    # Image only, no description
                    try:
                        if _is_valid_image(photo_path):
                            current_index += 1
                            img_p = doc.add_paragraph()._element
                            parent.remove(img_p)
                            parent.insert(current_index, img_p)
                            
                            # Find and configure image paragraph (left-aligned)
                            for p in doc.paragraphs:
                                if p._element == img_p:
                                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                    run = p.add_run()
                                    run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                                    break
                    except Exception as img_error:
                        logger.error(f"Failed to insert image {photo_path}: {str(img_error)}")
                        current_index += 1
                        placeholder_p = doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}]")._element
                        parent.remove(placeholder_p)
                        parent.insert(current_index, placeholder_p)
                
                elif description and description.strip():
                    # Description only, no image
                    current_index += 1
                    desc_p = doc.add_paragraph(description.strip())._element
                    parent.remove(desc_p)
                    parent.insert(current_index, desc_p)
                    logger.info(f"Added description for Item {i}: {description[:50]}...")
                
                # Add blank line before fair market value
                current_index += 1
                blank_p = doc.add_paragraph()._element
                parent.remove(blank_p)
                parent.insert(current_index, blank_p)
                
                # Insert fair market value with dotted leader up to margin
                current_index += 1
                p = doc.add_paragraph()
                parent.remove(p._element)
                parent.insert(current_index, p._element)

                # Create tab stops: one left, one right-aligned with dotted leader
                tab_stops = p.paragraph_format.tab_stops
                tab_stops.add_tab_stop(Inches(6.5), WD_ALIGN_PARAGRAPH.RIGHT, leader=1)  # 6.5" typical page width

                # Add text + tab + value
                run = p.add_run("Fair Market Value")
                run = p.add_run("\t")
                run = p.add_run(f"${appraised_value:.2f}")

                
                # Priority: 2 items per page, then page break
                # Also add page break after leftover single items to isolate them
                should_add_page_break = False
                
                if i % 2 == 0:
                    # After every 2nd item, always add page break (including the last item)
                    should_add_page_break = True
                    logger.info(f"Page break after Item {i} (2 items per page)")
                elif i % 2 == 1 and i == len(items_to_process):
                    # After the last item if it's a leftover single item
                    should_add_page_break = True
                    logger.info(f"Page break after Item {i} (leftover single item)")
                
                if should_add_page_break:
                    current_index += 1
                    page_break_p = doc.add_paragraph()._element
                    parent.remove(page_break_p)
                    parent.insert(current_index, page_break_p)
                    
                    # Find and configure page break paragraph
                    for p in doc.paragraphs:
                        if p._element == page_break_p:
                            run = p.add_run()
                            run.add_break(WD_BREAK.PAGE)
                            break
            
            # After processing all items, find and remove content between last item and summary
            _cleanup_content_between_images_and_summary(doc, current_index)
            
            # Add summary table for image-based templates
            _add_summary_table(doc, appraisal_items, 'image_based', project_data)
            
            # Add page break after summary (at the end of document)
            try:
                # Add page break at the end
                last_paragraph = doc.add_paragraph()
                run = last_paragraph.add_run()
                run.add_break(WD_BREAK.PAGE)
            except Exception as e:
                logger.warning(f"Could not add page break after summary: {str(e)}")
                
        else:
            # Try to add items at the end of the document as fallback
            for i, item in enumerate(items_to_process, 1):
                # Add item paragraph
                doc.add_paragraph(f"Item {i}")
                
                # Get description and appraised value
                description = item.get('description', '')
                appraised_value = 0
                if 'appraised_value' in item:
                    appraised_value = item.get('appraised_value', 0)
                elif appraisal_items and i <= len(appraisal_items):
                    appraised_value = appraisal_items[i-1].get('appraised_value', 0)
                
                # Add image and description side-by-side
                photo_path = item.get('file_path') if 'file_path' in item else item.get('photo_path')
                
                if photo_path and os.path.exists(photo_path) and description and description.strip():
                    # Create table layout with image on left, description on right
                    try:
                        if _is_valid_image(photo_path):
                            # Create a 1x2 table (1 row, 2 columns)
                            table = doc.add_table(rows=1, cols=2)
                            
                            # Set column widths: 2.5" for image, rest for description
                            table.columns[0].width = Inches(2.5)
                            table.columns[1].width = Inches(4.0)
                            
                            # Configure table style - no borders
                            table.style = 'Table Grid'
                            for row in table.rows:
                                for cell in row.cells:
                                    # Remove all borders
                                    tc = cell._element.get_or_add_tcPr()
                                    tcBorders = tc.find(qn('w:tcBorders'))
                                    if tcBorders is not None:
                                        tc.remove(tcBorders)
                                    
                                    # Add invisible borders
                                    tcBorders = OxmlElement('w:tcBorders')
                                    for border_name in ['top', 'left', 'bottom', 'right']:
                                        border = OxmlElement(f'w:{border_name}')
                                        border.set(qn('w:val'), 'nil')
                                        tcBorders.append(border)
                                    tc.append(tcBorders)
                            
                            # Add image to first cell (left-aligned)
                            img_cell = table.cell(0, 0)
                            img_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            img_paragraph = img_cell.paragraphs[0]
                            img_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            
                            img_run = img_paragraph.add_run()
                            img_run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                            
                            # Add description to second cell
                            desc_cell = table.cell(0, 1)
                            desc_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                            desc_paragraph = desc_cell.paragraphs[0]
                            desc_paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            
                            desc_run = desc_paragraph.add_run(description.strip())
                            
                            logger.info(f"Added table layout for Item {i} (fallback): {description[:50]}...")
                    except Exception as img_error:
                        logger.error(f"Failed to create table layout {photo_path}: {str(img_error)}")
                        # Fallback to separate paragraphs
                        doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}] {description.strip()}")
                
                elif photo_path and os.path.exists(photo_path):
                    # Image only, no description
                    try:
                        if _is_valid_image(photo_path):
                            img_p = doc.add_paragraph()
                            img_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            run = img_p.add_run()
                            run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                    except Exception as img_error:
                        logger.error(f"Failed to insert image {photo_path}: {str(img_error)}")
                        doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}]")
                
                elif description and description.strip():
                    # Description only, no image
                    doc.add_paragraph(description.strip())
                    logger.info(f"Added description for Item {i} (fallback): {description[:50]}...")
                
                # Add fair market value with dots
                fmv_text = "Fair Market Value"
                price_text = f"${appraised_value:.2f}"
                
                # Calculate dots needed (approximate)
                dots_needed = max(1, 60 - len(fmv_text) - len(price_text))
                dots = "." * dots_needed
                
                price_line = f"{fmv_text}{dots}{price_text}"
                doc.add_paragraph(price_line)

        # else:
        #     logger.warning("*** ITEM 1 NOT FOUND IN TEMPLATE! ***")
        #     logger.warning("Cannot clear existing content without Item 1 anchor point")
        #     logger.warning("Template paragraphs were logged above - check if 'Item 1' exists")
        #     logger.warning("Skipping content clearing and proceeding with fallback item insertion")

        
    except Exception as e:
        import traceback
        error_msg = str(e) if e else "Unknown error"
        traceback_str = traceback.format_exc()
        
        logger.error(f"Error handling appraisal items: {error_msg}")
        logger.error(f"Full traceback: {traceback_str}")





def _get_field_value_from_project(field_name: str, project_data: Dict) -> str:
    """Get field value from project data using comprehensive mapping"""

    
    client_data = project_data.get('client', {})
    account_data = project_data.get('account', {})
    appraisal_items = project_data.get('appraisal_items', [])
    did_inspect = project_data.get('did_inspect')
    inspection_placeholders = _get_inspection_placeholders(did_inspect)
    
    # Log the field name we're looking for
    logger.info(f"Looking for field value: {field_name}")
    
    # Check if the field is directly in project_data first
    if field_name in project_data:
        logger.info(f"Found {field_name} directly in project_data: {project_data[field_name]}")
        return project_data[field_name]
    
    # Check if the field is in client_data
    if field_name in client_data:
        logger.info(f"Found {field_name} in client_data: {client_data[field_name]}")
        return client_data[field_name]
    
    # Check if the field is in account_data
    if field_name in account_data:
        logger.info(f"Found {field_name} in account_data: {account_data[field_name]}")
        return account_data[field_name]
    
    # Build full address
    full_address = f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip()
    
    # Fixed metal prices
    gold_price = 115.65
    
    # Comprehensive field mapping
    field_mappings = {
        # Basic project fields
        'client_name': client_data.get('name', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'inspection_date': _format_date(project_data.get('inspection_date', datetime.now().strftime('%Y-%m-%d'))),
        'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'effective_date': _format_date(project_data.get('effective_date', '')),
        'appraisal_location': project_data.get('appraisal_location', ''),
        'appraisal_type': project_data.get('appraisal_type', ''),
        'address': full_address,
        'death_date': _format_date(client_data.get('date_of_death')),
        'total_value': f"${project_data.get('total_value', '0.00')}",
        'gold_price': f"${gold_price:.2f}",
        'silver_price': '$1.32',
        'plat_price': '$45.10',
        'case_number': project_data.get('case_number', ''),
        'project_name': project_data.get('project_name', ''),
        
        # Client fields
        'client_address': full_address,
        'client_phone': client_data.get('phone', ''),
        'client_email': client_data.get('email', ''),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        'case_name': client_data.get('case_name', 'Appraisal'),
        'estate_of': client_data.get('name', ''),
        
        # Account fields
            'law_firm': account_data.get('name', ''),  # law_firm uses name from account table
        
        # Inspection fields
        **inspection_placeholders,
        
        # Appraisal summary fields
        'item_count': str(len(appraisal_items)),
        'photo_count': str(len(project_data.get('all_project_photos', []))),
        'market_value': f"${appraisal_items[0].get('appraised_value', 0):.2f}" if appraisal_items else '$0.00',
        
        # Static appraiser fields
        'appraiser_name': 'Andrew Kravit',
        'appraiser_credentials': 'Certified Appraiser',
    }
    
    # Add individual item fields for first few items
    for i, item in enumerate(appraisal_items[:10]):  # Support up to 10 items
        item_num = i + 1
        field_mappings.update({
            f'item_{item_num}_description': item.get('description', ''),
            f'item_{item_num}_value': f"${item.get('appraised_value', 0):.2f}",
            f'item_{item_num}_room': item.get('room_area', ''),
            f'item_{item_num}_floor': item.get('floor_building', ''),
            f'item_{item_num}_type': item.get('item_type', ''),
        })
        
        # Add type-specific attributes
        attributes = item.get('attributes', {})
        for attr_name, attr_value in attributes.items():
            field_mappings[f'item_{item_num}_{attr_name}'] = str(attr_value) if attr_value else ''
    
    # Add individual photo fields for first few photos
    all_project_photos = project_data.get('all_project_photos', [])
    for i, photo in enumerate(all_project_photos[:10]):  # Support up to 10 photos
        photo_num = i + 1
        field_mappings.update({
            f'photo_{photo_num}_filename': photo.get('original_filename', ''),
            f'photo_{photo_num}_path': photo.get('file_path', ''),
        })
    
    # Try to find the field with case-insensitive matching
    if field_name.lower() in {k.lower(): k for k in field_mappings.keys()}:
        actual_key = {k.lower(): k for k in field_mappings.keys()}[field_name.lower()]
        logger.info(f"Found case-insensitive match for {field_name}: {actual_key} = {field_mappings[actual_key]}")
        return field_mappings[actual_key]
    
    # Check for similar field names (fuzzy matching)
    for mapped_field in field_mappings.keys():
        if field_name.lower() in mapped_field.lower() or mapped_field.lower() in field_name.lower():
            logger.info(f"Found fuzzy match for {field_name}: {mapped_field} = {field_mappings[mapped_field]}")
            return field_mappings[mapped_field]
    
    # If we get here, no match was found
    logger.warning(f"No match found for field: {field_name}")
    return None

def _format_date(date_value) -> str:
    """Format date value for display in documents"""
    if not date_value:
        return ""
    
    try:
        # Log the date value and its type for debugging
        logger.info(f"Formatting date: {date_value} (type: {type(date_value)})")
        
        # If it's already a string, try to parse it
        if isinstance(date_value, str):
            from datetime import datetime
            # Try different date formats
            formats = [
                '%Y-%m-%d %H:%M:%S%z',  # 2025-09-01 00:00:00+05:00
                '%Y-%m-%d %H:%M:%S',    # 2025-09-01 00:00:00
                '%Y-%m-%d',             # 2025-09-01
                '%m/%d/%Y',             # 09/01/2025
                '%d/%m/%Y',             # 01/09/2025
            ]
            
            # Clean the date string (remove any extra whitespace)
            date_value = date_value.strip()
            
            # Special case: if the date is just a year or empty
            if not date_value or date_value == 'None':
                logger.warning(f"Empty or None date value: '{date_value}'")
                return ""
            
            # Try each format
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_value, fmt)
                    formatted_date = parsed_date.strftime('%B %d, %Y')  # September 01, 2025
                    logger.info(f"Successfully formatted date: {date_value} -> {formatted_date}")
                    return formatted_date
                except ValueError:
                    continue
            
            # If no format worked, return the original string
            logger.warning(f"Could not parse date: {date_value}, returning as is")
            return date_value
        
        # If it's a datetime object
        elif hasattr(date_value, 'strftime'):
            formatted_date = date_value.strftime('%B %d, %Y')
            logger.info(f"Formatted datetime object: {formatted_date}")
            return formatted_date
        
        # For any other type, convert to string
        logger.warning(f"Unknown date type: {type(date_value)}, converting to string")
        return str(date_value) if date_value else ""
        
    except Exception as e:
        logger.warning(f"Error formatting date {date_value}: {str(e)}")
        return str(date_value) if date_value and str(date_value) != 'None' else ""

def _get_field_value(field_name: str, field_config: Dict, project_data: Dict) -> str:
    """Fallback field value getter for unmapped fields"""
    # Try project mapping first
    value = _get_field_value_from_project(field_name, project_data)
    if value is not None:
        return value
    
    # Fallback to field config default
    default_value = field_config.get('default_value', '')
    
    # If default value is empty or None, return empty string instead of placeholder
    if not default_value or default_value == f'[{field_name}]':
        logger.info(f"Using empty string for field {field_name} instead of placeholder")
        return ''
    
    return default_value

def _cleanup_content_between_images_and_summary(doc: Document, last_item_index: int):
    """Remove all content between the last item and the summary section and isolate summary on its own page"""
    try:
        # Check if this is an estate appraisal template by looking for specific text
        is_estate_template = False
        for paragraph in doc.paragraphs:
            if "estate" in paragraph.text.lower() or "estate appraisal" in paragraph.text.lower():
                is_estate_template = True
                logger.info("Detected estate appraisal template")
                break
        
        # First, ensure proper formatting after the last item
        # This prevents any formatting issues with the last item
        last_item_element = None
        for i, paragraph in enumerate(doc.paragraphs):
            if i >= last_item_index:
                last_item_element = paragraph
                break
        
        # Look for summary paragraph
        summary_paragraph = None
        summary_keywords = ['summary', 'total', 'conclusion', 'appraisal summary', 'market value summary']
        
        # Look for summary paragraph after the last item
        for i, paragraph in enumerate(doc.paragraphs):
            paragraph_text = paragraph.text.lower()
            if any(keyword in paragraph_text for keyword in summary_keywords):
                summary_paragraph = paragraph
                break
        
        if summary_paragraph:
            # Find the index of the summary paragraph
            summary_index = -1
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph == summary_paragraph:
                    summary_index = i
                    break
            
            if summary_index > last_item_index:
                # Get the parent element for XML manipulation
                parent = summary_paragraph._element.getparent()
                summary_element = summary_paragraph._element
                summary_element_index = list(parent).index(summary_element)
                
                # Find the last item element's index in the parent
                last_item_element_index = -1
                if last_item_element:
                    last_item_element_index = list(parent).index(last_item_element._element)
                
                if last_item_element_index >= 0:
                    # Remove all elements between last item and summary
                    elements_to_remove = []
                    for i in range(last_item_element_index + 1, summary_element_index):
                        if i < len(parent):
                            elements_to_remove.append(parent[i])
                    
                    for element in elements_to_remove:
                        try:
                            parent.remove(element)
                        except Exception as e:
                            logger.warning(f"Could not remove element: {str(e)}")
                    
                    logger.info(f"Removed {len(elements_to_remove)} elements between items and summary")
                
                # Add page break before summary to isolate it on its own page
                # This ensures the summary starts on a new page
                page_break_before = doc.add_paragraph()._element
                parent.remove(page_break_before)
                parent.insert(summary_element_index, page_break_before)
                
                # Find and configure page break paragraph
                for p in doc.paragraphs:
                    if p._element == page_break_before:
                        run = p.add_run()
                        run.add_break(WD_BREAK.PAGE)
                        break
                
                logger.info("Added page break before summary section")
                
                # For estate appraisal templates, use a different approach to center the summary on the page
                if is_estate_template:
                    try:
                        # Create a table with 3 rows to position the summary in the middle row
                        # This is a more reliable way to center content vertically on a page
                        
                        # First, get the summary content
                        summary_text = summary_paragraph.text
                        
                        # Create a new table with 3 rows and 1 column
                        table = doc.add_table(rows=3, cols=1)
                        table.style = 'Table Grid'
                        table.autofit = True
                        
                        # Remove borders by setting the table style to 'Table Normal' and then removing borders
                        table.style = 'Table Normal'
                        
                        # Set all cell borders to none
                        for row in table.rows:
                            for cell in row.cells:
                                cell.border_top = None
                                cell.border_bottom = None
                                cell.border_left = None
                                cell.border_right = None
                        
                        # Set equal heights for all rows to ensure proper vertical centering
                        # First row (top spacing)
                        top_cell = table.cell(0, 0)
                        top_cell.text = ""
                        top_p = top_cell.add_paragraph()
                        top_p.add_run("\n" * 10)  # Add vertical space
                        
                        # Middle cell (summary content)
                        middle_cell = table.cell(1, 0)
                        middle_cell.text = ""
                        p = middle_cell.add_paragraph(summary_text)
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        
                        # Bottom row (bottom spacing)
                        bottom_cell = table.cell(2, 0)
                        bottom_cell.text = ""
                        bottom_p = bottom_cell.add_paragraph()
                        bottom_p.add_run("\n" * 10)  # Add vertical space
                        
                        # Remove the original summary paragraph
                        summary_paragraph._element.getparent().remove(summary_paragraph._element)
                        
                        # Insert the table at the summary position
                        table_element = table._element
                        parent.remove(table_element)
                        parent.insert(summary_element_index, table_element)
                        
                        logger.info("Added table-based vertical centering for estate template summary")
                    except Exception as e:
                        logger.warning(f"Could not add table-based centering: {str(e)}")
                        # Fallback to simple center alignment
                        try:
                            summary_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            logger.info("Fallback: Center-aligned summary paragraph")
                        except Exception as align_error:
                            logger.warning(f"Could not center-align summary: {str(align_error)}")
                else:
                    # For other templates (like divorce), just center-align the text
                    try:
                        summary_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        logger.info("Center-aligned summary paragraph for non-estate template")
                    except Exception as e:
                        logger.warning(f"Could not center-align summary: {str(e)}")
                
                # Find all paragraphs after the summary that might be part of it
                summary_paragraphs = [summary_index]
                end_of_summary = False
                summary_end_index = summary_element_index
                
                # Look for the end of the summary section
                # We'll check for headings or specific keywords that indicate a new section
                # Only add the summary paragraph to the list if we haven't replaced it with a table
                summary_paragraphs_list = []  # Initialize as empty list
                if not is_estate_template or summary_paragraph._element.getparent() is not None:
                    summary_paragraphs_list.append(summary_paragraph)
                
                for i in range(summary_index + 1, len(doc.paragraphs)):
                    p = doc.paragraphs[i]
                    p_text = p.text.lower()
                    
                    # Check if this is a heading or contains keywords indicating a new section
                    if (p.style and p.style.name and p.style.name.startswith('Heading')) or \
                       any(keyword in p_text for keyword in ['appraiser', 'certification', 'disclaimer', 'appendix']):
                        end_of_summary = True
                        try:
                            summary_end_index = list(parent).index(p._element)
                        except ValueError:
                            # If element isn't a direct child of parent, find its closest parent
                            current = p._element
                            while current.getparent() != parent and current.getparent() is not None:
                                current = current.getparent()
                            if current.getparent() == parent:
                                summary_end_index = list(parent).index(current)
                        break
                    else:
                        # This paragraph is part of the summary
                        summary_paragraphs_list.append(p)
                
                # For estate templates, center-align all paragraphs in the summary section
                if is_estate_template:
                    for p in summary_paragraphs_list:
                        try:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        except Exception as e:
                            logger.warning(f"Could not center-align paragraph: {str(e)}")
                    logger.info(f"Center-aligned {len(summary_paragraphs_list)} paragraphs in summary section")
                
                # If we found the end of summary, add page break after it
                if end_of_summary:
                    # Add page break after summary to start next content on a new page
                    page_break_after = doc.add_paragraph()._element
                    parent.remove(page_break_after)
                    parent.insert(summary_end_index, page_break_after)
                    
                    # Find and configure page break paragraph
                    for p in doc.paragraphs:
                        if p._element == page_break_after:
                            run = p.add_run()
                            run.add_break(WD_BREAK.PAGE)
                            break
                    
                    logger.info("Added page break after summary section")
            
    except Exception as e:
        logger.error(f"Error during content cleanup: {str(e)}")

def _is_valid_image(image_path: str) -> bool:
    """Validate if image file is valid and supported by python-docx"""
    try:
        from PIL import Image
        
        # Check if file exists
        if not os.path.exists(image_path):
            return False
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in valid_extensions:
            logger.warning(f"Unsupported file extension: {file_ext}")
            return False
        
        # Try to open with PIL to validate image
        with Image.open(image_path) as img:
            # Verify it's a valid image
            img.verify()
        
        # Re-open for format check (verify() closes the image)
        with Image.open(image_path) as img:
            # Check if format is supported by python-docx
            supported_formats = ['JPEG', 'PNG', 'GIF', 'BMP', 'TIFF']
            if img.format not in supported_formats:
                logger.warning(f"Unsupported image format: {img.format}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Image validation failed for {image_path}: {str(e)}")
        return False

# ==================== TABLE RENDERING FUNCTIONS ====================

def _parse_description_for_coin_wine(description: str, item_type: str) -> tuple:
    """Parse description template to extract quantity and price for Coin/Wine items"""
    import re
    
    quantity = 0
    price = 0
    
    if not description:
        return (quantity, price)
    
    is_coin = item_type.lower() in ['coin', 'coins']
    is_wine = item_type.lower() in ['wine', 'wines']
    
    try:
        if is_coin:
            # Parse: "Quantity: X" and "Value Per Coin $: Y"
            quantity_match = re.search(r'Quantity:\s*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            price_match = re.search(r'Value Per Coin \$:\s*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            
            if quantity_match:
                quantity = float(quantity_match.group(1))
            if price_match:
                price = float(price_match.group(1))
                
        elif is_wine:
            # Parse: "Quantity: X" and "Per Bottle Price: Y"
            quantity_match = re.search(r'Quantity:\s*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            price_match = re.search(r'Per Bottle Price:\s*(\d+(?:\.\d+)?)', description, re.IGNORECASE)
            
            if quantity_match:
                quantity = float(quantity_match.group(1))
            if price_match:
                price = float(price_match.group(1))
    
    except Exception as e:
        logger.error(f"Error parsing description: {str(e)}")
    
    return (quantity, price)

def _add_images_after_table(doc: Document, items: list, insert_index: int, parent):
    """Add images from items after the table"""
    import os
    logger.info(f"🖼️ Adding images after table for {len(items)} items")
    
    current_insert_index = insert_index
    images_added = 0
    
    for item in items:
        photo_path = item.get('photo_path')
        if photo_path and os.path.exists(photo_path):
            try:
                # Create a new paragraph for the image
                img_paragraph = doc.add_paragraph()
                img_run = img_paragraph.add_run()
                
                # Add the image with a reasonable size
                img_run.add_picture(photo_path, width=Inches(3), height=Inches(3))
                
                # Get the paragraph element and insert it at the correct position
                img_p_element = img_paragraph._element
                doc._body._element.remove(img_p_element)  # Remove from end
                parent.insert(current_insert_index, img_p_element)  # Insert at position
                
                images_added += 1
                current_insert_index += 1
                logger.info(f"✅ Added image: {os.path.basename(photo_path)}")
            except Exception as e:
                logger.error(f"❌ Failed to add image {photo_path}: {str(e)}")
        else:
            logger.debug(f"⏭️ No photo or file not found for item")
    
    logger.info(f"✅ Added {images_added} images after table")
    return images_added

def _handle_coin_table(doc: Document, project_data: Dict):
    """Handle coin collection table rendering - uses JSONB attributes"""
    from docx.shared import Pt
    from docx.enum.text import WD_BREAK
    
    logger.info("🪙 Rendering coin collection table from JSONB attributes")
    
    # Get coin items from appraisal_items with type='coin'
    appraisal_items = project_data.get('appraisal_items', [])
    coin_items = [
        item
        for item in appraisal_items
        if item.get('item_type') in ['Coins', 'coins', 'Coin', 'coin']
    ]
    
    if not coin_items:
        logger.warning("No coin items found for coin table")
        return
    
    # Find the first table in the document and replace it
    if len(doc.tables) > 0:
        logger.info(f"📋 Found {len(doc.tables)} table(s) in document, replacing first one with coin data")
        old_table = doc.tables[0]
        
        # Get the parent element and position
        tbl_element = old_table._element
        parent = tbl_element.getparent()
        tbl_index = list(parent).index(tbl_element)
        logger.info(f"📍 Old table position: index {tbl_index}")
        
        # Create new table (will be added at end of document initially)
        logger.info("🔨 Creating new coin table...")
        new_table = doc.add_table(rows=1, cols=5)
        
        # Try to apply a style, fall back to Table Grid if not available
        try:
            new_table.style = 'Light Grid Accent 1'
        except KeyError:
            try:
                new_table.style = 'Table Grid'
            except KeyError:
                pass  # Use default table style
        
        # Header row
        header_cells = new_table.rows[0].cells
        header_cells[0].text = "Quantity"
        header_cells[1].text = "Year"
        header_cells[2].text = "Coin"
        header_cells[3].text = "Condition"
        header_cells[4].text = "Appraised Price"
        
        # Make headers bold (no color)
        for cell in header_cells:
            # Set cell height for header row
            cell.height = Pt(25)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(14)
        
        # Data rows
        logger.info(f"📝 Adding {len(coin_items)} coin items to table")
        for coin in coin_items:
            row_cells = new_table.add_row().cells
            
            # Parse description to extract quantity and price
            description = coin.get('description', '')
            quantity, price_per_coin = _parse_description_for_coin_wine(description, 'coins')
            
            # Extract other fields from description using regex
            year_match = re.search(r'Year:\s*([^\n]+)', description)
            condition_match = re.search(r'Condition:\s*([^\n]+)', description)
            coin_desc_match = re.search(r'Coin Description:\s*([^\n]+)', description)
            
            row_cells[0].text = str(int(quantity)) if quantity else '0'
            row_cells[1].text = year_match.group(1).strip() if year_match else ''
            row_cells[2].text = coin_desc_match.group(1).strip() if coin_desc_match else description.split('\n')[0][:50]
            row_cells[3].text = condition_match.group(1).strip() if condition_match else ''
            
            # Auto-calculate and format price (quantity * price_per_coin)
            total_value = quantity * price_per_coin
            try:
                row_cells[4].text = f"${total_value:,.2f}"
            except:
                row_cells[4].text = "$0.00"
            
            # Format cells
            for cell in row_cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(14)
        
        logger.info("🔄 Moving new table to replace old table...")
        
        # Move new table to correct position and remove old table (no page break)
        new_tbl_element = new_table._element
        doc._body._element.remove(new_tbl_element)  # Remove from end
        parent.insert(tbl_index, new_tbl_element)  # Insert at same position
        logger.info("✅ Inserted new table at correct position")
        
        parent.remove(tbl_element)  # Remove old template table
        logger.info("✅ Removed old template table")
        
        # Add images after the table
        _add_images_after_table(doc, coin_items, tbl_index + 1, parent)
        
        # Add page break after images (page break will be added after all images)
        # Count how many elements (paragraphs) were added for images
        images_added = len([item for item in coin_items if item.get('photo_path')])
        
        break_after_data = OxmlElement('w:p')
        break_run_after_data = OxmlElement('w:r')
        break_element_after_data = OxmlElement('w:br')
        break_element_after_data.set(qn('w:type'), 'page')
        break_run_after_data.append(break_element_after_data)
        break_after_data.append(break_run_after_data)
        parent.insert(tbl_index + 1 + images_added, break_after_data)
        logger.info("✅ Added page break after coin data table and images")
        
        # Add summary table after data table
        _add_summary_table(doc, coin_items, 'coin', project_data)
        
        logger.info(f"✅ Coin table replaced with {len(coin_items)} items from JSONB attributes")
    else:
        logger.warning("⚠️ No table found in document to replace")

def _handle_content_table(doc: Document, project_data: Dict):
    """Handle content/inventory table rendering - uses JSONB attributes"""
    from docx.shared import Pt
    from docx.enum.text import WD_BREAK
    
    logger.info("📦 Rendering content inventory table from JSONB attributes")
    
    # Get content items from appraisal_items with type='content'
    appraisal_items = project_data.get('appraisal_items', [])
    content_items = [
        item.get('attributes', {})
        for item in appraisal_items
        if item.get('item_type') in ['content', 'contents', 'inventory']
    ]
    
    if not content_items:
        logger.warning("No content items found for content table")
        return
    
    # Find the first table in the document and replace it
    if len(doc.tables) > 0:
        logger.info(f"📋 Found {len(doc.tables)} table(s) in document, replacing first one with content data")
        old_table = doc.tables[0]
        
        # Get the parent element and position
        tbl_element = old_table._element
        parent = tbl_element.getparent()
        tbl_index = list(parent).index(tbl_element)
        logger.info(f"📍 Old table position: index {tbl_index}")
        
        # Create new table (will be added at end of document initially)
        logger.info("🔨 Creating new content table...")
        new_table = doc.add_table(rows=1, cols=2)
        
        # Try to apply a style, fall back to Table Grid if not available
        try:
            new_table.style = 'Light Grid Accent 1'
        except KeyError:
            try:
                new_table.style = 'Table Grid'
            except KeyError:
                pass  # Use default table style
        
        # Header row
        header_cells = new_table.rows[0].cells
        header_cells[0].text = "Area"
        header_cells[1].text = "Fair Market Value (FMV)"
        
        # Make headers bold (no color)
        for cell in header_cells:
            # Set cell height for header row
            cell.height = Pt(25)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(14)
        
        # Data rows
        logger.info(f"📝 Adding {len(content_items)} content items to table")
        for content in content_items:
            row_cells = new_table.add_row().cells
            
            row_cells[0].text = str(content.get('area', ''))
            
            # Format FMV
            fmv = content.get('fair_market_value', 0)
            try:
                row_cells[1].text = f"${float(fmv):,.2f}"
            except:
                row_cells[1].text = "$0.00"
            
            # Format cells
            for cell in row_cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(14)
        
        logger.info("🔄 Moving new table to replace old table...")
        
        # Move new table to correct position and remove old table (no page break)
        new_tbl_element = new_table._element
        doc._body._element.remove(new_tbl_element)  # Remove from end
        parent.insert(tbl_index, new_tbl_element)  # Insert at same position
        logger.info("✅ Inserted new table at correct position")
        
        parent.remove(tbl_element)  # Remove old template table
        logger.info("✅ Removed old template table")
        
        # Add page break after data table
        break_after_data = OxmlElement('w:p')
        break_run_after_data = OxmlElement('w:r')
        break_element_after_data = OxmlElement('w:br')
        break_element_after_data.set(qn('w:type'), 'page')
        break_run_after_data.append(break_element_after_data)
        break_after_data.append(break_run_after_data)
        parent.insert(tbl_index + 1, break_after_data)
        logger.info("✅ Added page break after content data table")
        
        # Add summary table after data table
        _add_summary_table(doc, content_items, 'content', project_data)
        
        logger.info(f"✅ Content table replaced with {len(content_items)} items from JSONB attributes")
    else:
        logger.warning("⚠️ No table found in document to replace")

def _handle_wine_table(doc: Document, project_data: Dict):
    """Handle wine collection table rendering - uses JSONB attributes"""
    from docx.shared import Pt
    from docx.enum.text import WD_BREAK
    
    logger.info("🍷 Rendering wine collection table from JSONB attributes")
    
    # Get wine items from appraisal_items with type='wine'
    appraisal_items = project_data.get('appraisal_items', [])
    wine_items = [
        item
        for item in appraisal_items
        if item.get('item_type') in ['Wine', 'wine', 'Wines', 'wines']
    ]
    
    if not wine_items:
        logger.warning("No wine items found for wine table")
        return
    
    # Find the first table in the document and replace it
    if len(doc.tables) > 0:
        logger.info(f"📋 Found {len(doc.tables)} table(s) in document, replacing first one with wine data")
        old_table = doc.tables[0]
        
        # Get the parent element and position
        tbl_element = old_table._element
        parent = tbl_element.getparent()
        tbl_index = list(parent).index(tbl_element)
        logger.info(f"📍 Old table position: index {tbl_index}")
        
        # Create new table (will be added at end of document initially)
        logger.info("🔨 Creating new wine table...")
        new_table = doc.add_table(rows=1, cols=4)
        
        # Try to apply a style, fall back to Table Grid if not available
        try:
            new_table.style = 'Light Grid Accent 1'
        except KeyError:
            try:
                new_table.style = 'Table Grid'
            except KeyError:
                pass  # Use default table style
        
        # Header row
        header_cells = new_table.rows[0].cells
        header_cells[0].text = "Quantity"
        header_cells[1].text = "Bottle"
        header_cells[2].text = "Per Bottle Price"
        header_cells[3].text = "Total Price"
        
        # Make headers bold (no color)
        for cell in header_cells:
            # Set cell height for header row
            cell.height = Pt(25)
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(14)
        
        # Data rows
        logger.info(f"📝 Adding {len(wine_items)} wine items to table")
        for wine in wine_items:
            row_cells = new_table.add_row().cells
            
            # Parse description to extract quantity and price
            description = wine.get('description', '')
            quantity, price_per_bottle = _parse_description_for_coin_wine(description, 'wine')
            
            # Extract bottle description from template
            bottle_desc_match = re.search(r'Bottle Description:\s*([^\n]+)', description)
            
            row_cells[0].text = str(int(quantity)) if quantity else '0'
            row_cells[1].text = bottle_desc_match.group(1).strip() if bottle_desc_match else description.split('\n')[0][:50]
            
            # Format prices
            try:
                row_cells[2].text = f"${price_per_bottle:,.2f}"
            except:
                row_cells[2].text = "$0.00"
            
            # Auto-calculate and format total price (quantity * price_per_bottle)
            total_value = quantity * price_per_bottle
            try:
                row_cells[3].text = f"${total_value:,.2f}"
            except:
                row_cells[3].text = "$0.00"
            
            # Format cells
            for cell in row_cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(14)
        
        logger.info("🔄 Moving new table to replace old table...")
        
        # Move new table to correct position and remove old table (no page break)
        new_tbl_element = new_table._element
        doc._body._element.remove(new_tbl_element)  # Remove from end
        parent.insert(tbl_index, new_tbl_element)  # Insert at same position
        logger.info("✅ Inserted new table at correct position")
        
        parent.remove(tbl_element)  # Remove old template table
        logger.info("✅ Removed old template table")
        
        # Add images after the table
        _add_images_after_table(doc, wine_items, tbl_index + 1, parent)
        
        # Add page break after images (page break will be added after all images)
        # Count how many elements (paragraphs) were added for images
        images_added = len([item for item in wine_items if item.get('photo_path')])
        
        break_after_data = OxmlElement('w:p')
        break_run_after_data = OxmlElement('w:r')
        break_element_after_data = OxmlElement('w:br')
        break_element_after_data.set(qn('w:type'), 'page')
        break_run_after_data.append(break_element_after_data)
        break_after_data.append(break_run_after_data)
        parent.insert(tbl_index + 1 + images_added, break_after_data)
        logger.info("✅ Added page break after wine data table and images")
        
        # Add summary table after data table
        _add_summary_table(doc, wine_items, 'wine', project_data)
        
        logger.info(f"✅ Wine table replaced with {len(wine_items)} items from JSONB attributes")
    else:
        logger.warning("⚠️ No table found in document to replace")

def _add_summary_table(doc: Document, items: list, item_type: str, project_data: Dict):
    """Find summary section and replace its table with project summary data"""
    from docx.enum.text import WD_BREAK, WD_ALIGN_PARAGRAPH
    
    
    logger.info(f"📊 Searching for summary table to replace for {item_type}")
    
    # First, find all tables in the document
    if len(doc.tables) == 0:
        logger.warning("⚠️ No tables found in document, skipping summary replacement")
        return
    
    # Search for "summary" text that has a table after it
    # We need to find the RIGHT summary (not table of contents), so we check if there's a table nearby
    summary_paragraph = None
    summary_table_to_replace = None
    parent = None
    
    for idx, paragraph in enumerate(doc.paragraphs):
        if 'summary' in paragraph.text.lower():
            # Check if there's a table after this paragraph
            temp_parent = paragraph._element.getparent()
            para_element = paragraph._element
            para_position = list(temp_parent).index(para_element)
            
            # Look for table elements after this paragraph (within a reasonable distance)
            tables_found = []
            for i in range(para_position + 1, min(para_position + 50, len(list(temp_parent)))):
                element = list(temp_parent)[i]
                if element.tag.endswith('}tbl'):  # This is a table element
                    # Find which table object this corresponds to
                    for tbl in doc.tables:
                        if tbl._element == element:
                            tables_found.append(tbl)
                            break
                    if tables_found:
                        break  # Stop after finding first table
            
            # If we found a table after this summary text, this is the right one
            if tables_found:
                summary_paragraph = paragraph
                parent = temp_parent
                logger.info(f"✅ Found summary section with table at paragraph {idx}: '{paragraph.text.strip()}'")
                
                # Determine which table to use
                if len(tables_found) > 1:
                    summary_table_to_replace = tables_found[-1]  # Use the LAST table
                    logger.info(f"📋 Found {len(tables_found)} tables after summary, using last one")
                else:
                    summary_table_to_replace = tables_found[0]
                    logger.info(f"📋 Found table after summary section")
                break
    
    if not summary_paragraph or not summary_table_to_replace:
        logger.warning("⚠️ No summary section with table found, skipping replacement")
        return
    
    # Get table position
    tbl_element = summary_table_to_replace._element
    tbl_index = list(parent).index(tbl_element)
    
    # Get summary paragraph position
    summary_para_element = summary_paragraph._element
    summary_para_index = list(parent).index(summary_para_element)
    
    # Step 1: Remove the existing summary text paragraph and ALL content between it and the table
    parent.remove(summary_para_element)
    logger.info("✅ Removed existing summary text")
    
    # Aggressively remove ALL elements between the old summary position and the table
    # This ensures we clean up any page breaks, empty paragraphs, whitespace, or other elements
    elements_removed = 0
    max_cleanup = 50  # Increased safety limit to handle more elements
    cleanup_count = 0
    
    while summary_para_index < len(list(parent)) and cleanup_count < max_cleanup:
        next_element = list(parent)[summary_para_index]
        
        # Stop if we've reached the table
        if next_element == tbl_element:
            logger.info("✅ Reached the table, stopping cleanup")
            break
        
        # Check if this element should be removed
        should_remove = False
        
        if next_element.tag.endswith('}p'):  # Paragraph
            # Get all text from the paragraph and its children
            full_text = ''.join(next_element.itertext()) if hasattr(next_element, 'itertext') else ''
            
            # Remove if:
            # 1. It's completely empty
            # 2. It only contains whitespace (spaces, tabs, newlines, etc.)
            # 3. It contains a page break
            # 4. It has no text content (just formatting)
            if not full_text or not full_text.strip() or full_text.isspace():
                should_remove = True
                logger.info(f"   → Removing empty/whitespace paragraph")
            else:
                # Check for page break in children
                for child in next_element.iter():
                    if 'br' in str(child.tag).lower() or 'break' in str(child.tag).lower():
                        should_remove = True
                        logger.info(f"   → Removing paragraph with page break")
                        break
        
        if should_remove:
            parent.remove(next_element)
            elements_removed += 1
            cleanup_count += 1
        else:
            # If we encounter actual content, stop cleaning
            logger.info(f"   → Found content paragraph, stopping cleanup")
            break
    
    if elements_removed > 0:
        logger.info(f"✅ Cleaned up {elements_removed} element(s) between old summary and table")
    
    # Recalculate table index after removing summary paragraph and cleanup
    tbl_index = list(parent).index(tbl_element)
    
    # Step 1.5: Aggressively clean up ALL empty paragraphs immediately before the table
    # This ensures there are no extra spaces before the summary heading
    extra_elements_removed = 0
    max_extra_cleanup = 50  # Safety limit
    extra_cleanup_count = 0
    
    # Work backwards from just before the table position
    check_index = tbl_index - 1
    while check_index >= 0 and extra_cleanup_count < max_extra_cleanup:
        if check_index < len(list(parent)):
            element = list(parent)[check_index]
            
            should_remove_extra = False
            if element.tag.endswith('}p'):  # Paragraph
                full_text = ''.join(element.itertext()) if hasattr(element, 'itertext') else ''
                
                # Remove if empty or whitespace only
                if not full_text or not full_text.strip() or full_text.isspace():
                    should_remove_extra = True
                    logger.info(f"   → Extra cleanup: Removing empty/whitespace paragraph before summary heading")
            
            if should_remove_extra:
                parent.remove(element)
                extra_elements_removed += 1
                extra_cleanup_count += 1
                # Recalculate indices after removal
                tbl_index = list(parent).index(tbl_element)
                check_index = tbl_index - 1  # Reset to check again from table position
            else:
                # Found content or non-paragraph element, stop cleaning
                logger.info(f"   → Found content before table, stopping extra cleanup")
                break
        else:
            break
    
    if extra_elements_removed > 0:
        logger.info(f"✅ Extra cleanup removed {extra_elements_removed} empty element(s) before summary heading position")

    page_break_before_summary = OxmlElement('w:p')
    page_break_run = OxmlElement('w:r')
    page_break_el = OxmlElement('w:br')
    page_break_el.set(qn('w:type'), 'page')
    page_break_run.append(page_break_el)
    page_break_before_summary.append(page_break_run)
    parent.insert(tbl_index, page_break_before_summary)
    logger.info("✅ Added page break BEFORE SUMMARY heading")

    # Final recalculation of table index before inserting heading
    tbl_index = list(parent).index(tbl_element)
    
    # Step 2: Add new centered "SUMMARY" heading at the position where summary was
    summary_heading_para = OxmlElement('w:p')
    # Add paragraph properties for center alignment
    pPr = OxmlElement('w:pPr')
    jc = OxmlElement('w:jc')
    jc.set(qn('w:val'), 'center')
    pPr.append(jc)
    summary_heading_para.append(pPr)
    # Add the text run
    summary_run = OxmlElement('w:r')
    summary_rPr = OxmlElement('w:rPr')
    # Make it bold
    bold = OxmlElement('w:b')
    summary_rPr.append(bold)
    # Set font size to 14pt
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), '28')  # 28 half-points = 14pt
    summary_rPr.append(sz)
    summary_run.append(summary_rPr)
    # Add text
    summary_text = OxmlElement('w:t')
    summary_text.text = "SUMMARY"
    summary_run.append(summary_text)
    summary_heading_para.append(summary_run)
    parent.insert(tbl_index, summary_heading_para)
    logger.info("✅ Inserted centered SUMMARY heading (no page break before)")
    
    # Recalculate table index again after adding heading
    tbl_index = list(parent).index(tbl_element)
    
    # Calculate totals based on item type
    total_items = len(items)
    total_value = 0.0
    
    if item_type == 'coin':
        for item in items:
            try:
                quantity = float(item.get('quantity', 0))
                price = float(item.get('appraised_price', 0))
                total_value += (quantity * price)
            except:
                pass
    elif item_type == 'wine':
        for item in items:
            try:
                total_value += float(item.get('total_price', 0))
            except:
                pass
    elif item_type == 'content':
        for item in items:
            try:
                total_value += float(item.get('fair_market_value', 0))
            except:
                pass
    elif item_type == 'image_based':
        # For image-based templates, get value from appraisal_items
        appraisal_items = project_data.get('appraisal_items', [])
        for item in appraisal_items:
            try:
                total_value += float(item.get('appraised_value', 0))
            except:
                pass
    
    # Create new summary table - 2 rows only (headers and values) like the image
    new_summary_table = doc.add_table(rows=2, cols=2)
    
    # Try to apply a style, fall back to Table Grid if not available
    try:
        new_summary_table.style = 'Table Grid'
    except KeyError:
        pass  # Use default table style
    
    # Set column widths (equal width for both columns)
    for row in new_summary_table.rows:
        row.cells[0].width = 3250000  # ~3.25 inches
        row.cells[1].width = 3250000  # ~3.25 inches
    
    # Row 1 (Headers): Total number of items | Total appraised value
    header_cells = new_summary_table.rows[0].cells
    header_cells[0].text = "Total number of items"
    header_cells[1].text = "Total appraised value"
    
    # Make header row bold and taller with 14pt font
    for cell in header_cells:
        cell.height = Pt(25)
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(14)
    
    # Row 2 (Values): Item count | Total value
    value_cells = new_summary_table.rows[1].cells
    value_cells[0].text = str(total_items)
    value_cells[1].text = str(int(total_value))  # No dollar sign, no decimals, just number
    
    # Format value row with 14pt font, centered
    for cell in value_cells:
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.font.size = Pt(14)
    
    # Center align the entire table
    new_summary_table.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Step 3: Move new table to correct position (after SUMMARY heading) and remove old table
    new_tbl_element = new_summary_table._element
    doc._body._element.remove(new_tbl_element)  # Remove from end
    parent.insert(tbl_index + 1, new_tbl_element)  # Insert after heading (+1)
    logger.info("✅ Inserted new summary table")
    
    parent.remove(tbl_element)  # Remove old template table
    logger.info("✅ Removed old template table")
    
    # Step 4: Add page break after summary table
    summary_tbl_index = list(parent).index(new_tbl_element)
    break_after_summary = OxmlElement('w:p')
    break_run_after_summary = OxmlElement('w:r')
    break_element_after_summary = OxmlElement('w:br')
    break_element_after_summary.set(qn('w:type'), 'page')
    break_run_after_summary.append(break_element_after_summary)
    break_after_summary.append(break_run_after_summary)
    parent.insert(summary_tbl_index + 1, break_after_summary)
    logger.info("✅ Added page break after summary table")
    
    # Step 5: Aggressively clean up ALL empty lines/spaces after the page break until we find text content
    cleanup_index = summary_tbl_index + 2  # Start after the page break we just added
    elements_cleaned = 0
    max_cleanup_after = 100  # Increased safety limit to handle more elements
    cleanup_count_after = 0
    
    while cleanup_index < len(list(parent)) and cleanup_count_after < max_cleanup_after:
        # Check if we're at the end of the document
        if cleanup_index >= len(list(parent)):
            logger.info("   → Reached end of document, stopping cleanup")
            break
            
        element_to_check = list(parent)[cleanup_index]
        
        # Check if this element should be removed
        should_remove_after = False
        if element_to_check.tag.endswith('}p'):  # Paragraph
            full_text = ''.join(element_to_check.itertext()) if hasattr(element_to_check, 'itertext') else ''
            
            # Remove if:
            # 1. It's completely empty
            # 2. It only contains whitespace (spaces, tabs, newlines, etc.)
            # 3. It has no text content (just formatting)
            if not full_text or not full_text.strip() or full_text.isspace():
                should_remove_after = True
                logger.info(f"   → Cleaning up empty/whitespace paragraph after summary table")
        
        if should_remove_after:
            parent.remove(element_to_check)
            elements_cleaned += 1
            cleanup_count_after += 1
            # Don't increment cleanup_index since we removed an element
        else:
            # Found actual content, stop cleaning
            logger.info(f"   → Found content after summary table, stopping cleanup")
            break
    
    if elements_cleaned > 0:
        logger.info(f"✅ Cleaned up {elements_cleaned} empty element(s) after summary table")
    
    logger.info(f"✅ Summary section complete: {total_items} items, ${total_value:,.2f} total value")

# ==================== WATERMARK FUNCTIONS ====================

def _add_watermark(doc: Document):
    """Add DRAFT watermark as a true background watermark using VML shape with textbox"""
    try:
        logger.info("💧💧💧 Adding DRAFT watermark using VML shape with textbox 💧💧💧")
        logger.info(f"Document has {len(doc.sections)} sections")
        
        watermarks_added = 0
        
        # Add watermark to EVERY section
        for section_idx, section in enumerate(doc.sections):
            try:
                logger.info(f"📍 Processing section {section_idx+1}/{len(doc.sections)}")
                
                # Check if header exists
                if not section.header:
                    logger.warning(f"  Section {section_idx+1} has no header, skipping")
                    continue
                
                # Get the header and unlink from previous section
                logger.info(f"  Accessing header for section {section_idx+1}")
                header = section.header
                logger.info(f"  Header type: {type(header)}")
                
                logger.info(f"  Unlinking header from previous section")
                header.is_linked_to_previous = False
                
                # Add paragraph to header
                logger.info(f"  Adding paragraph to header")
                header_para = header.add_paragraph()
                logger.info(f"  Header paragraph created: {type(header_para)}")
                
                # Create VML watermark using parse_xml with complete XML
                logger.info(f"  Creating VML watermark with parse_xml")
                
                # Define namespace URIs
                w_ns = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
                v_ns = 'urn:schemas-microsoft-com:vml'
                o_ns = 'urn:schemas-microsoft-com:office:office'
                
                watermark_xml = f'''<w:p xmlns:w="{w_ns}" xmlns:v="{v_ns}" xmlns:o="{o_ns}">
                    <w:r>
                        <w:pict>
                            <v:shape id="Watermark{section_idx}" type="#_x0000_t136"
                                style="position:absolute;left:0;top:0;width:468pt;height:200pt;z-index:-251654144;mso-position-horizontal:center;mso-position-vertical:center;mso-position-horizontal-relative:page;mso-position-vertical-relative:page;mso-wrap-edited:f"
                                rotation="315" fillcolor="#d3d3d3" stroked="f">
                                <v:textbox style="mso-fit-shape-to-text:t">
                                    <w:txbxContent>
                                        <w:p>
                                            <w:r>
                                                <w:rPr>
                                                    <w:color w:val="D3D3D3"/>
                                                    <w:sz w:val="120"/>
                                                </w:rPr>
                                                <w:t>DRAFT</w:t>
                                            </w:r>
                                        </w:p>
                                    </w:txbxContent>
                                </v:textbox>
                            </v:shape>
                        </w:pict>
                    </w:r>
                </w:p>'''
                
                watermark_element = parse_xml(watermark_xml)
                logger.info(f"  Watermark XML parsed successfully, type: {type(watermark_element)}")
                
                # Replace the empty paragraph with our watermark paragraph
                header._element.replace(header_para._element, watermark_element)
                logger.info(f"  ✅ Watermark paragraph inserted into header for section {section_idx}")
                
                watermarks_added += 1
                logger.info(f"✅ Successfully added watermark to section {section_idx+1}")
                
            except Exception as section_error:
                logger.error(f"❌ Failed to add watermark to section {section_idx+1}: {str(section_error)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"✅ Successfully added {watermarks_added} watermarks total")
        
        if watermarks_added == 0:
            logger.error("⚠️ WARNING: No watermarks were added!")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Critical error adding watermark: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def _remove_existing_watermarks(doc: Document):
    """Remove any existing watermarks from the document - NUCLEAR approach"""
    try:
        logger.info("🚫🚫🚫 Starting AGGRESSIVE watermark removal 🚫🚫🚫")
        
        # Strategy 1: Remove from section properties (VML background watermarks)
        for section_idx, section in enumerate(doc.sections):
            try:
                sectPr = section._sectPr
                elements_removed = 0
                
                # Remove all v:background elements
                for child in list(sectPr):
                    if 'background' in str(child.tag).lower():
                        sectPr.remove(child)
                        elements_removed += 1
                        logger.info(f"Removed background element from section {section_idx+1}")
                
                logger.info(f"Section {section_idx+1}: Removed {elements_removed} background elements")
            except Exception as vml_error:
                logger.warning(f"Error removing VML watermarks from section {section_idx+1}: {str(vml_error)}")
        
        # Strategy 2: Remove ALL paragraphs from headers/footers that contain DRAFT (aggressive)
        for section_idx, section in enumerate(doc.sections):
            logger.info(f"Processing section {section_idx+1} for header/footer watermarks")
            
            # Process ALL header types
            headers_to_check = []
            
            # Main header
            if section.header:
                headers_to_check.append(('main header', section.header))
            
            # First page header
            try:
                if section.first_page_header:
                    headers_to_check.append(('first page header', section.first_page_header))
            except:
                pass
            
            # Even page header
            try:
                if section.even_page_header:
                    headers_to_check.append(('even page header', section.even_page_header))
            except:
                pass
            
            # Process each header
            for header_name, header in headers_to_check:
                logger.info(f"Checking {header_name} in section {section_idx+1}")
                paragraphs_to_remove = []
                
                # Check every paragraph
                for para_idx, paragraph in enumerate(list(header.paragraphs)):
                    para_text = paragraph.text.strip().upper()
                    
                    # Remove if it contains DRAFT anywhere
                    if 'DRAFT' in para_text:
                        paragraphs_to_remove.append(paragraph)
                        logger.info(f"Marked paragraph {para_idx} for removal from {header_name}: '{paragraph.text[:50]}'")
                    
                    # Also check for VML/drawing elements
                    try:
                        p_element = paragraph._p
                        
                        # Check for drawings
                        drawings = p_element.xpath('.//w:drawing')
                        if drawings:
                            # Check if any text in the drawing contains DRAFT
                            for drawing in drawings:
                                text_elements = drawing.xpath('.//w:t')
                                for text_elem in text_elements:
                                    if text_elem.text and 'DRAFT' in text_elem.text.upper():
                                        paragraphs_to_remove.append(paragraph)
                                        logger.info(f"Found drawing with DRAFT in {header_name}")
                                        break
                        
                        # Check for VML shapes
                        picts = p_element.xpath('.//w:pict')
                        if picts:
                            paragraphs_to_remove.append(paragraph)
                            logger.info(f"Found VML shape in {header_name} - removing as precaution")
                        
                        # Check for positioned paragraphs (framePr)
                        pPr = p_element.xpath('.//w:pPr')
                        if pPr:
                            for pr in pPr:
                                frame_props = pr.xpath('.//w:framePr')
                                if frame_props:
                                    paragraphs_to_remove.append(paragraph)
                                    logger.info(f"Found positioned paragraph in {header_name} - removing")
                                    break
                    
                    except Exception as check_error:
                        logger.warning(f"Error checking paragraph elements: {str(check_error)}")
                
                # Remove marked paragraphs
                removed_count = 0
                for paragraph in paragraphs_to_remove:
                    try:
                        paragraph._element.getparent().remove(paragraph._element)
                        removed_count += 1
                    except Exception as remove_error:
                        logger.warning(f"Could not remove paragraph: {str(remove_error)}")
                
                logger.info(f"✅ Removed {removed_count} paragraphs from {header_name}")
            
            # Process footers (same approach)
            footers_to_check = []
            
            if section.footer:
                footers_to_check.append(('main footer', section.footer))
            
            try:
                if section.first_page_footer:
                    footers_to_check.append(('first page footer', section.first_page_footer))
            except:
                pass
            
            try:
                if section.even_page_footer:
                    footers_to_check.append(('even page footer', section.even_page_footer))
            except:
                pass
            
            for footer_name, footer in footers_to_check:
                logger.info(f"Checking {footer_name} in section {section_idx+1}")
                paragraphs_to_remove = []
                
                for para_idx, paragraph in enumerate(list(footer.paragraphs)):
                    para_text = paragraph.text.strip().upper()
                    
                    if 'DRAFT' in para_text:
                        paragraphs_to_remove.append(paragraph)
                        logger.info(f"Marked paragraph {para_idx} for removal from {footer_name}")
                
                removed_count = 0
                for paragraph in paragraphs_to_remove:
                    try:
                        paragraph._element.getparent().remove(paragraph._element)
                        removed_count += 1
                    except Exception as remove_error:
                        logger.warning(f"Could not remove paragraph: {str(remove_error)}")
                
                logger.info(f"✅ Removed {removed_count} paragraphs from {footer_name}")
        
        # Strategy 3: Remove DRAFT text from body paragraphs
        logger.info("Checking body paragraphs for DRAFT watermarks")
        paragraphs_to_remove = []
        
        for i, paragraph in enumerate(doc.paragraphs):
            paragraph_text = paragraph.text.strip().upper()
            
            # Remove standalone DRAFT paragraphs
            if paragraph_text == 'DRAFT' or paragraph_text == '[DRAFT]':
                paragraphs_to_remove.append(paragraph)
                logger.info(f"Found standalone DRAFT paragraph at index {i}")
            
            # Clear DRAFT from runs with watermark characteristics
            for run in paragraph.runs:
                if run.text and 'DRAFT' in run.text.upper():
                    # Check for watermark characteristics
                    is_watermark = False
                    
                    # Gray color check
                    try:
                        if run.font.color and run.font.color.rgb:
                            rgb = run.font.color.rgb
                            if rgb.red == rgb.green == rgb.blue and rgb.red > 100:
                                is_watermark = True
                    except:
                        pass
                    
                    # Large font check
                    try:
                        if run.font.size and run.font.size >= Pt(30):
                            is_watermark = True
                    except:
                        pass
                    
                    # Bold check
                    try:
                        if run.font.bold:
                            is_watermark = True
                    except:
                        pass
                    
                    if is_watermark:
                        run.text = run.text.replace('DRAFT', '').replace('Draft', '').replace('draft', '')
                        logger.info(f"Cleared DRAFT from watermark run in paragraph {i}")
        
        # Remove marked paragraphs
        body_removed = 0
        for paragraph in paragraphs_to_remove:
            try:
                paragraph._element.getparent().remove(paragraph._element)
                body_removed += 1
            except Exception as e:
                logger.warning(f"Could not remove body paragraph: {str(e)}")
        
        logger.info(f"✅ Removed {body_removed} DRAFT paragraphs from document body")
        
        # Strategy 4: Remove shapes and drawings with DRAFT text
        logger.info("Checking for watermark shapes and drawings")
        try:
            document_part = doc.part
            doc_element = document_part.element
            
            shapes_removed = 0
            
            # Find all drawings
            drawing_elements = doc_element.xpath('.//w:drawing')
            logger.info(f"Found {len(drawing_elements)} drawing elements to check")
            
            for drawing in list(drawing_elements):
                should_remove = False
                
                # Check for DRAFT in text elements
                text_elements = drawing.xpath('.//w:t')
                for text_elem in text_elements:
                    if text_elem.text and 'DRAFT' in text_elem.text.upper():
                        should_remove = True
                        logger.info(f"Found drawing with DRAFT text: '{text_elem.text}'")
                        break
                
                # Also check DrawingML text
                if not should_remove:
                    a_text_elements = drawing.xpath('.//a:t', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                    for text_elem in a_text_elements:
                        if text_elem.text and 'DRAFT' in text_elem.text.upper():
                            should_remove = True
                            logger.info(f"Found DrawingML with DRAFT text: '{text_elem.text}'")
                            break
                
                if should_remove:
                    try:
                        parent = drawing.getparent()
                        if parent is not None:
                            parent.remove(drawing)
                            shapes_removed += 1
                    except Exception as e:
                        logger.warning(f"Could not remove drawing: {str(e)}")
            
            # Find all VML shapes (w:pict)
            pict_elements = doc_element.xpath('.//w:pict')
            logger.info(f"Found {len(pict_elements)} VML pict elements to check")
            
            for pict in list(pict_elements):
                should_remove = False
                
                # Check for textpath with DRAFT
                textpath_elements = pict.xpath('.//v:textpath', namespaces={'v': 'urn:schemas-microsoft-com:vml'})
                for textpath in textpath_elements:
                    text_content = textpath.get('string', '')
                    if 'DRAFT' in text_content.upper():
                        should_remove = True
                        logger.info(f"Found VML textpath with DRAFT: '{text_content}'")
                        break
                
                # Check for shape IDs containing watermark
                shape_elements = pict.xpath('.//v:shape', namespaces={'v': 'urn:schemas-microsoft-com:vml'})
                for shape in shape_elements:
                    shape_id = shape.get('id', '')
                    if 'watermark' in shape_id.lower():
                        should_remove = True
                        logger.info(f"Found VML shape with watermark ID: '{shape_id}'")
                        break
                
                if should_remove:
                    try:
                        parent = pict.getparent()
                        if parent is not None:
                            parent.remove(pict)
                            shapes_removed += 1
                    except Exception as e:
                        logger.warning(f"Could not remove VML pict: {str(e)}")
            
            logger.info(f"✅ Removed {shapes_removed} watermark shapes/drawings")
        
        except Exception as shape_error:
            logger.error(f"Error removing shapes: {str(shape_error)}")
        
        logger.info("✅✅✅ AGGRESSIVE watermark removal completed ✅✅✅")
        
    except Exception as e:
        logger.error(f"Critical error in watermark removal: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

def _remove_watermarks_from_header_footer(header_footer):
    """Remove watermarks from header or footer"""
    try:
        logger.info("Starting watermark removal from header/footer")
        
        # First, remove entire paragraphs that are watermarks
        paragraphs_to_remove = []
        
        # Look for VML watermarks and shapes with DRAFT text
        for paragraph in list(header_footer.paragraphs):
            should_remove = False
            paragraph_text = paragraph.text.strip().upper()
            
            # Check if this paragraph contains DRAFT watermark text
            if 'DRAFT' in paragraph_text:
                logger.info(f"Found paragraph with DRAFT text: '{paragraph.text}'")
                
                # Check if it's likely a watermark based on properties
                try:
                    p_element = paragraph._p
                    pPr = p_element.get_or_add_pPr()
                    
                    # Check for framePr (positioned paragraphs used for watermarks)
                    frame_props = pPr.xpath('.//w:framePr')
                    if frame_props:
                        should_remove = True
                        logger.info("Found framePr - this is a positioned watermark paragraph")
                    
                    # Check for centered alignment with large font (watermark characteristics)
                    if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                        for run in paragraph.runs:
                            if run.font.size and run.font.size >= Pt(60):  # Large font
                                should_remove = True
                                logger.info(f"Found centered DRAFT with large font: {run.font.size}")
                                break
                
                except Exception as check_error:
                    logger.warning(f"Error checking paragraph properties: {str(check_error)}")
                
                # Check for w:pict elements (VML shapes)
                try:
                    p_element = paragraph._p
                    pict_elements = p_element.xpath('.//w:pict')
                    
                    if pict_elements:
                        logger.info("Found w:pict elements")
                        for pict in pict_elements:
                            # Check for v:shape elements that might be watermarks
                            shape_elements = pict.xpath('.//v:shape')
                            for shape in shape_elements:
                                # Check if this is a watermark shape
                                shape_id = shape.get('id', '')
                                if 'Watermark' in shape_id or 'watermark' in shape_id:
                                    should_remove = True
                                    logger.info(f"Found VML watermark shape: {shape_id}")
                                    break
                                
                                # Check for textpath with DRAFT text
                                textpath_elements = shape.xpath('.//v:textpath')
                                for textpath in textpath_elements:
                                    text_content = textpath.get('string', '')
                                    if 'DRAFT' in text_content.upper():
                                        should_remove = True
                                        logger.info(f"Found VML watermark with DRAFT text: {text_content}")
                                        break
                            
                            if should_remove:
                                break
                
                except Exception as vml_error:
                    logger.warning(f"Error checking for VML elements: {str(vml_error)}")
                
                # Check for w:drawing elements
                try:
                    p_element = paragraph._p
                    drawing_elements = p_element.xpath('.//w:drawing')
                    
                    if drawing_elements:
                        logger.info("Found w:drawing elements")
                        for drawing in drawing_elements:
                            # Check for text elements with DRAFT
                            text_elements = drawing.xpath('.//w:t')
                            for text_elem in text_elements:
                                if text_elem.text and 'DRAFT' in text_elem.text.upper():
                                    should_remove = True
                                    logger.info(f"Found drawing watermark with DRAFT text: {text_elem.text}")
                                    break
                            
                            # Also check DrawingML text
                            a_text_elements = drawing.xpath('.//a:t', namespaces={'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'})
                            for text_elem in a_text_elements:
                                if text_elem.text and 'DRAFT' in text_elem.text.upper():
                                    should_remove = True
                                    logger.info(f"Found DrawingML watermark with DRAFT text: {text_elem.text}")
                                    break
                            
                            if should_remove:
                                break
                
                except Exception as drawing_error:
                    logger.warning(f"Error checking for drawing elements: {str(drawing_error)}")
            
            # If we determined this is a watermark paragraph, mark it for removal
            if should_remove:
                paragraphs_to_remove.append(paragraph)
        
        # Remove identified watermark paragraphs
        for paragraph in paragraphs_to_remove:
            try:
                paragraph._element.getparent().remove(paragraph._element)
                logger.info("✅ Removed watermark paragraph from header/footer")
            except Exception as e:
                logger.warning(f"Could not remove watermark paragraph: {str(e)}")
        
        logger.info(f"Removed {len(paragraphs_to_remove)} watermark paragraphs in first pass")
        
        # Second pass: Remove any remaining "DRAFT" text-only watermarks
        additional_removals = []
        
        for paragraph in list(header_footer.paragraphs):
            paragraph_text = paragraph.text.strip()
            
            # Check if this paragraph contains only DRAFT text (case insensitive)
            if paragraph_text.upper() == 'DRAFT' or paragraph_text.upper() == '[DRAFT]':
                additional_removals.append(paragraph)
                logger.info(f"Found standalone DRAFT text paragraph: '{paragraph_text}'")
            elif 'DRAFT' in paragraph_text.upper() and len(paragraph_text) < 20:
                # Short paragraph with DRAFT is likely a watermark
                additional_removals.append(paragraph)
                logger.info(f"Found short DRAFT paragraph (likely watermark): '{paragraph_text}'")
            elif 'DRAFT' in paragraph_text.upper() and len(paragraph_text) < 20:
                # Short paragraph with DRAFT is likely a watermark
                additional_removals.append(paragraph)
                logger.info(f"Found short DRAFT paragraph (likely watermark): '{paragraph_text}'")
            else:
                # Check individual runs for watermark characteristics
                runs_to_clear = []
                for run in paragraph.runs:
                    if run.text and 'DRAFT' in run.text.upper():
                        # Check if this looks like a watermark (gray, bold, large, or italic)
                        is_watermark = False
                        
                        # Check for gray color (watermarks are typically gray)
                        if run.font.color and run.font.color.rgb:
                            rgb = run.font.color.rgb
                            # Any gray shade (R=G=B and value > 100)
                            if rgb.red == rgb.green == rgb.blue and rgb.red > 100:
                                is_watermark = True
                                logger.info(f"Found gray DRAFT text: RGB({rgb.red},{rgb.green},{rgb.blue})")
                        
                        # Check for bold formatting (watermarks are often bold)
                        if run.font.bold:
                            is_watermark = True
                            logger.info("Found bold DRAFT text")
                        
                        # Check for italic formatting
                        if run.font.italic:
                            is_watermark = True
                            logger.info("Found italic DRAFT text")
                        
                        # Check for large size (watermarks are large)
                        if run.font.size and run.font.size >= Pt(40):
                            is_watermark = True
                            logger.info(f"Found large DRAFT text: {run.font.size}")
                        
                        if is_watermark:
                            runs_to_clear.append(run)
                
                # Clear watermark runs
                for run in runs_to_clear:
                    logger.info(f"Clearing DRAFT watermark run: '{run.text}'")
                    run.text = ''
        
        # Remove additional watermark paragraphs
        for paragraph in additional_removals:
            try:
                paragraph._element.getparent().remove(paragraph._element)
                logger.info("✅ Removed additional DRAFT watermark paragraph")
            except Exception as e:
                logger.warning(f"Could not remove watermark paragraph: {str(e)}")
        
        logger.info(f"Removed {len(additional_removals)} additional watermark paragraphs in second pass")
        
        # Third pass: Check for paragraphs with frame positioning (positioned watermarks)
        positioned_removals = 0
        for paragraph in list(header_footer.paragraphs):
            try:
                p_element = paragraph._p
                pPr = p_element.get_or_add_pPr()
                
                # Check if this paragraph has frame properties (positioned paragraphs used by watermarks)
                frame_props = pPr.xpath('.//w:framePr')
                if frame_props:
                    # If it has framePr and contains DRAFT, it's definitely a watermark
                    if 'DRAFT' in paragraph.text.upper():
                        paragraph._element.getparent().remove(paragraph._element)
                        positioned_removals += 1
                        logger.info(f"✅ Removed positioned DRAFT watermark: '{paragraph.text}'")
                    else:
                        # Even if no DRAFT text visible, positioned paragraphs in headers are often watermarks
                        logger.info(f"Found positioned paragraph (potential watermark): '{paragraph.text}'")
            except Exception as e:
                logger.warning(f"Error checking for positioned watermark: {str(e)}")
        
        logger.info(f"Removed {positioned_removals} positioned watermark paragraphs in third pass")
        logger.info("✅ Watermark removal from header/footer completed")
        
    except Exception as e:
        logger.error(f"Could not remove watermarks from header/footer: {str(e)}")


def _clear_content_between_item1_and_last_fmv(doc: Document, item1_paragraph) -> None:
    """Clear all content between Item 1 and the last Fair Market Value occurrence"""
    try:
        logger.info("=== STARTING CONTENT CLEARING ===")
        
        # Find Item 1 paragraph index by text content
        item1_index = -1
        item1_text = item1_paragraph.text.strip()
        logger.info(f"Looking for Item 1 paragraph with text: '{item1_text}'")
        
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip() == item1_text:
                item1_index = i
                logger.info(f"Found Item 1 at paragraph index {i}: '{paragraph.text.strip()}'")
                break
        
        if item1_index == -1:
            logger.warning(f"Could not find Item 1 paragraph with text '{item1_text}'")
            return
        
        # Skip excessive paragraph logging
        
        # Find the last Fair Market Value paragraph
        last_fmv_index = -1
        for i in range(len(doc.paragraphs) - 1, item1_index, -1):  # Search backwards from end
            text = doc.paragraphs[i].text.strip()
            if 'Fair Market Value' in text and '$' in text:
                last_fmv_index = i
                logger.info(f"Found last Fair Market Value at paragraph {i}: {text[:50]}...")
                break
        
        if last_fmv_index == -1:
            logger.info("No existing Fair Market Value found, will clear content after Item 1")
            # If no FMV found, clear everything after Item 1 until we hit a summary section
            for i in range(len(doc.paragraphs) - 1, item1_index, -1):
                text = doc.paragraphs[i].text.strip()
                if ('SUMMARY' in text.upper() or 
                    'TOTAL' in text.upper() or 
                    'APPRAISER' in text.upper()):
                    last_fmv_index = i
                    logger.info(f"Using summary section as boundary: {text[:50]}...")
                    break
        
        # Remove all paragraphs and tables between Item 1 and last FMV (inclusive)
        elements_to_remove = []
        parent = item1_paragraph._element.getparent()
        
        # Get the range of elements to remove
        item1_element = item1_paragraph._element
        item1_element_index = list(parent).index(item1_element)
        
        if last_fmv_index > item1_index:
            last_fmv_element = doc.paragraphs[last_fmv_index]._element
            last_fmv_element_index = list(parent).index(last_fmv_element)
            
            # Collect all elements from Item 1 to last FMV (inclusive)
            for i in range(item1_element_index, last_fmv_element_index + 1):
                element = parent[i]
                elements_to_remove.append(element)
        else:
            # If no FMV boundary found, remove elements from Item 1 until we find a summary
            all_elements = list(parent)
            for i in range(item1_element_index, len(all_elements)):
                element = all_elements[i]
                
                # Check if this element is a paragraph with summary content
                if element.tag.endswith('}p'):
                    for paragraph in doc.paragraphs:
                        if paragraph._element == element:
                            text = paragraph.text.strip()
                            if ('SUMMARY' in text.upper() or 
                                'TOTAL' in text.upper() or 
                                'APPRAISER' in text.upper()):
                                logger.info(f"Stopping at summary: {text[:50]}...")
                                goto_end = True
                                break
                    if 'goto_end' in locals():
                        break
                
                elements_to_remove.append(element)
        
        # Remove the collected elements
        for element in elements_to_remove:
            try:
                parent.remove(element)
            except Exception as e:
                logger.warning(f"Could not remove element: {str(e)}")
        
        logger.info(f"Cleared {len(elements_to_remove)} elements including Item 1 and last Fair Market Value")
        
    except Exception as e:
        logger.error(f"Error clearing content between Item 1 and last FMV: {str(e)}")
        # Don't raise exception, just log and continue