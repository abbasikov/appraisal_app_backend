from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate

class AccountService:
    
    @staticmethod
    def create_account(db: Session, account_data: AccountCreate) -> Account:
        """Create a new account"""
        try:
            account = Account(**account_data.model_dump())
            db.add(account)
            db.commit()
            db.refresh(account)
            return account
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create account: {str(e)}")
    
    @staticmethod
    def get_accounts(db: Session, account_type: str = None, is_active: bool = True) -> List[Account]:
        """Get filtered accounts"""
        query = db.query(Account).filter(Account.is_active == is_active)
        
        if account_type:
            query = query.filter(Account.account_type == account_type)
        
        return query.order_by(Account.name).all()
    
    @staticmethod
    def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        return db.query(Account).filter(Account.id == account_id).first()
    
    @staticmethod
    def update_account(db: Session, account_id: int, account_data: AccountUpdate) -> Account:
        """Update account"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        try:
            update_data = account_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(account, field, value)
            
            db.commit()
            db.refresh(account)
            return account
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update account: {str(e)}")
    
    @staticmethod
    def delete_account(db: Session, account_id: int) -> bool:
        """Soft delete account"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        try:
            account.is_active = False
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete account: {str(e)}")
    
    @staticmethod
    def get_sub_accounts(db: Session, parent_account_id: int) -> List[Account]:
        """Get sub-accounts for a parent account"""
        return db.query(Account).filter(
            Account.parent_account_id == parent_account_id,
            Account.is_active == True
        ).order_by(Account.name).all()