from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    line_number = Column(Integer, nullable=False)
    photo_id = Column(Integer, ForeignKey("photos.id"))
    room_area = Column(String)
    item_type = Column(String)
    description = Column(Text)
    detailed_description = Column(Text)
    estimated_value = Column(Numeric(10, 2))
    replacement_value = Column(Numeric(10, 2))
    market_value = Column(Numeric(10, 2))
    condition_notes = Column(Text)
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="items")
    photo = relationship("Photo", back_populates="items")

    def __repr__(self):
        return f"<Item(id={self.id}, line_number={self.line_number}, description='{self.description[:50]}...')>"