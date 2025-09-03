from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    READER = "reader"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    mobile_number = Column(String)
    role = Column(Enum(UserRole), default=UserRole.READER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    otp_secret = Column(String)  # For OTP MFA
    otp_enabled = Column(Boolean, default=False)
    invitation_token = Column(String)
    invitation_expires_at = Column(DateTime(timezone=True))
    invited_by = Column(Integer)
    password_set = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    assigned_projects = relationship("Project", back_populates="assigned_user")
    activity_logs = relationship("ActivityLog", back_populates="user")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}')>"