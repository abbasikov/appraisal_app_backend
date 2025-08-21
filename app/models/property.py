from sqlalchemy import Column, Integer, String, DateTime, Enum, Float
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class PropertyType(enum.Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    LAND = "land"

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)
    property_type = Column(Enum(PropertyType), nullable=False)
    square_footage = Column(Integer)
    lot_size = Column(Float)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    year_built = Column(Integer)
    legal_description = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())