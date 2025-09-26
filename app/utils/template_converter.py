import re
import os
from typing import Dict, List, Tuple
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import logging

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
                                field_mappings: Dict, project_data: Dict) -> str:
    """Generate report from template using project data"""
    try:
        doc = Document(template_path)
        
        # Replace text fields first
        for paragraph in doc.paragraphs:
            _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Handle appraisal items and images
        _handle_appraisal_items(doc, project_data)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise ReportGenerationError(f"Failed to generate report: {str(e)}")

def _replace_fields_in_paragraph(paragraph, field_mappings: Dict, project_data: Dict):
    """Replace field placeholders with actual data - only {field_name} format"""
    text = paragraph.text
    
    # Check if this is field mappings data (for template generation)
    field_mapping_data = project_data.get('field_mappings', {})
    
    # Replace all {field_name} patterns found in the document
    import re
    pattern = r'\{([^{}]+)\}'
    
    def replace_field(match):
        field_name = match.group(1).strip()
        
        # Get value from project data mapping
        value = _get_field_value_from_project(field_name, project_data)
        
        # Fallback to field mappings if no direct mapping found
        if value is None and field_name in field_mappings:
            if field_mapping_data:
                value = field_mapping_data.get(field_name, field_mappings[field_name].get('default_value', f'[{field_name}]'))
            else:
                value = _get_field_value(field_name, field_mappings[field_name], project_data)
        
        # Final fallback
        if value is None:
            value = f'[{field_name}]'
        
        return str(value) if value is not None else ''
    
    # Replace all {field_name} patterns
    text = re.sub(pattern, replace_field, text)
    paragraph.text = text

def _handle_appraisal_items(doc: Document, project_data: Dict):
    """Handle appraisal items and images insertion - simplified for {field_name} format"""
    try:
        appraisal_items = project_data.get('appraisal_items', [])
        if not appraisal_items:
            return
        
        # Find and process the template item section
        template_item_paragraph = None
        
        # Look for "Item 1" paragraph
        for paragraph in doc.paragraphs:
            if 'item 1' in paragraph.text.lower():
                template_item_paragraph = paragraph
                break
        
        if template_item_paragraph and appraisal_items:
            # Get the index of Item 1 paragraph
            item_paragraph_index = -1
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph == template_item_paragraph:
                    item_paragraph_index = i
                    break
            
            # Replace Item 1 text
            template_item_paragraph.text = f"Item 1"
            
            # Get parent and position for insertions
            parent = template_item_paragraph._element.getparent()
            item1_index = list(parent).index(template_item_paragraph._element)
            
            # Process all items
            current_index = item1_index
            
            for i, item in enumerate(appraisal_items, 1):
                if i > 1:
                    # Insert new item paragraph
                    current_index += 1
                    new_item_p = doc.add_paragraph(f"Item {i}")._element
                    parent.remove(new_item_p)
                    parent.insert(current_index, new_item_p)
                
                # Insert image if exists
                if item.get('photo_path') and os.path.exists(item['photo_path']):
                    current_index += 1
                    img_p = doc.add_paragraph()._element
                    parent.remove(img_p)
                    parent.insert(current_index, img_p)
                    
                    # Find and configure image paragraph
                    for p in doc.paragraphs:
                        if p._element == img_p:
                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = p.add_run()
                            run.add_picture(item['photo_path'], width=Inches(3), height=Inches(2))
                            break
                
                # Insert price paragraph
                current_index += 1
                price_p = doc.add_paragraph(f"${item.get('appraised_value', 0):.2f}")._element
                parent.remove(price_p)
                parent.insert(current_index, price_p)
        

        
    except Exception as e:
        logger.error(f"Error handling appraisal items: {str(e)}")





def _get_field_value_from_project(field_name: str, project_data: Dict) -> str:
    """Get field value from project data using comprehensive mapping"""
    from datetime import datetime
    
    client_data = project_data.get('client', {})
    appraisal_items = project_data.get('appraisal_items', [])
    
    # Build full address
    full_address = f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip()
    
    # Calculate gold price (sum of all jewelry items)
    gold_price = sum(
        item.get('appraised_value', 0) 
        for item in appraisal_items 
        if item.get('item_type') and item.get('item_type').lower() == 'jewelry'
    )
    
    # Comprehensive field mapping
    field_mappings = {
        # Basic project fields
        'client_name': client_data.get('name', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'inspection_date': str(project_data.get('inspection_date', '')),
        'report_date': str(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
        'address': full_address,
        'death_date': str(client_data.get('date_of_death', '')),
        'total_value': f"${project_data.get('total_value', '0.00')}",
        'gold_price': f"${gold_price:.2f}" if gold_price > 0 else '',
        'case_number': project_data.get('case_number', ''),
        'project_name': project_data.get('project_name', ''),
        
        # Client fields
        'client_address': full_address,
        'client_phone': client_data.get('phone', ''),
        'client_email': client_data.get('email', ''),
        'attorney_name': client_data.get('attorney_name', ''),
        'attorney_phone': client_data.get('attorney_phone', ''),
        'attorney_email': client_data.get('attorney_email', ''),
        
        # Appraisal summary fields
        'item_count': str(len(appraisal_items)),
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
    
    return field_mappings.get(field_name)

def _get_field_value(field_name: str, field_config: Dict, project_data: Dict) -> str:
    """Fallback field value getter for unmapped fields"""
    # Try project mapping first
    value = _get_field_value_from_project(field_name, project_data)
    if value is not None:
        return value
    
    # Fallback to field config default
    return field_config.get('default_value', f'[{field_name}]')