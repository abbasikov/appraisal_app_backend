from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    company = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    parent_account_id = Column(Integer, ForeignKey("accounts.id"))  # Link to Account
    # Divorce-specific fields
    attorney_name = Column(String)
    attorney_email = Column(String)
    attorney_phone = Column(String)
    case_name = Column(String)
    case_number = Column(String)
    date_of_death = Column(DateTime(timezone=True))  # For estate cases
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent_account = relationship("Account", back_populates="clients")
    projects = relationship("Project", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}')>"