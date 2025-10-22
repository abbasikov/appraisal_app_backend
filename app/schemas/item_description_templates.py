"""
Item Description Templates for Auto-Population
"""

ITEM_DESCRIPTION_TEMPLATES = {
    "Artwork": """Artwork Type: [Enter Artwork Type]
Item Name: [Enter Item Name]
Artist Name: [Enter Artist Name]
Artist Nationality: [Enter Nationality]
Artist Life Dates: [Enter Dates]
Title of Work: [Enter Title]
Date of Work (Month): [Enter Month]
Year of Work: [Enter Year]
Medium: [Enter Medium]
Artwork Dimensions: [Enter Dimensions]
Frame Dimensions: [Enter Frame Dimensions]
Description of Subject Matter: [Enter Details]
Description of Frame: [Enter Frame Details]
Condition: [Enter Condition]
Condition Explanation: [Enter Details]
Provenance / Literature / Exhibitions: [Enter Info]""",

    "Watches": """Watch Type: [Enter Watch Type]
Make: [Enter Make]
Model: [Enter Model]
Reference: [Enter Reference Number]
Serial Number: [Enter Serial Number]
Movement: [Enter Movement Type]
Case Metal: [Enter Case Metal]
Case Diameter: [Enter Diameter]
Dial: [Enter Dial Description]
Bezel: [Enter Bezel Type]
Crystal: [Enter Crystal Type]
Band: [Enter Band Description]
Buckle: [Enter Buckle Type]
Functions: [Enter Functions]
Condition: [Enter Condition]
Box Description: [Enter Box Details]
Papers Description: [Enter Papers Details]""",

    "Jewelry": """Stone Type: [Enter Stone Type]
Cut: [Enter Cut]
Clarity: [Enter Clarity]
Carat Weight: [Enter Carat Weight]
Metal Type: [Enter Metal Type]
Hallmarks: [Enter Hallmarks]
Weight: [Enter Weight]
Visual Description: [Enter Visual Description]
Papers Description: [Enter Papers Details]
Condition: [Enter Condition]
Authentication: [Enter Authentication Details]""",

    "Auto": """Year: [Enter Year]
Make: [Enter Make]
Model: [Enter Model]
VIN: [Enter VIN Number]
Miles: [Enter Mileage]
Color: [Enter Color]
Style: [Enter Style]
Condition: [Enter Condition]
Provenance: [Enter Provenance Details]""",

    "Handbag": """Designer: [Enter Designer]
Model: [Enter Model]
Color: [Enter Color]
Material: [Enter Material]
Hardware: [Enter Hardware Details]
Style: [Enter Style]
Condition: [Enter Condition]
Notes: [Enter Additional Notes]""",

    "Firearms": """Manufacturer: [Enter Manufacturer]
Model: [Enter Model]
Serial Number: [Enter Serial Number]
Type: [Enter Firearm Type]
Caliber: [Enter Caliber]
Condition: [Enter Condition]
Notes: [Enter Additional Notes]""",

    "Coins": """Quantity: [Enter Quantity]
Year: [Enter Year]
Description: [Enter Description]
Condition: [Enter Condition]
Notes: [Enter Additional Notes]""",

    "Wine": """Quantity: [Enter Quantity]
Year: [Enter Year]
Description: [Enter Wine Description]
Per Bottle Price: [Enter Price]
Notes: [Enter Additional Notes]""",

    "Collectibles": """Description: [Enter Description]
Maker: [Enter Maker]
Model Number: [Enter Model Number]
Materials: [Enter Materials]
Dimensions: [Enter Dimensions]
Condition: [Enter Condition]
Rarity: [Enter Rarity Details]
Provenance: [Enter Provenance]""",

    "Contents": """Brand Name: [Enter Brand Name]
Manufacturer: [Enter Manufacturer]
Model Number: [Enter Model Number]
Serial Number: [Enter Serial Number]
Dimensions: [Enter Dimensions]
Materials: [Enter Materials]
Condition: [Enter Condition]
Notes: [Enter Additional Notes]"""
}

def get_description_template(item_type: str) -> str:
    """Get description template for a specific item type"""
    return ITEM_DESCRIPTION_TEMPLATES.get(item_type, "Description: [Enter Item Description]")