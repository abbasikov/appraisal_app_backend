from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.database import Base

class FormTemplate(Base):
    __tablename__ = "form_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    template_type = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    version = Column(String, default="1.0")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())