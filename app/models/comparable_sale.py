from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class ComparableSale(Base):
    __tablename__ = "comparable_sales"

    id = Column(Integer, primary_key=True, index=True)
    appraisal_id = Column(Integer, ForeignKey("appraisals.id"), nullable=False)
    address = Column(String, nullable=False)
    sale_date = Column(Date, nullable=False)
    sale_price = Column(Float, nullable=False)
    square_footage = Column(Integer)
    adjustments = Column(Float, default=0.0)
    distance_from_subject = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appraisal = relationship("Appraisal")