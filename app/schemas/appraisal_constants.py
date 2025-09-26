"""
Appraisal schema constants and type definitions
"""

from typing import Dict, List, Any
from enum import Enum

# Room/Area options
ROOM_AREA_OPTIONS = [
    "AC CLOSET 1", "AC CLOSET 2", "AC CLOSET 3", "AC CLOSET 4", "ART GALLERY", "ART STUDIO", "ATRIUM", "ATTIC",
    "AU PAIR SUITE", "BALCONY", "BALLROOM", "BAR AREA", "BASEMENT", "BATHROOM 1", "BATHROOM 1 CLOSET", "BATHROOM 2",
    "BATHROOM 2 CLOSET", "BATHROOM 3", "BATHROOM 3 CLOSET", "BATHROOM 4", "BATHROOM 4 CLOSET", "BATHROOM 5",
    "BATHROOM 5 CLOSET", "BATHROOM 6", "BATHROOM 6 CLOSET", "BATHROOM 7", "BATHROOM 7 CLOSET", "BATHROOM 8",
    "BATHROOM 8 CLOSET", "BATHROOM 9", "BATHROOM 9 CLOSET", "BATHROOM 10", "BATHROOM 10 CLOSET", "BATHROOM 11",
    "BATHROOM 11 CLOSET", "BATHROOM 12", "BATHROOM 12 CLOSET", "BATTING CAGE", "BEDROOM 1", "BEDROOM 1 CLOSET 1",
    "BEDROOM 1 CLOSET 2", "BEDROOM 2", "BEDROOM 2 CLOSET 1", "BEDROOM 2 CLOSET 2", "BEDROOM 3", "BEDROOM 3 CLOSET 1",
    "BEDROOM 3 CLOSET 2", "BEDROOM 4", "BEDROOM 4 CLOSET 1", "BEDROOM 4 CLOSET 2", "BEDROOM 5", "BEDROOM 5 CLOSET 1",
    "BEDROOM 5 CLOSET 2", "BEDROOM 6", "BEDROOM 6 CLOSET 1", "BEDROOM 6 CLOSET 2", "BEDROOM 7", "BEDROOM 7 CLOSET 1",
    "BEDROOM 7 CLOSET 2", "BEDROOM 8", "BEDROOM 8 CLOSET 1", "BEDROOM 8 CLOSET 2", "BEDROOM 9", "BEDROOM 9 CLOSET 1",
    "BEDROOM 9 CLOSET 2", "BEDROOM 10", "BEDROOM 10 CLOSET 1", "BEDROOM 10 CLOSET 2", "BEDROOM 11", "BEDROOM 11 CLOSET 1",
    "BEDROOM 11 CLOSET 2", "BEDROOM 12", "BEDROOM 12 CLOSET 1", "BEDROOM 12 CLOSET 2", "BEDROOM 13", "BEDROOM 13 CLOSET 1",
    "BEDROOM 13 CLOSET 2", "BEDROOM 14", "BEDROOM 14 CLOSET 1", "BEDROOM 14 CLOSET 2", "BEDROOM 15", "BEDROOM 15 CLOSET 1",
    "BEDROOM 15 CLOSET 2", "BEDROOM HALLWAY", "BILLIARDS ROOM", "BOWLING ALLEY", "BREAKFAST NOOK", "BUTLER'S PANTRY",
    "CABANA", "CIGAR ROOM", "CLOSET", "CONFERENCE ROOM", "CONSERVATORY", "COURTYARD", "CRAFT ROOM", "DEN", "DINETTE AREA",
    "DINING ROOM", "DINING ROOM 2", "DRAWING ROOM", "EXTERIOR BACK", "EXTERIOR FRONT", "EXTERIOR LEFT SIDE OF FRONT",
    "EXTERIOR RIGHT SIDE OF FRONT", "FAMILY ROOM", "FLORIDA ROOM", "FOYER", "FOYER CLOSET", "GARAGE", "GAZEBO",
    "GREENHOUSE", "GYM/WORKOUT ROOM", "GYMNASTICS ROOM", "HALLWAY", "HALLWAY CLOSET 1", "HALLWAY CLOSET 2",
    "HALLWAY CLOSET 3", "HALLWAY CLOSET 4", "HALLWAY CLOSET 5", "HALLWAY CLOSET 6", "HALLWAY CLOSET 7",
    "HALLWAY CLOSET 8", "HALLWAY CLOSET 9", "HALLWAY CLOSET 10", "HALLWAY CLOSET 11", "HALLWAY CLOSET 12",
    "HALLWAY CLOSET 13", "HALLWAY CLOSET 14", "HALLWAY CLOSET 15", "HALLWAY CLOSET 16", "HALLWAY CLOSET 17",
    "HALLWAY CLOSET 18", "HALLWAY CLOSET 19", "HALLWAY CLOSET 20", "HOME GYM", "HOME THEATER", "INDOOR BASKETBALL COURT",
    "INDOOR POOL", "INDOOR TENNIS COURT", "KEEPING ROOM", "KITCHEN", "KITCHEN 2", "LAUNDRY", "LIBRARY/STUDY",
    "LINEN CLOSET", "LIVING ROOM", "LOFT", "LOGGIA", "LOUNGE", "MASSAGE ROOM", "MASTER BATHOOM CLOSET", "MASTER BATHROOM",
    "MASTER BEDROOM", "MASTER BEDROOM CLOSET 1", "MASTER BEDROOM CLOSET 2", "MASTER BEDROOM CLOSET 3",
    "MASTER BEDROOM CLOSET 4", "MEDITATION ROOM", "MOTHER IN LAW SUITE", "MUD ROOM", "MUSIC ROOM",
    "NON BEDROOM or BATHROOM CLOSETS", "NURSERY", "OFFICE 1", "OFFICE 2", "OTHER ROOM 1", "OTHER ROOM 2",
    "OTHER ROOM 3", "OTHER ROOM 4", "OTHER ROOM 5", "OTHER ROOM 6", "OTHER ROOM 7", "OTHER ROOM 8", "OTHER ROOM 9",
    "OTHER ROOM 10", "OTHER ROOM 11", "OTHER ROOM 12", "OUTDOOR KITCHEN", "PANIC ROOM", "PANTRY", "PARLOR",
    "PATIO/DECK", "PET ROOM", "PLAYROOM/REC ROOM", "PORCH", "ROOF", "SAUNA", "SCULLERY", "SERVANT QUARTERS",
    "SHED", "SPA ROOM", "STAIRS/STAIRWAY", "STEAM ROOM", "STORAGE AREA UNDER STAIRWELL", "SUN ROOM", "TERRACE",
    "TRAMPOLINE ROOM", "UTILITY ROOM", "VERANDA", "VESTIBULE", "WINE CELLAR", "WINE TASTING ROOM", "WORKSHOP", "YOGA ROOM"
]

# Floor/Building options
FLOOR_BUILDING_OPTIONS = [
    "1st", "2nd", "3rd", "4th", "5th", "6th", "Mother-In-Law Suite", "Barn", "Workshed", "Detached Garage",
    "Workers Quarters", "Basement", "Sub-Basement", "Cellar", "Lower Level", "Ground Floor", "Mezzanine",
    "Loft Level", "Attic", "Roof Level", "Penthouse Level", "Tower", "East Wing", "West Wing", "North Wing",
    "South Wing", "Main House", "Guest House", "Pool House", "Carriage House", "Stable", "Greenhouse",
    "Conservatory (detached)", "Gatehouse", "Guard House", "Boathouse", "Tennis Pavilion", "Sports Barn",
    "Equipment Shed", "Gardening Shed", "Outdoor Kitchen Pavilion", "Yoga Pavilion", "Spa Building",
    "Home Theater Annex", "Wine Cellar Building (if detached)", "Art Studio (detached)", "Music Pavilion",
    "Observatory", "Helipad Structure"
]

# Item type options
ITEM_TYPE_OPTIONS = [
    "Artwork", "Watches", "Jewelry", "Auto", "Handbag", "Firearms", "Coins", "Wine", "Collectibles", "Contents"
]

# Type-specific attribute schemas
TYPE_ATTRIBUTES = {
    "Artwork": [
        "artwork_type", "item_name", "artist_name", "artist_nationality", "artist_life_dates",
        "title_of_work", "date_of_work_month", "year_of_work", "medium", "artwork_dimensions",
        "frame_dimensions", "description_of_subject_matter", "description_of_frame",
        "condition", "condition_explanation", "provenance_literature_exhibitions", "artwork_photos"
    ],
    "Watches": [
        "watch_type", "make", "model", "reference", "serial_number", "movement", "case_metal",
        "case_diameter", "dial", "bezel", "crystal", "band", "buckle", "functions", "condition",
        "box_description", "papers_description"
    ],
    "Jewelry": [
        "stone_type", "cut", "clarity", "carat_weight", "metal_type", "hallmarks",
        "weight", "visual_description", "papers_description", "condition", "authentication"
    ],
    "Auto": [
        "year", "make", "model", "vin", "miles", "color", "style", "condition", "provenance"
    ],
    "Handbag": [
        "designer", "model", "color", "material", "hardware", "style", "condition", "notes"
    ],
    "Firearms": [
        "manufacturer", "model", "serial_number", "type", "caliber", "condition", "notes"
    ],
    "Coins": [
        "quantity", "year", "description", "condition", "notes"
    ],
    "Wine": [
        "quantity", "year", "description", "per_bottle_price", "notes"
    ],
    "Collectibles": [
        "description", "maker", "model_number", "materials", "dimensions",
        "condition", "rarity", "provenance"
    ],
    "Contents": [
        "brand_name", "manufacturer", "model_number", "serial_number",
        "dimensions", "materials", "condition", "notes"
    ]
}

# Required fields per type
REQUIRED_ATTRIBUTES = {
    "Artwork": ["artist_name", "title_of_work", "medium", "condition"],
    "Watches": ["make", "model", "condition"],
    "Jewelry": ["stone_type", "metal_type", "condition"],
    "Auto": ["year", "make", "model", "condition"],
    "Handbag": ["designer", "condition"],
    "Firearms": ["manufacturer", "model", "condition"],
    "Coins": ["description", "condition"],
    "Wine": ["description", "year"],
    "Collectibles": ["description", "condition"],
    "Contents": ["description", "condition"]
}