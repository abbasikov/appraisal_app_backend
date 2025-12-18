from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Archive(Base):
    __tablename__ = "archives"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    archive_status = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Unique constraint to ensure only one record per client-account pair
    __table_args__ = (UniqueConstraint('client_id', 'account_id', name='unique_client_account_archive'),)

    # Relationships
    client = relationship("Client")
    account = relationship("Account")

    def __repr__(self):
        return f"<Archive(id={self.id}, client_id={self.client_id}, account_id={self.account_id}, status={self.archive_status})>"
