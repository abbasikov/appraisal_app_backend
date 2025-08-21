from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class UserRole(enum.Enum):
    APPRAISER = "appraiser"
    ADMIN = "admin"
    CLIENT = "client"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    phone = Column(String)
    role = Column(Enum(UserRole), default=UserRole.APPRAISER)
    license_number = Column(String)
    certification_level = Column(String)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())