"""
Template type detection utility
Detects template category from template name by extracting keywords
"""

from enum import Enum
from typing import Optional
import re

class TemplateCategory(str, Enum):
    """Template categories"""
    IMAGE_BASED = "image_based"  # artwork, auto, firearms, handbag, jewelery, watch
    COIN = "coin"
    CONTENT = "content"
    WINE = "wine"

# Template keywords to category mapping
# These keywords will be searched within longer template names
TEMPLATE_KEYWORDS = {
    # Image-based templates (all identical)
    "jewelry": TemplateCategory.IMAGE_BASED,
    "artwork": TemplateCategory.IMAGE_BASED,
    "art": TemplateCategory.IMAGE_BASED,
    "auto": TemplateCategory.IMAGE_BASED,
    "automobile": TemplateCategory.IMAGE_BASED,
    "firearms": TemplateCategory.IMAGE_BASED,
    "firearm": TemplateCategory.IMAGE_BASED,
    "handbag": TemplateCategory.IMAGE_BASED,
    "handbags": TemplateCategory.IMAGE_BASED,
    "watch": TemplateCategory.IMAGE_BASED,
    "watches": TemplateCategory.IMAGE_BASED,
    "collectibles": TemplateCategory.IMAGE_BASED,
    "collectible": TemplateCategory.IMAGE_BASED,
    
    # Table-based templates (each different)
    "coin": TemplateCategory.COIN,
    "coins": TemplateCategory.COIN,
    "content": TemplateCategory.CONTENT,
    "contents": TemplateCategory.CONTENT,
    "inventory": TemplateCategory.CONTENT,
    "wine": TemplateCategory.WINE,
    "wines": TemplateCategory.WINE,
}

def detect_template_category(template_name: str) -> TemplateCategory:
    """
    Detect template category from template name by extracting keywords
    
    Examples:
        "Divorce Template Wine Appraisal MSTEMPLATE-Doc" → WINE
        "Estate Template Coin Collection MSTEMPLATE" → COIN
        "Divorce Template Jewelry Appraisal-FORM-FINAL" → IMAGE_BASED
        "jewelry" → IMAGE_BASED
    
    Args:
        template_name: Name of the template (case-insensitive)
    
    Returns:
        TemplateCategory enum value
    """
    if not template_name:
        return TemplateCategory.IMAGE_BASED
    
    # Normalize name (lowercase, convert to words)
    normalized = template_name.lower().strip()
    
    # Remove common separators and split into words
    # This helps match "Wine" in "Divorce Template Wine Appraisal"
    words = re.split(r'[\s\-_]+', normalized)
    
    # First pass: Check for exact keyword matches in words
    for word in words:
        if word in TEMPLATE_KEYWORDS:
            return TEMPLATE_KEYWORDS[word]
    
    # Second pass: Check if any keyword is contained in the full name
    for keyword, category in TEMPLATE_KEYWORDS.items():
        if keyword in normalized:
            return category
    
    # Default to image-based (backward compatible)
    return TemplateCategory.IMAGE_BASED

def get_template_columns(category: TemplateCategory) -> dict:
    """
    Get column configuration for a template category
    
    Returns:
        Dictionary with column definitions
    """
    COLUMN_CONFIGS = {
        TemplateCategory.IMAGE_BASED: {
            "requires_images": True,
            "table_placeholder": "{appraisal_items_table}",
            "columns": [
                {"name": "room_area", "label": "Room/Area", "type": "text"},
                {"name": "floor_building", "label": "Floor/Building", "type": "text"},
                {"name": "description", "label": "Description", "type": "textarea"},
                {"name": "appraised_value", "label": "Appraised Value", "type": "decimal"}
            ]
        },
        
        TemplateCategory.COIN: {
            "requires_images": False,
            "table_placeholder": "{coin_collection_table}",
            "columns": [
                {"name": "quantity", "label": "Quantity", "type": "number", "required": True},
                {"name": "year", "label": "Year", "type": "text", "required": True},
                {"name": "coin", "label": "Coin", "type": "text", "required": True},
                {"name": "condition", "label": "Condition", "type": "select", "required": True,
                 "options": ["Poor", "Fair", "Good", "Very Good", "Fine", "Very Fine", 
                           "Extremely Fine", "About Uncirculated", "Uncirculated", "Brilliant Uncirculated"]},
                {"name": "appraised_price", "label": "Appraised Price", "type": "decimal", "required": True}
            ]
        },
        
        TemplateCategory.CONTENT: {
            "requires_images": False,
            "table_placeholder": "{content_inventory_table}",
            "columns": [
                {"name": "area", "label": "Area", "type": "text", "required": True,
                 "placeholder": "e.g., Living Room, Kitchen"},
                {"name": "fair_market_value", "label": "Fair Market Value (FMV)", "type": "decimal", "required": True}
            ]
        },
        
        TemplateCategory.WINE: {
            "requires_images": False,
            "table_placeholder": "{wine_collection_table}",
            "columns": [
                {"name": "quantity", "label": "Quantity", "type": "number", "required": True,
                 "help_text": "Number of bottles"},
                {"name": "bottle", "label": "Bottle", "type": "text", "required": True,
                 "placeholder": "e.g., 2015 Chateau Lafite Rothschild"},
                {"name": "per_bottle_price", "label": "Per Bottle Price", "type": "decimal", "required": True},
                {"name": "total_price", "label": "Total Price", "type": "decimal", "required": True,
                 "help_text": "Quantity × Per Bottle Price"}
            ]
        }
    }
    
    return COLUMN_CONFIGS.get(category, COLUMN_CONFIGS[TemplateCategory.IMAGE_BASED])

# Easy testing
if __name__ == "__main__":
    print("Testing template name detection:")
    print("=" * 80)
    
    test_names = [
        "Divorce Template Wine Appraisal MSTEMPLATE-Doc",
        "Estate Template Coin Collection MSTEMPLATE",
        "Divorce Template Jewelry Appraisal-FORM-FINAL",
        "Estate Template Content Inventory",
        "jewelry",
        "coin",
        "wine",
        "Divorce Template Artwork Appraisal",
        "Estate Template Auto Appraisal",
        "Divorce Template Firearms Appraisal",
        "Estate Template Handbag Appraisal",
        "Divorce Template Watch Appraisal",
        "Estate Template Collectibles Appraisal",
        "Divorce Template collectibles Appraisal",
        "unknown template name",
    ]
    
    for name in test_names:
        category = detect_template_category(name)
        columns = get_template_columns(category)
        print(f"{name:60} -> {category.value:15} ({len(columns['columns'])} cols)")
    
    print("=" * 80)
    print("✅ Detection logic working correctly!")

