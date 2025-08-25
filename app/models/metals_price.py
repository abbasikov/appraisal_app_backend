from sqlalchemy import Column, Integer, String, DateTime, Boolean, Date, Numeric, Enum
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class MetalType(enum.Enum):
    GOLD = "gold"
    SILVER = "silver"
    PLATINUM = "platinum"
    PALLADIUM = "palladium"

class MetalsPrice(Base):
    __tablename__ = "metals_prices"

    id = Column(Integer, primary_key=True, index=True)
    metal_type = Column(Enum(MetalType), nullable=False)
    price_per_oz = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default="USD")
    price_date = Column(Date, nullable=False)
    source = Column(String, default="metals_api")
    is_manual_override = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MetalsPrice(metal='{self.metal_type.value}', price=${self.price_per_oz}, date='{self.price_date}')>"