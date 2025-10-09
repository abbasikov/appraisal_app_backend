import re
import os
from typing import Dict, List, Tuple
from docx import Document
from docx.shared import Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml.shared import OxmlElement, qn
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
                                field_mappings: Dict, project_data: Dict, 
                                add_watermark: bool = False) -> str:
    """Generate report from template using project data"""
    try:
        doc = Document(template_path)
        
        # Replace text fields in main document paragraphs
        for paragraph in doc.paragraphs:
            _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Replace text fields in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        _replace_fields_in_paragraph(paragraph, field_mappings, project_data)
        
        # Replace text fields in text boxes, shapes, and drawing objects
        # _replace_fields_in_shapes(doc, field_mappings, project_data)  # Disabled - not needed
        
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
        _handle_appraisal_items(doc, project_data)
        
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

def _replace_fields_in_paragraph(paragraph, field_mappings: Dict, project_data: Dict):
    """Replace field placeholders with actual data - only {field_name} format, preserving formatting"""
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
    
    # Process each run to preserve formatting
    for run in paragraph.runs:
        if run.text:
            # Replace all {field_name} patterns in this run
            new_text = re.sub(pattern, replace_field, run.text)
            if new_text != run.text:
                run.text = new_text

# Shape processing functions removed - not needed

def _handle_appraisal_items(doc: Document, project_data: Dict):
    """Handle appraisal items and images insertion with all project photos"""
    try:
        appraisal_items = project_data.get('appraisal_items', [])
        all_project_photos = project_data.get('all_project_photos', [])
        
        if not appraisal_items and not all_project_photos:
            return
        
        # Find and process the template item section
        template_item_paragraph = None
        
        # Look for "Item 1" paragraph
        for i, paragraph in enumerate(doc.paragraphs):
            if 'item 1' in paragraph.text.lower():
                template_item_paragraph = paragraph
                break
        
        if template_item_paragraph:
            # Get the index of Item 1 paragraph
            item_paragraph_index = -1
            for i, paragraph in enumerate(doc.paragraphs):
                if paragraph == template_item_paragraph:
                    item_paragraph_index = i
                    break
            
            # Get parent and position for insertions
            parent = template_item_paragraph._element.getparent()
            item1_index = list(parent).index(template_item_paragraph._element)
            
            # Add page break before images
            current_index = item1_index
            page_break_p = doc.add_paragraph()._element
            parent.remove(page_break_p)
            parent.insert(current_index, page_break_p)
            
            # Find and configure page break paragraph
            for p in doc.paragraphs:
                if p._element == page_break_p:
                    run = p.add_run()
                    run.add_break(WD_BREAK.PAGE)
                    break
            
            current_index += 1
            
            # Process all project photos as items
            
            # Use all project photos if available, otherwise use appraisal items
            items_to_process = all_project_photos if all_project_photos else appraisal_items
            
            for i, item in enumerate(items_to_process, 1):
                
                if i > 1:
                    # Insert new item paragraph
                    current_index += 1
                    new_item_p = doc.add_paragraph(f"Item {i}")._element
                    parent.remove(new_item_p)
                    parent.insert(current_index, new_item_p)
                
                # Insert image if exists (left-aligned)
                photo_path = item.get('file_path') if 'file_path' in item else item.get('photo_path')
                
                if photo_path and os.path.exists(photo_path):
                    # Try to insert image with comprehensive error handling
                    image_inserted = False
                    try:
                        # Validate image before inserting
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
                                    # Use 2x2 inch size as requested
                                    run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                                    image_inserted = True
                                    break
                            
                    except Exception as img_error:
                        logger.error(f"Failed to insert image {photo_path}: {str(img_error)}")
                        image_inserted = False
                    
                    # If image insertion failed, add placeholder
                    if not image_inserted:
                        current_index += 1
                        placeholder_p = doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}]")._element
                        parent.remove(placeholder_p)
                        parent.insert(current_index, placeholder_p)
                
                # Insert fair market value paragraph
                current_index += 1
                # Get appraised value from appraisal items if available, otherwise use 0
                appraised_value = 0
                if 'appraised_value' in item:
                    appraised_value = item.get('appraised_value', 0)
                elif appraisal_items and i <= len(appraisal_items):
                    appraised_value = appraisal_items[i-1].get('appraised_value', 0)
                
                price_p = doc.add_paragraph(f"Fair Market Value: ${appraised_value:.2f}")._element
                parent.remove(price_p)
                parent.insert(current_index, price_p)
            
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
                
                # Add image if exists
                photo_path = item.get('file_path') if 'file_path' in item else item.get('photo_path')
                if photo_path and os.path.exists(photo_path):
                    image_inserted = False
                    try:
                        if _is_valid_image(photo_path):
                            img_p = doc.add_paragraph()
                            img_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                            run = img_p.add_run()
                            run.add_picture(photo_path, width=Inches(2), height=Inches(2))
                            image_inserted = True
                    except Exception as img_error:
                        logger.error(f"Failed to insert image {photo_path}: {str(img_error)}")
                        image_inserted = False
                    
                    # Add placeholder if image insertion failed
                    if not image_inserted:
                        doc.add_paragraph(f"[Image: {os.path.basename(photo_path)}]")
                
                # Add fair market value
                appraised_value = 0
                if 'appraised_value' in item:
                    appraised_value = item.get('appraised_value', 0)
                elif appraisal_items and i <= len(appraisal_items):
                    appraised_value = appraisal_items[i-1].get('appraised_value', 0)
                
                doc.add_paragraph(f"Fair Market Value: ${appraised_value:.2f}")

        
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
    
    
    # Build full address
    full_address = f"{client_data.get('address', '')} {client_data.get('city', '')} {client_data.get('state', '')} {client_data.get('zip_code', '')}".strip()
    
    # Fixed metal prices
    gold_price = 115.65
    
    # Comprehensive field mapping
    field_mappings = {
        # Basic project fields
        'client_name': client_data.get('name', ''),
        'current_date': datetime.now().strftime('%B %d, %Y'),
        'inspection_date': str(project_data.get('inspection_date', '')),
        'report_date': str(project_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))),
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
        'case_name': client_data.get('case_name', '') or 'No Case Name',
        
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
    
    return field_mappings.get(field_name)

def _format_date(date_value) -> str:
    """Format date value for display in documents"""
    if not date_value:
        return ""
    
    try:
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
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_value, fmt)
                    return parsed_date.strftime('%B %d, %Y')  # September 01, 2025
                except ValueError:
                    continue
            
            # If no format worked, return the original string
            return date_value
        
        # If it's a datetime object
        elif hasattr(date_value, 'strftime'):
            return date_value.strftime('%B %d, %Y')
        
        # If it's a date object
        elif hasattr(date_value, 'strftime'):
            return date_value.strftime('%B %d, %Y')
        
        return str(date_value)
        
    except Exception as e:
        logger.warning(f"Error formatting date {date_value}: {str(e)}")
        return str(date_value) if date_value else ""

def _get_field_value(field_name: str, field_config: Dict, project_data: Dict) -> str:
    """Fallback field value getter for unmapped fields"""
    # Try project mapping first
    value = _get_field_value_from_project(field_name, project_data)
    if value is not None:
        return value
    
    # Fallback to field config default
    return field_config.get('default_value', f'[{field_name}]')

def _cleanup_content_between_images_and_summary(doc: Document, last_item_index: int):
    """Remove all content between the last item and the summary section"""
    try:
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
                # Remove paragraphs between last item and summary
                paragraphs_to_remove = []
                
                # Collect paragraphs to remove (in reverse order to avoid index issues)
                for i in range(summary_index - 1, last_item_index, -1):
                    if i < len(doc.paragraphs):
                        paragraphs_to_remove.append((i, doc.paragraphs[i]))
                
                # Remove paragraphs in reverse order
                for i, paragraph in paragraphs_to_remove:
                    try:
                        paragraph._element.getparent().remove(paragraph._element)
                    except Exception as e:
                        logger.warning(f"Could not remove paragraph {i}: {str(e)}")
            
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
    """Add DRAFT watermark to document"""
    try:
        logger.info("Adding watermark to document")
        # Add watermark to all sections
        for section in doc.sections:
            logger.info(f"Processing section, header exists: {section.header is not None}")
            if section.header:
                logger.info(f"Header has {len(section.header.paragraphs)} paragraphs")
                # Add a paragraph with DRAFT text
                p = section.header.add_paragraph()
                run = p.add_run("DRAFT")
                run.font.color.rgb = RGBColor(128, 128, 128)  # Gray
                run.font.size = Inches(0.5)
                run.font.italic = True
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                logger.info("Added DRAFT watermark to header")
            else:
                logger.info("No header found in section")
        
        logger.info("Watermark addition completed")
        
    except Exception as e:
        logger.error(f"Error adding watermark: {str(e)}")
        # Fallback: add watermark as text in header
        try:
            for section in doc.sections:
                if section.header:
                    # Add a paragraph with DRAFT text
                    p = section.header.paragraphs[0] if section.header.paragraphs else section.header.add_paragraph()
                    run = p.add_run("DRAFT")
                    run.font.color.rgb = RGBColor(128, 128, 128)  # Gray
                    run.font.size = Inches(0.5)
                    run.font.italic = True
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        except Exception as e2:
            logger.error(f"Fallback watermark also failed: {str(e2)}")

def _remove_existing_watermarks(doc: Document):
    """Remove any existing watermarks from the document"""
    try:
        # Remove watermarks from all sections
        for section in doc.sections:
            # Remove watermarks from header
            if section.header:
                _remove_watermarks_from_header_footer(section.header)
            
            # Remove watermarks from footer
            if section.footer:
                _remove_watermarks_from_header_footer(section.footer)
        
        logger.info("Successfully removed existing watermarks from template")
        
    except Exception as e:
        logger.warning(f"Could not remove existing watermarks: {str(e)}")

def _remove_watermarks_from_header_footer(header_footer):
    """Remove watermarks from header or footer"""
    try:
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
                        # Check if this looks like a watermark (gray, italic, or large)
                        is_watermark = False
                        
                        # Check for gray color
                        if run.font.color and run.font.color.rgb:
                            if run.font.color.rgb == RGBColor(128, 128, 128):
                                is_watermark = True
                        
                        # Check for italic formatting
                        if run.font.italic:
                            is_watermark = True
                        
                        # Check for large size
                        if run.font.size and run.font.size > Inches(0.3):
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
        
    except Exception as e:
        logger.warning(f"Could not remove watermarks from header/footer: {str(e)}")