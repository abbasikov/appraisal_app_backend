from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    thumbnail_path = Column(String)
    file_size = Column(Integer)
    mime_type = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    exif_date = Column(DateTime(timezone=True))
    sort_timestamp = Column(DateTime(timezone=True))  # stable ordering (EXIF→filename→Dropbox modified→created)
    dropbox_server_modified = Column(DateTime(timezone=True))  # Dropbox server_modified when available
    sort_order = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)
    dropbox_file_id = Column(String)
    dropbox_folder_path = Column(String)  # Store the folder/subfolder path
    source_folder_link = Column(String)   # Store which dropbox link this came from
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="photos")
    items = relationship("Item", back_populates="photo")

    def __repr__(self):
        return f"<Photo(id={self.id}, filename='{self.original_filename}', project_id={self.project_id})>"