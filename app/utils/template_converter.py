import re
import os
from typing import Dict, List, Tuple
from docx import Document
from docx.shared import Inches, RGBColor, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.shared import OxmlElement, qn
import logging
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt
from docx import Document



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
                                add_watermark: bool = False) -> str:
    """Generate report from template using project data"""
    try:
        doc = Document(template_path)
        logger.info("⭐⭐⭐ DOCUMENT LOADED SUCCESSFULLY ⭐⭐⭐")
        
        # Replace text fields in main document paragraphs
        for paragraph in doc.paragraphs:
            _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Replace text fields in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Replace text fields in text boxes on the first page
        logger.info("💬💬💬 ABOUT TO PROCESS TEXT BOXES ON FIRST PAGE 💬💬💬")
        _handle_textboxes_first_page(doc, field_mappings, project_data)
        logger.info("💬💬💬 TEXT BOX PROCESSING COMPLETED 💬💬💬")
        
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
        
        # Handle appraisal items and images
        logger.info("🔥🔥🔥 ABOUT TO CALL _handle_appraisal_items 🔥🔥🔥")
        _handle_appraisal_items(doc, project_data)
        logger.info("🔥🔥🔥 _handle_appraisal_items COMPLETED 🔥🔥🔥")
        
        # Special pass for headers and footers
        logger.info("🔄🔄🔄 PERFORMING SPECIAL HEADER/FOOTER PLACEHOLDER CHECK 🔄🔄🔄")
        _ensure_headers_footers_replaced(doc, field_mappings, project_data)
        logger.info("🔄🔄🔄 HEADER/FOOTER PLACEHOLDER CHECK COMPLETED 🔄🔄🔄")
        
        # Final pass to catch any remaining placeholders
        logger.info("🔍🔍🔍 PERFORMING FINAL PLACEHOLDER CHECK 🔍🔍🔍")
        _final_placeholder_check(doc, field_mappings, project_data)
        logger.info("🔍🔍🔍 FINAL PLACEHOLDER CHECK COMPLETED 🔍🔍🔍")
        
        # Remove any existing watermarks from the template only if we're not adding a new one
        if not add_watermark:
            _remove_existing_watermarks(doc)
        
        # Add watermark if requested
        if add_watermark:
            _add_watermark(doc)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise ReportGenerationError(f"Failed to generate report: {str(e)}")

def _ensure_headers_footers_replaced(doc: Document, field_mappings: Dict, project_data: Dict):
    """Special pass to ensure all header and footer placeholders are replaced"""
    import re
    pattern = r'\{([^{}]+)\}'
    
    # Special handling for problematic fields
    client_data = project_data.get('client', {})
    
    # Ensure we have values for commonly problematic fields
    from datetime import datetime
    special_fields = {
        'case_name': client_data.get('case_name', 'Estate Appraisal'),
        'inspection_date': _format_date(project_data.get('inspection_date', '')),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'client_name': client_data.get('name', 'Client'),
        'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        'death_date': _format_date(client_data.get('date_of_death', '')),
        'project_name': project_data.get('project_name', 'Appraisal Project')
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
    import re
    pattern = r'\{([^{}]+)\}'
    
    # Special handling for problematic fields
    client_data = project_data.get('client', {})
    
    # Ensure we have values for commonly problematic fields
    from datetime import datetime
    special_fields = {
        'case_name': client_data.get('case_name', 'Estate Appraisal'),
        'inspection_date': _format_date(project_data.get('inspection_date', '')),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'client_name': client_data.get('name', 'Client'),
        'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        'death_date': _format_date(client_data.get('date_of_death', '')),
        'project_name': project_data.get('project_name', 'Appraisal Project')
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
                
                # Special handling for the entire paragraph
                # This is a more aggressive approach that replaces the entire paragraph text
                # It may lose some formatting but ensures placeholders are replaced
                if paragraph.runs:
                    # Put all text in the first run
                    paragraph.runs[0].text = full_text
                    
                    # Clear all other runs
                    for i in range(1, len(paragraph.runs)):
                        paragraph.runs[i].text = ''
    
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
                            
                            # Special handling for the entire paragraph
                            if paragraph.runs:
                                paragraph.runs[0].text = full_text
                                for i in range(1, len(paragraph.runs)):
                                    paragraph.runs[i].text = ''
    
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
        from datetime import datetime
        special_fields = {
            'case_name': client_data.get('case_name', 'Estate Appraisal'),
            'inspection_date': _format_date(project_data.get('inspection_date', '')),
            'current_date': datetime.now().strftime('%B %d, %Y'),
            'report_date': _format_date(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
            'client_name': client_data.get('name', 'Client'),
            'address': f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip(),
            'attorney_name': client_data.get('attorney_name', ''),
            'attorney_phone': client_data.get('attorney_phone', ''),
            'attorney_email': client_data.get('attorney_email', ''),
            'death_date': _format_date(client_data.get('date_of_death', '')),
            'project_name': project_data.get('project_name', 'Appraisal Project')
        }
        
        # Access the document's XML directly to find text boxes
        import re
        pattern = r'\{([^{}]+)\}'
        
        # Get the main document part
        document_part = doc.part
        
        # Find all shape elements (which include text boxes)
        shape_elements = []
        
        # Look for shape elements in the document XML - multiple possible structures
        xpath_patterns = [
            './/w:drawing//wp:inline//a:graphic//a:graphicData//wps:txbx//w:p',  # Standard inline text boxes
            './/w:drawing//wp:anchor//a:graphic//a:graphicData//wps:txbx//w:p',   # Anchored text boxes
            './/mc:AlternateContent//w:drawing//wp:anchor//a:graphic//a:graphicData//wps:txbx//w:p',  # Alternate content
            './/w:pict//v:shape//v:textbox//w:p',  # VML text boxes (older format)
            './/w:drawing//wp:inline//a:graphic//a:graphicData//v:shape//v:textbox//w:p',  # Mixed format
            './/w:drawing//wp:anchor//a:graphic//a:graphicData//v:shape//v:textbox//w:p',  # Mixed format anchored
        ]
        
        # Try each XPath pattern
        for xpath_pattern in xpath_patterns:
            try:
                elements = document_part.element.xpath(xpath_pattern)
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
            frame_elements = document_part.element.xpath('.//w:txbxContent//w:p')
            logger.info(f"Found {len(frame_elements)} text frame paragraphs")
            shape_elements.extend(frame_elements)
        except Exception as e:
            logger.warning(f"Error finding text frames: {str(e)}")
            
        # Try a direct XML approach for text boxes
        try:
            # Find all text elements that might contain placeholders
            text_elements = document_part.element.xpath('.//w:t')
            logger.info(f"Found {len(text_elements)} text elements to check for placeholders")
            
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
                            modified_text = modified_text.replace(placeholder, str(value))
                        
                        # Update the text element directly
                        text_element.text = modified_text
        except Exception as e:
            logger.warning(f"Error with direct XML approach: {str(e)}")
        
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
    from datetime import datetime
    
    client_data = project_data.get('client', {})
    appraisal_items = project_data.get('appraisal_items', [])
    
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
        'case_name': client_data.get('case_name', 'Estate Appraisal'),
        
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

def _add_watermark(doc: Document):
    """Add DRAFT watermark to document as a true background watermark"""
    try:
        logger.info("Adding true background DRAFT watermark to document")
        
        # Create a true watermark using a simpler approach
        try:
            for section_idx, section in enumerate(doc.sections):
                # Get the header part
                header_part = section.header
                
                # Create a paragraph for the watermark
                watermark_p = header_part.add_paragraph()
                watermark_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
                # Add a run with the watermark text
                run = watermark_p.add_run("DRAFT")
                run.font.size = Pt(120)  # Very large font
                run.font.bold = True
                run.font.color.rgb = RGBColor(192, 192, 192)  # Light gray
                
                # Try to position it behind text using Word's XML
                try:
                    # Get the paragraph element
                    p_element = watermark_p._p
                    
                    # Add paragraph properties
                    pPr = p_element.get_or_add_pPr()
                    
                    # Create frame properties for positioning
                    framePr = OxmlElement('w:framePr')
                    framePr.set(qn('w:wrap'), 'through')  # Text wraps through the frame
                    framePr.set(qn('w:vAnchor'), 'page')  # Anchor to page
                    framePr.set(qn('w:hAnchor'), 'page')  # Anchor to page
                    framePr.set(qn('w:yAlign'), 'center')  # Center vertically
                    framePr.set(qn('w:xAlign'), 'center')  # Center horizontally
                    pPr.append(framePr)
                    
                    # Set text wrapping
                    textWrapping = OxmlElement('w:textWrapping')
                    textWrapping.set(qn('w:val'), 'around')  # Text wraps around
                    pPr.append(textWrapping)
                    
                    # Try to set z-order to be behind text
                    try:
                        # Add a custom style for the paragraph
                        style = OxmlElement('w:pStyle')
                        style.set(qn('w:val'), 'Watermark')
                        pPr.append(style)
                        
                        # Add a vanish property to make it appear behind text
                        rPr = OxmlElement('w:rPr')
                        vanish = OxmlElement('w:vanish')
                        rPr.append(vanish)
                        p_element.append(rPr)
                    except Exception as style_error:
                        logger.warning(f"Could not set watermark style: {str(style_error)}")
                    
                    logger.info(f"Added positioned watermark to section {section_idx+1}")
                except Exception as pos_error:
                    logger.warning(f"Could not position watermark: {str(pos_error)}")
            
            logger.info("Successfully added watermarks")
            return True
        except Exception as watermark_error:
            logger.error(f"Main watermark approach failed: {str(watermark_error)}")

        
        # Fallback to the drawing approach
        logger.info("Falling back to drawing approach")
        
        # Use Word's drawing canvas to create a true watermark
        for section_idx, section in enumerate(doc.sections):
            logger.info(f"Processing section {section_idx+1} of {len(doc.sections)}")

            
            # Get the header part for this section (create if needed)
            header_part = section.header
            
            # Create a new paragraph for the watermark
            watermark_p = header_part.add_paragraph()
            
            # Create the watermark drawing using Word's XML directly
            # This creates a true watermark that appears behind text
            try:
                # Create the VML object with proper namespace declarations
                r = watermark_p._p.add_r()
                drawing = OxmlElement('w:drawing')
                r.append(drawing)
                
                # Create the main drawing container
                inline = OxmlElement('wp:inline')
                drawing.append(inline)
                
                # Set size and position
                extent = OxmlElement('wp:extent')
                extent.set('cx', '7772400')  # Width in EMUs (7.5 inches)
                extent.set('cy', '7772400')  # Height in EMUs (7.5 inches)
                inline.append(extent)
                
                # Set effect extent (padding)
                effectExtent = OxmlElement('wp:effectExtent')
                effectExtent.set('l', '0')
                effectExtent.set('t', '0')
                effectExtent.set('r', '0')
                effectExtent.set('b', '0')
                inline.append(effectExtent)
                
                # Create the docPr element (drawing properties)
                docPr = OxmlElement('wp:docPr')
                docPr.set('id', f'{1000 + section_idx}')
                docPr.set('name', f'Watermark {section_idx}')
                inline.append(docPr)
                
                # Create the graphic element
                graphic = OxmlElement('a:graphic')
                graphic.set('xmlns:a', 'http://schemas.openxmlformats.org/drawingml/2006/main')
                inline.append(graphic)
                
                # Create the graphic data element
                graphicData = OxmlElement('a:graphicData')
                graphicData.set('uri', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape')
                graphic.append(graphicData)
                
                # Create the WordProcessingShape element
                wps_shape = OxmlElement('wps:wsp')
                wps_shape.set('xmlns:wps', 'http://schemas.microsoft.com/office/word/2010/wordprocessingShape')
                graphicData.append(wps_shape)
                
                # Create the shape properties
                wps_shape_props = OxmlElement('wps:cNvSpPr')
                wps_shape_props.set('txBox', '1')
                wps_shape.append(wps_shape_props)
                
                # Create the shape properties
                spPr = OxmlElement('wps:spPr')
                wps_shape.append(spPr)
                
                # Create a transform element for rotation
                xfrm = OxmlElement('a:xfrm')
                xfrm.set('rot', '2700000')  # 270 degrees (in 60,000ths of a degree)
                spPr.append(xfrm)
                
                # Create the text body
                txbx = OxmlElement('wps:txbx')
                wps_shape.append(txbx)
                
                # Add the text box content
                txbxContent = OxmlElement('w:txbxContent')
                txbx.append(txbxContent)
                
                # Add a paragraph with the watermark text
                p = OxmlElement('w:p')
                txbxContent.append(p)
                
                # Add paragraph properties
                pPr = OxmlElement('w:pPr')
                p.append(pPr)
                
                # Center align the text
                jc = OxmlElement('w:jc')
                jc.set(qn('w:val'), 'center')
                pPr.append(jc)
                
                # Add a run with the watermark text
                r = OxmlElement('w:r')
                p.append(r)
                
                # Add run properties
                rPr = OxmlElement('w:rPr')
                r.append(rPr)
                
                # Set font size (72 point)
                sz = OxmlElement('w:sz')
                sz.set(qn('w:val'), '144')  # 144 half-points = 72 points
                rPr.append(sz)
                
                # Set font color to light gray
                color = OxmlElement('w:color')
                color.set(qn('w:val'), 'C0C0C0')  # Light gray
                rPr.append(color)
                
                # Make it bold
                b = OxmlElement('w:b')
                rPr.append(b)
                
                # Make it italic
                i = OxmlElement('w:i')
                rPr.append(i)
                
                # Add the text
                t = OxmlElement('w:t')
                r.append(t)
                t.text = 'DRAFT'
                
                # Set body properties for the shape
                bodyPr = OxmlElement('wps:bodyPr')
                bodyPr.set('rot', '0')
                bodyPr.set('vert', 'horz')
                wps_shape.append(bodyPr)
                
                # Set the shape to be semi-transparent
                wps_style = OxmlElement('wps:style')
                wps_shape.append(wps_style)
                
                # Add fill properties to make it semi-transparent
                fill_props = OxmlElement('a:fillStyleLst')
                wps_style.append(fill_props)
                
                logger.info(f"Added true background watermark to section {section_idx+1}")
            except Exception as drawing_error:
                logger.error(f"Error creating drawing watermark: {str(drawing_error)}")
                
                # Fallback to simpler method if the drawing approach fails
                try:
                    # Create a simple watermark paragraph
                    p = header_part.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    
                    # Add the watermark text
                    run = p.add_run("DRAFT")
                    run.font.size = Pt(120)  # Very large font
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(192, 192, 192)  # Light gray
                    
                    # Try to position it behind text using Word's XML
                    p_element = p._p
                    pPr = p_element.get_or_add_pPr()
                    
                    # Set the paragraph to be positioned
                    framePr = OxmlElement('w:framePr')
                    framePr.set(qn('w:wrap'), 'through')  # Text wraps through
                    framePr.set(qn('w:vAnchor'), 'page')  # Anchor to page
                    framePr.set(qn('w:hAnchor'), 'page')  # Anchor to page
                    framePr.set(qn('w:yAlign'), 'center')  # Center vertically
                    framePr.set(qn('w:xAlign'), 'center')  # Center horizontally
                    pPr.append(framePr)
                    
                    # Set z-order to be behind text
                    behindText = OxmlElement('w:rPr')
                    vanish = OxmlElement('w:vanish')
                    behindText.append(vanish)
                    p_element.append(behindText)
                    
                    logger.info(f"Added fallback watermark to section {section_idx+1}")
                except Exception as fallback_error:
                    logger.error(f"Fallback watermark also failed: {str(fallback_error)}")
        
        logger.info("Watermark addition completed successfully")
        
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        # Last resort fallback
        try:
            # Just add DRAFT to each header
            for section in doc.sections:
                if section.header:
                    p = section.header.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run("DRAFT")
                    run.font.bold = True
                    run.font.size = Pt(72)
                    run.font.color.rgb = RGBColor(192, 192, 192)  # Light gray
            logger.info("Added last resort watermark")
        except Exception as e2:
            logger.error(f"All watermark attempts failed: {str(e2)}")



def _remove_existing_watermarks(doc: Document):
    """Remove any existing watermarks from the document"""
    try:
        # First, remove VML background watermarks (center of page watermarks)
        for section in doc.sections:
            try:
                sectPr = section._sectPr
                
                # Find and remove any v:background elements (VML watermarks)
                for child in list(sectPr):
                    if child.tag.endswith('background'):
                        sectPr.remove(child)
                        logger.info("Removed VML background watermark")
            except Exception as vml_error:
                logger.warning(f"Error removing VML watermarks: {str(vml_error)}")
        
        # Remove watermarks from headers and footers
        for section in doc.sections:
            # Remove watermarks from header
            if section.header:
                _remove_watermarks_from_header_footer(section.header)
            
            # Remove watermarks from footer
            if section.footer:
                _remove_watermarks_from_header_footer(section.footer)
        
        # Remove any watermarks from the document body
        paragraphs_to_remove = []
        for i, paragraph in enumerate(doc.paragraphs):
            # Check if this is a standalone DRAFT watermark paragraph
            if paragraph.text.strip().upper() == 'DRAFT':
                # Check if it has watermark characteristics (centered, large font)
                if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
                    paragraphs_to_remove.append(paragraph)
                    logger.info(f"Found body watermark paragraph at index {i}")
            
            # Also check for runs with DRAFT text that might be watermarks
            for run in paragraph.runs:
                if run.text and 'DRAFT' in run.text.upper():
                    # Check if this looks like a watermark (gray, bold, large)
                    is_watermark = False
                    
                    # Check for gray color
                    if run.font.color and run.font.color.rgb:
                        rgb = run.font.color.rgb
                        if rgb.red == rgb.green == rgb.blue and rgb.red > 128:
                            is_watermark = True
                    
                    # Check for large size
                    if run.font.size and run.font.size > Pt(30):
                        is_watermark = True
                    
                    if is_watermark:
                        run.text = run.text.replace('DRAFT', '')
                        logger.info(f"Cleared DRAFT watermark text from paragraph {i}")
        
        # Remove watermark paragraphs from body
        for paragraph in paragraphs_to_remove:
            try:
                paragraph._element.getparent().remove(paragraph._element)
                logger.info("Removed body watermark paragraph")
            except Exception as e:
                logger.warning(f"Could not remove body watermark paragraph: {str(e)}")
        
        logger.info("Successfully removed existing watermarks from template")
        
    except Exception as e:
        logger.warning(f"Could not remove existing watermarks: {str(e)}")

def _remove_watermarks_from_header_footer(header_footer):
    """Remove watermarks from header or footer"""
    try:
        # Look for VML watermarks (our new implementation)
        try:
            # Find paragraphs with VML elements
            for paragraph in list(header_footer.paragraphs):
                # Check for w:pict elements
                try:
                    p_element = paragraph._p
                    pict_elements = p_element.xpath('.//w:pict')
                    
                    if pict_elements:
                        for pict in pict_elements:
                            # Check for v:shape elements that might be watermarks
                            shape_elements = pict.xpath('./v:shape')
                            for shape in shape_elements:
                                # Check if this is a watermark shape
                                if shape.get('id', '').startswith('Watermark'):
                                    # Remove the entire paragraph
                                    paragraph._element.getparent().remove(paragraph._element)
                                    logger.info("Removed VML watermark paragraph")
                                    break
                except Exception as e:
                    logger.warning(f"Error checking for VML elements: {str(e)}")
        except Exception as vml_error:
            logger.warning(f"Error checking for VML watermarks: {str(vml_error)}")
        
        # Remove any "DRAFT" text that might be watermarks
        paragraphs_to_remove = []
        
        for paragraph in header_footer.paragraphs:
            paragraph_text = paragraph.text.strip()
            
            # Check if this paragraph contains only watermark text
            if paragraph_text.upper() == 'DRAFT':
                paragraphs_to_remove.append(paragraph)
                logger.info("Found DRAFT watermark paragraph to remove")
            else:
                # Check individual runs for watermark characteristics
                runs_to_clear = []
                for run in paragraph.runs:
                    if run.text and 'DRAFT' in run.text.upper():
                        # Check if this looks like a watermark (gray, bold, or large)
                        is_watermark = False
                        
                        # Check for gray color
                        if run.font.color and run.font.color.rgb:
                            # Check for any gray shade
                            rgb = run.font.color.rgb
                            if rgb.red == rgb.green == rgb.blue and rgb.red > 128:
                                is_watermark = True
                        
                        # Check for bold formatting
                        if run.font.bold:
                            is_watermark = True
                        
                        # Check for italic formatting
                        if run.font.italic:
                            is_watermark = True
                        
                        # Check for large size
                        if run.font.size and run.font.size > Pt(30):  # Larger threshold
                            is_watermark = True
                        
                        if is_watermark:
                            runs_to_clear.append(run)
                            logger.info("Found DRAFT watermark run to clear")
                
                # Clear watermark runs
                for run in runs_to_clear:
                    run.text = ''
        
        # Remove watermark paragraphs
        for paragraph in paragraphs_to_remove:
            try:
                paragraph._element.getparent().remove(paragraph._element)
                logger.info("Removed DRAFT watermark paragraph")
            except Exception as e:
                logger.warning(f"Could not remove watermark paragraph: {str(e)}")
        
        # Also check for paragraphs with positioning that might be watermarks
        for paragraph in header_footer.paragraphs:
            try:
                p_element = paragraph._p
                pPr = p_element.get_or_add_pPr()
                
                # Check if this paragraph has frame properties (positioned)
                frame_props = pPr.xpath('./w:framePr')
                if frame_props and 'DRAFT' in paragraph.text.upper():
                    paragraph._element.getparent().remove(paragraph._element)
                    logger.info("Removed positioned DRAFT watermark paragraph")
            except Exception as e:
                logger.warning(f"Error checking for positioned watermark: {str(e)}")
        
    except Exception as e:
        logger.warning(f"Could not remove watermarks from header/footer: {str(e)}")


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