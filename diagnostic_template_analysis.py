#!/usr/bin/env python3
"""
Diagnostic script to analyze template field extraction and replacement
WITHOUT modifying any existing code
"""

import sys
import os
import json
import re
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from docx import Document
from app.utils.template_converter import (
    extract_field_mappings, 
    _extract_fields_from_text,
    _replace_fields_in_paragraph,
    _handle_appraisal_items,
    _get_field_value,
    FIELD_PATTERNS
)

def find_template_file():
    """Find the Estate Template file"""
    current_dir = os.path.dirname(__file__)
    possible_paths = [
        os.path.join(current_dir, "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"),
        os.path.join(current_dir, "..", "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"),
        os.path.join(current_dir, "templates", "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"),
        os.path.join(current_dir, "templates", "original", "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"),
        "Estate Template Jewelry Appraisal-FORM-FINAL (1).docx"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None

def analyze_template():
    """Run diagnostic analysis on the template"""
    
    # Sample project data
    project_data = {
        "client": {
            "name": "Test Client",
            "attorney_name": "Test Law",
            "address": "xyz abc ny 10001",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "date_of_death": "2025-09-16"
        },
        "inspection_date": "2025-09-17",
        "report_date": "2025-09-18",
        "total_value": 109.00,
        "appraisal_items": [
            {
                "description": "Gold Ring - 18K",
                "appraised_value": 109.00,
                "photo_path": "/absolute/path/to/existing/photo1.jpg"
            },
            {
                "description": "Silver Necklace",
                "appraised_value": 59.50,
                "photo_path": "/absolute/path/to/existing/photo2.jpg"
            }
        ],
        "field_mappings": {}
    }
    
    # Find template file
    template_path = find_template_file()
    if not template_path:
        return {
            "error": "Estate Template Jewelry Appraisal-FORM-FINAL.docx not found",
            "searched_paths": [
                "Current directory",
                "Parent directory", 
                "templates/ subdirectory",
                "templates/original/ subdirectory"
            ]
        }
    
    try:
        doc = Document(template_path)
    except Exception as e:
        return {
            "error": f"Failed to load template: {str(e)}",
            "template_path": template_path
        }
    
    diagnostic_report = {
        "template_path": template_path,
        "extracted_placeholders": [],
        "field_mappings": {},
        "pattern_matches": {},
        "items_handling": {},
        "replacement_status": {},
        "unreplaced_placeholders": []
    }
    
    # 1. Extract field mappings and raw placeholders
    print("🔍 Extracting field mappings...")
    
    # Track raw extractions
    raw_extractions = []
    
    # Scan paragraphs
    for i, paragraph in enumerate(doc.paragraphs):
        if paragraph.text.strip():
            fields = _extract_fields_from_text(paragraph.text)
            for field_name, pattern_type in fields:
                raw_extractions.append({
                    "field_name": field_name,
                    "pattern_type": pattern_type,
                    "source_type": "paragraph",
                    "source_index": i,
                    "source_text": paragraph.text,
                    "exact_match": _find_exact_match(paragraph.text, field_name, pattern_type)
                })
    
    # Scan tables
    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para_idx, paragraph in enumerate(cell.paragraphs):
                    if paragraph.text.strip():
                        fields = _extract_fields_from_text(paragraph.text)
                        for field_name, pattern_type in fields:
                            raw_extractions.append({
                                "field_name": field_name,
                                "pattern_type": pattern_type,
                                "source_type": "table_cell",
                                "source_location": f"table_{table_idx}_row_{row_idx}_cell_{cell_idx}_para_{para_idx}",
                                "source_text": paragraph.text,
                                "exact_match": _find_exact_match(paragraph.text, field_name, pattern_type)
                            })
    
    diagnostic_report["extracted_placeholders"] = raw_extractions
    
    # Get field mappings
    field_mappings = extract_field_mappings(doc)
    diagnostic_report["field_mappings"] = field_mappings
    
    # 2. Analyze pattern matches
    print("🔍 Analyzing pattern matches...")
    pattern_matches = {}
    
    for field_name in field_mappings.keys():
        patterns = [
            f"{{{{{field_name}}}}}",
            f"[{field_name}]", 
            f"{field_name}:"
        ]
        
        pattern_matches[field_name] = {
            "patterns": patterns,
            "matches": []
        }
        
        # Test patterns against sample paragraphs
        sample_paragraphs = []
        for i, paragraph in enumerate(doc.paragraphs[:10]):  # First 10 paragraphs
            if paragraph.text.strip():
                sample_paragraphs.append({
                    "index": i,
                    "original_text": paragraph.text,
                    "pattern_results": {}
                })
                
                for pattern in patterns:
                    matches = pattern in paragraph.text
                    if matches:
                        # Simulate replacement
                        value = _get_field_value(field_name, field_mappings[field_name], project_data)
                        replaced_text = paragraph.text.replace(pattern, str(value))
                        sample_paragraphs[-1]["pattern_results"][pattern] = {
                            "matches": True,
                            "replaced_text": replaced_text
                        }
                    else:
                        sample_paragraphs[-1]["pattern_results"][pattern] = {
                            "matches": False,
                            "replaced_text": paragraph.text
                        }
        
        pattern_matches[field_name]["sample_matches"] = sample_paragraphs
    
    diagnostic_report["pattern_matches"] = pattern_matches
    
    # 3. Analyze appraisal items handling
    print("🔍 Analyzing appraisal items handling...")
    
    # Find Item 1 paragraph
    item1_found = False
    item1_info = None
    
    for i, paragraph in enumerate(doc.paragraphs):
        if 'item 1' in paragraph.text.lower():
            item1_found = True
            item1_info = {
                "found": True,
                "paragraph_index": i,
                "paragraph_text": paragraph.text
            }
            break
    
    if not item1_found:
        item1_info = {"found": False, "message": "Item 1 not found"}
    
    # Simulate items handling (without actually modifying doc)
    items_handling = {
        "item1_paragraph": item1_info,
        "would_add_paragraphs": [],
        "would_insert_images": [],
        "market_value_replacements": []
    }
    
    # Simulate adding items
    if item1_found and project_data["appraisal_items"]:
        # First item replaces existing
        first_item = project_data["appraisal_items"][0]
        items_handling["item1_replacement"] = {
            "original_text": item1_info["paragraph_text"],
            "new_text": f"Item 1: {first_item['description']}"
        }
        
        # Additional items would be added
        for i, item in enumerate(project_data["appraisal_items"][1:], 2):
            items_handling["would_add_paragraphs"].append({
                "item_number": i,
                "text": f"Item {i}: {item['description']}",
                "would_append_at_end": True
            })
            
            # Check if image would be inserted
            photo_exists = os.path.exists(item["photo_path"]) if item.get("photo_path") else False
            items_handling["would_insert_images"].append({
                "item_number": i,
                "photo_path": item.get("photo_path"),
                "photo_exists": photo_exists,
                "would_insert": photo_exists,
                "insert_location": "after_item_paragraph"
            })
    
    # Check market value replacements in tables
    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                for para_idx, paragraph in enumerate(cell.paragraphs):
                    if '{market_value}' in paragraph.text:
                        first_item_value = project_data["appraisal_items"][0]["appraised_value"] if project_data["appraisal_items"] else 0
                        items_handling["market_value_replacements"].append({
                            "location": f"table_{table_idx}_row_{row_idx}_cell_{cell_idx}_para_{para_idx}",
                            "original_text": paragraph.text,
                            "replacement_value": f"${first_item_value:.2f}",
                            "new_text": paragraph.text.replace('{market_value}', f"${first_item_value:.2f}")
                        })
    
    diagnostic_report["items_handling"] = items_handling
    
    # 4. Replacement status analysis
    print("🔍 Analyzing replacement status...")
    
    # Find all placeholders in original document
    all_placeholders = set()
    placeholder_locations = {}
    
    # Estate-specific placeholders
    estate_patterns = [
        '{client_name}', '{current_date}', '{inspection_date}', 
        '{address}', '{death_date}', '{total_value}', '{market_value}'
    ]
    
    for pattern in estate_patterns:
        for i, paragraph in enumerate(doc.paragraphs):
            if pattern in paragraph.text:
                all_placeholders.add(pattern)
                if pattern not in placeholder_locations:
                    placeholder_locations[pattern] = []
                placeholder_locations[pattern].append({
                    "type": "paragraph",
                    "index": i,
                    "text": paragraph.text
                })
        
        # Check tables
        for table_idx, table in enumerate(doc.tables):
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    for para_idx, paragraph in enumerate(cell.paragraphs):
                        if pattern in paragraph.text:
                            all_placeholders.add(pattern)
                            if pattern not in placeholder_locations:
                                placeholder_locations[pattern] = []
                            placeholder_locations[pattern].append({
                                "type": "table_cell",
                                "location": f"table_{table_idx}_row_{row_idx}_cell_{cell_idx}_para_{para_idx}",
                                "text": paragraph.text
                            })
    
    # Check field mapping patterns
    for field_name in field_mappings.keys():
        patterns = [f"{{{{{field_name}}}}}", f"[{field_name}]", f"{field_name}:"]
        for pattern in patterns:
            for i, paragraph in enumerate(doc.paragraphs):
                if pattern in paragraph.text:
                    all_placeholders.add(pattern)
                    if pattern not in placeholder_locations:
                        placeholder_locations[pattern] = []
                    placeholder_locations[pattern].append({
                        "type": "paragraph", 
                        "index": i,
                        "text": paragraph.text
                    })
    
    # Analyze replacement status
    replacement_status = {}
    
    for placeholder in all_placeholders:
        status = {
            "placeholder": placeholder,
            "locations": placeholder_locations.get(placeholder, []),
            "replaced": False,
            "replacement_value": None,
            "failure_reason": None
        }
        
        # Determine if it would be replaced
        if placeholder in ['{client_name}', '{current_date}', '{inspection_date}', '{address}', '{death_date}', '{total_value}']:
            # Estate fields
            status["replaced"] = True
            if placeholder == '{client_name}':
                status["replacement_value"] = project_data["client"]["name"]
            elif placeholder == '{current_date}':
                status["replacement_value"] = datetime.now().strftime('%B %d, %Y')
            elif placeholder == '{inspection_date}':
                status["replacement_value"] = str(project_data["inspection_date"])
            elif placeholder == '{address}':
                client_data = project_data["client"]
                status["replacement_value"] = f"{client_data['address']} {client_data['city']} {client_data['state']} {client_data['zip_code']}".strip()
            elif placeholder == '{death_date}':
                status["replacement_value"] = str(project_data["client"]["date_of_death"])
            elif placeholder == '{total_value}':
                status["replacement_value"] = f"${project_data['total_value']}"
        elif placeholder == '{market_value}':
            if project_data["appraisal_items"]:
                status["replaced"] = True
                status["replacement_value"] = f"${project_data['appraisal_items'][0]['appraised_value']:.2f}"
            else:
                status["failure_reason"] = "no_appraisal_items"
        else:
            # Check field mappings
            found_mapping = False
            for field_name in field_mappings.keys():
                if placeholder in [f"{{{{{field_name}}}}}", f"[{field_name}]", f"{field_name}:"]:
                    found_mapping = True
                    value = _get_field_value(field_name, field_mappings[field_name], project_data)
                    if value:
                        status["replaced"] = True
                        status["replacement_value"] = value
                    else:
                        status["failure_reason"] = "empty_value"
                    break
            
            if not found_mapping:
                status["failure_reason"] = "no_mapping_key"
        
        replacement_status[placeholder] = status
    
    diagnostic_report["replacement_status"] = replacement_status
    
    # 5. Find unreplaced placeholders
    unreplaced = []
    for placeholder, status in replacement_status.items():
        if not status["replaced"]:
            unreplaced.append({
                "placeholder": placeholder,
                "reason": status["failure_reason"],
                "locations": status["locations"]
            })
    
    diagnostic_report["unreplaced_placeholders"] = unreplaced
    
    return diagnostic_report

def _find_exact_match(text, field_name, pattern_type):
    """Find the exact text that matched the pattern"""
    for pattern, ptype in FIELD_PATTERNS:
        if ptype == pattern_type:
            matches = re.finditer(pattern, text)
            for match in matches:
                if pattern_type == 'curly_bracket' and match.group(1).strip() == field_name:
                    return match.group(0)
                elif pattern_type in ['label_colon_x', 'label_space_x'] and match.group(1).strip().rstrip(':') == field_name:
                    return match.group(0)
                elif pattern_type == 'square_bracket' and match.group(1).strip() == field_name:
                    return match.group(0)
    return None

def main():
    """Run the diagnostic analysis"""
    print("🚀 Starting Template Diagnostic Analysis...")
    
    try:
        report = analyze_template()
        
        # Output JSON report
        print("\n" + "="*80)
        print("DIAGNOSTIC REPORT (JSON)")
        print("="*80)
        print(json.dumps(report, indent=2, default=str))
        
        # Human summary
        print("\n" + "="*80)
        print("HUMAN SUMMARY")
        print("="*80)
        
        if "error" in report:
            print(f"❌ Error: {report['error']}")
            return
        
        summary_points = []
        
        # Check template loading
        if report.get("template_path"):
            summary_points.append(f"✅ Template loaded successfully from: {report['template_path']}")
        
        # Check field extraction
        extracted_count = len(report.get("extracted_placeholders", []))
        mapping_count = len(report.get("field_mappings", {}))
        summary_points.append(f"📊 Extracted {extracted_count} placeholders, created {mapping_count} field mappings")
        
        # Check Item 1 handling
        item1_status = report.get("items_handling", {}).get("item1_paragraph", {})
        if item1_status.get("found"):
            summary_points.append("✅ Found 'Item 1' paragraph for appraisal items processing")
        else:
            summary_points.append("❌ 'Item 1' paragraph not found - appraisal items won't be processed correctly")
        
        # Check replacement status
        unreplaced_count = len(report.get("unreplaced_placeholders", []))
        total_placeholders = len(report.get("replacement_status", {}))
        replaced_count = total_placeholders - unreplaced_count
        summary_points.append(f"🔄 Replacement status: {replaced_count}/{total_placeholders} placeholders would be replaced")
        
        # Check common failure reasons
        failure_reasons = {}
        for placeholder_info in report.get("unreplaced_placeholders", []):
            reason = placeholder_info.get("reason", "unknown")
            failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
        
        if failure_reasons:
            reason_text = ", ".join([f"{count} {reason}" for reason, count in failure_reasons.items()])
            summary_points.append(f"⚠️  Common failure reasons: {reason_text}")
        
        # Check image handling
        image_issues = 0
        for img_info in report.get("items_handling", {}).get("would_insert_images", []):
            if not img_info.get("photo_exists", False):
                image_issues += 1
        
        if image_issues > 0:
            summary_points.append(f"📷 Image issues: {image_issues} photos have invalid paths and won't be inserted")
        
        for point in summary_points:
            print(f"• {point}")
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()