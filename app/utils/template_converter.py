import re
import os
from typing import Dict, List, Tuple
from docx import Document
import logging

logger = logging.getLogger(__name__)

class TemplateError(Exception):
    pass

class ConversionError(TemplateError):
    pass

class ReportGenerationError(TemplateError):
    pass

FIELD_PATTERNS = [
    (r'\{([^{}]+)\}', 'curly_bracket'),                    # {field_name}
    (r'([A-Za-z\s]{3,30}):\s*x{3,}', 'label_colon_x'),    # Label: xxxx
    (r'([A-Za-z\s]{3,30})\s+x{4,}', 'label_space_x'),     # Label xxxx
    (r'\[([A-Za-z\s]+)\]', 'square_bracket'),             # [Field Name]
    (r'_{5,}', 'underscore'),                             # _____ (5+ underscores)
    (r'RE:\s*x{3,}', 'RE_field'),                         # RE: xxxx
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
    """Extract all field mappings from document"""
    field_mappings = {}
    field_counter = 1
    
    # Add common appraisal fields with default values
    common_fields = {
        "Date": {"type": "date", "default": "[Current Date]"},
        "Client Name": {"type": "text", "default": "[Client Name]"},
        "Law Firm": {"type": "text", "default": "[Law Firm Name]"},
        "Client Address": {"type": "textarea", "default": "[Client Address]"},
        "Case Reference": {"type": "text", "default": "[Case Number]"},
        "Property Owner 1": {"type": "text", "default": "[Property Owner 1]"},
        "Property Owner 2": {"type": "text", "default": "[Property Owner 2]"},
        "Inspection Date": {"type": "date", "default": "[Inspection Date]"},
        "Report Date": {"type": "date", "default": "[Report Date]"},
        "Total Appraised Value": {"type": "currency", "default": "$0.00"},
        "Appraiser Name": {"type": "text", "default": "Andrew Kravit"},
        "Appraiser Credentials": {"type": "text", "default": "Certified Appraiser"}
    }
    
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
    
    # Always add common fields for appraisal templates
    for field_name, field_config in common_fields.items():
        if field_name not in field_mappings:
            field_mappings[field_name] = {
                "id": f"field_{field_counter}",
                "label": field_name,
                "type": field_config["type"],
                "required": field_name in ["Date", "Client Name", "Total Appraised Value"],
                "default_value": field_config["default"],
                "options": []
            }
            field_counter += 1
    
    return field_mappings

def _extract_fields_from_text(text: str) -> List[Tuple[str, str]]:
    """Extract field names from text using patterns"""
    fields = []
    
    for pattern, pattern_type in FIELD_PATTERNS:
        matches = re.finditer(pattern, text)
        for match in matches:
            if pattern_type == 'curly_bracket':
                field_name = match.group(1).strip()
            elif pattern_type in ['label_colon_x', 'label_space_x']:
                field_name = match.group(1).strip().rstrip(':')
                # Skip if it's too generic or contains common words
                skip_words = ['the', 'and', 'for', 'of', 'at', 'in', 'on', 'was', 'were', 'is', 'are', 'to', 'be', 'dear', 'sincerely', 'regards']
                if len(field_name) < 3 or any(word.lower() == field_name.lower() for word in skip_words):
                    continue
            elif pattern_type == 'square_bracket':
                field_name = match.group(1).strip()
            elif pattern_type == 'RE_field':
                field_name = "Case Reference"
            elif pattern_type == 'underscore':
                field_name = f"Field_{len(fields) + 1}"
            else:
                continue
                
            if field_name and len(field_name) > 2 and field_name not in [f[0] for f in fields]:
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
                                field_mappings: Dict, project_data: Dict) -> str:
    """Generate report from template using project data"""
    try:
        doc = Document(template_path)
        
        for paragraph in doc.paragraphs:
            _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise ReportGenerationError(f"Failed to generate report: {str(e)}")

def _replace_fields_in_paragraph(paragraph, field_mappings: Dict, project_data: Dict):
    """Replace field placeholders with actual data"""
    text = paragraph.text
    
    # Check if this is field mappings data (for template generation)
    field_mapping_data = project_data.get('field_mappings', {})
    
    # Replace field patterns
    for field_name, field_config in field_mappings.items():
        # Use field mapping data if available, otherwise project data
        if field_mapping_data:
            value = field_mapping_data.get(field_name, field_config.get('default_value', f'[{field_name}]'))
        else:
            value = _get_field_value(field_name, field_config, project_data)
        
        patterns = [
            f"{{{{{field_name}}}}}",
            f"[{field_name}]",
            f"{field_name}:"
        ]
        
        for pattern in patterns:
            if pattern in text:
                text = text.replace(pattern, str(value))
    
    # Replace common x patterns
    import re
    if field_mapping_data:
        # For template generation, use field mapping defaults
        if 'xxxxxxx' in text:
            text = text.replace('xxxxxxx', field_mapping_data.get('Case Reference', '[Case Reference]'))
        if 'xxxxxxxxxxxxxxxx' in text:
            text = text.replace('xxxxxxxxxxxxxxxx', field_mapping_data.get('Property Owner 1', '[Property Owner 1]'))
        if 'xxxxxxxxxxxxxxxxxxxxx' in text:
            text = text.replace('xxxxxxxxxxxxxxxxxxxxx', field_mapping_data.get('Property Owner 2', '[Property Owner 2]'))
    else:
        # For report generation, use project data
        if 'xxxxxxx' in text:
            case_ref = _get_field_value('Case Reference', {}, project_data)
            text = text.replace('xxxxxxx', case_ref if case_ref else 'Case Reference')
        if 'xxxxxxxxxxxxxxxx' in text:
            owner1 = _get_field_value('Property Owner 1', {}, project_data)
            text = text.replace('xxxxxxxxxxxxxxxx', owner1 if owner1 else 'Property Owner 1')
        if 'xxxxxxxxxxxxxxxxxxxxx' in text:
            owner2 = _get_field_value('Property Owner 2', {}, project_data)
            text = text.replace('xxxxxxxxxxxxxxxxxxxxx', owner2 if owner2 else 'Property Owner 2')
    
    paragraph.text = text

def _get_field_value(field_name: str, field_config: Dict, project_data: Dict) -> str:
    """Get field value from project data"""
    from datetime import datetime
    
    # Direct field name mappings
    field_mappings = {
        'Client Name': project_data.get('client', {}).get('name', ''),
        'Law Firm': project_data.get('client', {}).get('attorney_name', ''),
        'Client Address': project_data.get('client', {}).get('address', ''),
        'Case Reference': project_data.get('case_number', ''),
        'Property Owner 1': project_data.get('client', {}).get('name', ''),
        'Property Owner 2': '',
        'Inspection Date': str(project_data.get('inspection_date', '')),
        'Report Date': str(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'Date': datetime.now().strftime('%B %d, %Y'),
        'Total Appraised Value': f"${project_data.get('total_value', '0.00')}",
        'Appraiser Name': 'Andrew Kravit',
        'Appraiser Credentials': 'Certified Appraiser'
    }
    
    value = field_mappings.get(field_name, field_config.get('default_value', ''))
    return value if value else field_config.get('default_value', '')