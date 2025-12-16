from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class Recipient(Base):
    __tablename__ = "recipients"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    name = Column(String, nullable=False)
    title = Column(String)
    company = Column(String)
    address = Column(Text, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip_code = Column(String, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="recipient")

    def __repr__(self):
        return f"<Recipient(id={self.id}, name='{self.name}', project_id={self.project_id})>"
