"""
Item Description Templates for Auto-Population
"""

ITEM_DESCRIPTION_TEMPLATES = {
    "Artwork": """Artist Name: 
Artist Nationality: 
Artist Life Dates: 
Title of Work: 
Date of Work: 
Medium: 
Artwork Dimensions: 
Frame Dimensions: 
Signatures/Inspections: 
Description of Subject Matter: 
Description of Frame: 
Condition: 
Condition Explanation: 
Provenance / Literature / Exhibitions: """,

    "Watches": """Make: 
Model: 
Reference: 
Serial Number: 
Movement: 
Case Metal: 
Case Diameter: 
Dial: 
Bezel: 
Crystal: 
Band: 
Buckle: 
Functions: 
Condition: 
Box Description: 
Papers Description: """,

    "Jewelry": """Stone Type: 
Cut: 
Clarity: 
Carat Weight: 
Metal Type: 
Hallmarks: 
Weight: 
Visual Description: 
Papers Description: 
Condition: 
Authentication: """,

    "Auto": """Year: 
Make: 
Model: 
VIN: 
Miles: 
Color: 
Style: 
Provenance: """,

    "Handbag": """Designer: 
Color: 
Material: 
Hardware: 
Style: 
Condition: 
Notes: """,

    "Firearms": """Manufacturer: 
Model: 
Serial Number: 
Type: 
Caliber: 
Condition: 
Notes: """,

    "Coins": """Quantity: 
Year: 
Coin Description: 
Condition: 
Value Per Coin $: 
Notes: """,

    "Wine": """Quantity: 
Year: 
Bottle Description: 
Per Bottle Price: 
Notes: """,

    "Collectibles": """Description: 
Maker: 
Model Number: 
Materials: 
Dimensions: 
Condition: 
Rarity: 
Provenance: """,

    "Contents": """Description: 
Brand Name: 
Manufacturer: 
Model Number: 
Serial Number: 
Dimensions: 
Materials: 
Condition: 
Notes: """
}

def get_description_template(item_type: str) -> str:
    """Get description template for a specific item type"""
    return ITEM_DESCRIPTION_TEMPLATES.get(item_type, "Description: [Enter Item Description]")