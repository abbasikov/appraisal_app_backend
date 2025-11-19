"""
JSON Schema definitions for different appraisal item types
Provides validation for JSONB attributes without requiring separate database tables
"""

from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)

# ==================== JSON SCHEMAS ====================

COIN_SCHEMA = {
    "type": "object",
    "required": ["quantity", "year", "coin_name", "condition", "appraised_price"],
    "properties": {
        "quantity": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of coins"
        },
        "year": {
            "type": "string",
            "minLength": 1,
            "maxLength": 20,
            "description": "Year of minting"
        },
        "coin_name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500,
            "description": "Name of the coin"
        },
        "condition": {
            "type": "string",
            "enum": [
                "Poor", "Fair", "Good", "Very Good", "Fine", "Very Fine",
                "Extremely Fine", "About Uncirculated", "Uncirculated",
                "Brilliant Uncirculated"
            ]
        },
        "appraised_price": {
            "type": "number",
            "minimum": 0,
            "description": "Appraised price per coin"
        },
        "mint_mark": {"type": "string", "maxLength": 10},
        "grade": {"type": "string", "maxLength": 20},
        "certification": {"type": "string", "maxLength": 100},
        "notes": {"type": "string"}
    },
    "additionalProperties": False
}

WINE_SCHEMA = {
    "type": "object",
    "required": ["quantity", "bottle_description", "per_bottle_price", "total_price"],
    "properties": {
        "quantity": {
            "type": "integer",
            "minimum": 1,
            "description": "Number of bottles"
        },
        "bottle_description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 1000,
            "description": "Full description of the wine"
        },
        "per_bottle_price": {
            "type": "number",
            "minimum": 0,
            "description": "Price per bottle"
        },
        "total_price": {
            "type": "number",
            "minimum": 0,
            "description": "Total price (quantity × per_bottle_price)"
        },
        "vintage": {"type": "string", "maxLength": 20},
        "producer": {"type": "string", "maxLength": 200},
        "region": {"type": "string", "maxLength": 200},
        "varietal": {"type": "string", "maxLength": 100},
        "bottle_size": {"type": "string", "maxLength": 50},
        "notes": {"type": "string"}
    },
    "additionalProperties": False
}

CONTENT_SCHEMA = {
    "type": "object",
    "required": ["area", "fair_market_value"],
    "properties": {
        "area": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Area or room name"
        },
        "fair_market_value": {
            "type": "number",
            "minimum": 0,
            "description": "Fair market value of contents"
        },
        "description": {"type": "string"},
        "item_count": {"type": "integer", "minimum": 0},
        "condition": {"type": "string", "maxLength": 50},
        "notes": {"type": "string"}
    },
    "additionalProperties": False
}

IMAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "room_area": {"type": "string", "maxLength": 100},
        "floor_building": {"type": "string", "maxLength": 100},
        "description": {"type": "string"},
        "appraised_value": {"type": "number", "minimum": 0},
        "photo_path": {"type": "string"},
        "manufacturer": {"type": "string", "maxLength": 200},
        "model": {"type": "string", "maxLength": 200},
        "serial_number": {"type": "string", "maxLength": 100},
        "notes": {"type": "string"}
    },
    "additionalProperties": True  # Flexible for backward compatibility
}

# Schema registry - map item_type to schema
ITEM_SCHEMAS = {
    "coin": COIN_SCHEMA,
    "wine": WINE_SCHEMA,
    "content": CONTENT_SCHEMA,
    "jewellery": IMAGE_SCHEMA,
    "jewelry": IMAGE_SCHEMA,  # Alternative spelling
    "artwork": IMAGE_SCHEMA,
    "art": IMAGE_SCHEMA,
    "auto": IMAGE_SCHEMA,
    "automobile": IMAGE_SCHEMA,
    "firearms": IMAGE_SCHEMA,
    "firearm": IMAGE_SCHEMA,
    "handbag": IMAGE_SCHEMA,
    "handbags": IMAGE_SCHEMA,
    "watch": IMAGE_SCHEMA,
    "watches": IMAGE_SCHEMA
}


def get_schema_for_type(item_type: str) -> dict:
    """
    Get JSON schema for item type
    
    Args:
        item_type: Type of appraisal item (coin, wine, jewellery, etc.)
    
    Returns:
        JSON schema dictionary
    """
    item_type_lower = item_type.lower() if item_type else ""
    return ITEM_SCHEMAS.get(item_type_lower, IMAGE_SCHEMA)


def validate_appraisal_attributes(item_type: str, attributes: dict) -> tuple[bool, str]:
    """
    Validate appraisal item attributes against JSON schema
    
    Args:
        item_type: Type of appraisal item
        attributes: Dictionary of attributes to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not attributes:
        return True, ""  # Empty attributes are allowed
    
    schema = get_schema_for_type(item_type)
    
    try:
        validate(instance=attributes, schema=schema)
        
        # Additional validation for wine total_price
        if item_type.lower() == 'wine':
            quantity = attributes.get('quantity', 0)
            per_bottle = attributes.get('per_bottle_price', 0)
            total = attributes.get('total_price', 0)
            expected_total = quantity * per_bottle
            
            # Allow small rounding difference
            if abs(total - expected_total) > 0.01:
                return False, f"Total price ({total}) must equal quantity × per_bottle_price ({expected_total})"
        
        return True, ""
        
    except ValidationError as e:
        error_msg = f"Validation error in '{e.json_path}': {e.message}"
        logger.warning(f"Attributes validation failed for type '{item_type}': {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        logger.error(f"Unexpected validation error for type '{item_type}': {error_msg}")
        return False, error_msg


def get_required_fields(item_type: str) -> list:
    """
    Get list of required fields for item type
    
    Args:
        item_type: Type of appraisal item
    
    Returns:
        List of required field names
    """
    schema = get_schema_for_type(item_type)
    return schema.get('required', [])


def get_field_definition(item_type: str, field_name: str) -> dict:
    """
    Get field definition from schema
    
    Args:
        item_type: Type of appraisal item
        field_name: Name of the field
    
    Returns:
        Field definition dictionary
    """
    schema = get_schema_for_type(item_type)
    properties = schema.get('properties', {})
    return properties.get(field_name, {})

