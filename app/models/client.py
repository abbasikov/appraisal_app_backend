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
    parent_client_id = Column(Integer, ForeignKey("clients.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent_client = relationship("Client", remote_side=[id])
    sub_clients = relationship("Client", back_populates="parent_client")
    projects = relationship("Project", back_populates="client")

    def __repr__(self):
        return f"<Client(id={self.id}, name='{self.name}')>"