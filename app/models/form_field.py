from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.database import Base

class FormField(Base):
    __tablename__ = "form_fields"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("form_templates.id"), nullable=False)
    field_name = Column(String, nullable=False)
    field_type = Column(String, nullable=False)
    is_required = Column(Boolean, default=False)
    default_value = Column(String)
    validation_rules = Column(String)

    template = relationship("FormTemplate")