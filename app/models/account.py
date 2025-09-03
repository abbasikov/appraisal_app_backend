from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

class AccountType(enum.Enum):
    ATTORNEY = "attorney"
    ESTATE_PLANNER = "estate_planner"
    HOUSE_MANAGER = "house_manager"
    FINANCIAL_MANAGER = "financial_manager"
    ASSISTANT = "assistant"
    APPRAISER = "appraiser"
    CLIENT = "client"

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    phone = Column(String)
    alt_phone = Column(String)
    email = Column(String)
    web_address = Column(String)
    parent_account_id = Column(Integer, ForeignKey("accounts.id"))
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    parent_account = relationship("Account", remote_side=[id])
    sub_accounts = relationship("Account", back_populates="parent_account")
    projects = relationship("Project", back_populates="account")

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}', type='{self.account_type.value}')>"