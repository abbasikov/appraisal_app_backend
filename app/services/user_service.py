from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from typing import Optional

class UserService:
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> Optional[User]:
        try:
            hashed_password = get_password_hash(user.password)
            db_user = User(
                username=user.username,
                email=user.email,
                password_hash=hashed_password,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                role=user.role
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            return None

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        # Try to find user by username first, then by email
        user = UserService.get_user_by_username(db, username_or_email)
        if not user:
            user = UserService.get_user_by_email(db, username_or_email)
        
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(db: Session, user_id: int, new_password: str) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True
    
    @staticmethod
    def verify_email(db: Session, email: str) -> bool:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        user.is_email_verified = True
        db.commit()
        return True
    
    @staticmethod
    def update_password_by_email(db: Session, email: str, new_password: str) -> bool:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return False
        
        user.password_hash = get_password_hash(new_password)
        db.commit()
        return True