import secrets
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.activity_log import ActivityLog
from app.schemas.user import UserCreate, UserInvite, UserUpdate
from app.core.security import get_password_hash
from app.services.email_service import EmailService
from typing import List, Optional

class UserService:
    
    @staticmethod
    def invite_user(db: Session, user_invite: UserInvite, inviter_id: int) -> Optional[User]:
        """Invite a new user"""
        try:
            # Check if user already exists
            existing = db.query(User).filter(User.email == user_invite.email).first()
            if existing:
                raise ValueError("User with this email already exists")
            
            # Generate invitation token
            invitation_token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=48)
            
            # Create user with invitation
            user = User(
                username=user_invite.email,  # Use email as username initially
                email=user_invite.email,
                password_hash="",  # Empty until password is set
                first_name=user_invite.first_name,
                last_name=user_invite.last_name,
                mobile_number=user_invite.mobile_number,
                role=user_invite.role,
                is_active=False,  # Inactive until password is set
                is_email_verified=False,
                invitation_token=invitation_token,
                invitation_expires_at=expires_at,
                invited_by=inviter_id,
                password_set=False
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Send invitation email
            EmailService.send_invitation_email(
                user_invite.email,
                user_invite.first_name,
                invitation_token
            )
            
            # Log activity
            activity = ActivityLog(
                user_id=inviter_id,
                action=f"Invited user: {user_invite.email}",
                details={"invited_user_id": user.id, "role": user_invite.role.value}
            )
            db.add(activity)
            db.commit()
            
            return user
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def setup_password(db: Session, token: str, password: str) -> Optional[User]:
        """Set password for invited user"""
        try:
            user = db.query(User).filter(
                User.invitation_token == token,
                User.invitation_expires_at > datetime.utcnow(),
                User.password_set == False
            ).first()
            
            if not user:
                raise ValueError("Invalid or expired invitation token")
            
            # Set password and activate user
            user.password_hash = get_password_hash(password)
            user.password_set = True
            user.is_active = True
            user.is_email_verified = True
            user.invitation_token = None
            user.invitation_expires_at = None
            
            db.commit()
            db.refresh(user)
            
            return user
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users"""
        return db.query(User).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_user_role(db: Session, user_id: int, new_role: UserRole, updater_id: int) -> Optional[User]:
        """Update user role"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            old_role = user.role
            user.role = new_role
            
            db.commit()
            db.refresh(user)
            
            # Log activity
            activity = ActivityLog(
                user_id=updater_id,
                action=f"Changed role for {user.email} from {old_role.value} to {new_role.value}",
                details={"target_user_id": user_id, "old_role": old_role.value, "new_role": new_role.value}
            )
            db.add(activity)
            db.commit()
            
            return user
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_user(db: Session, user_id: int, deleter_id: int) -> bool:
        """Delete user"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("User not found")
            
            user_email = user.email
            db.delete(user)
            db.commit()
            
            # Log activity
            activity = ActivityLog(
                user_id=deleter_id,
                action=f"Deleted user: {user_email}",
                details={"deleted_user_id": user_id, "deleted_user_email": user_email}
            )
            db.add(activity)
            db.commit()
            
            return True
            
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def can_invite_role(inviter_role: UserRole, target_role: UserRole) -> bool:
        """Check if inviter can invite target role"""
        if inviter_role == UserRole.ADMIN:
            return True  # Admin can invite anyone
        elif inviter_role == UserRole.EDITOR:
            return target_role in [UserRole.EDITOR, UserRole.READER]
        return False
    
    @staticmethod
    def can_delete_user(deleter_role: UserRole, target_role: UserRole) -> bool:
        """Check if deleter can delete target user"""
        if deleter_role == UserRole.ADMIN:
            return True  # Admin can delete anyone
        elif deleter_role == UserRole.EDITOR:
            return target_role == UserRole.READER  # Editor can only delete readers
        return False
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        from app.core.security import verify_password
        
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email"""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def create_user(db: Session, user_create: UserCreate) -> Optional[User]:
        """Create new user"""
        try:
            user = User(
                username=user_create.username,
                email=user_create.email,
                password_hash=get_password_hash(user_create.password),
                first_name=user_create.first_name,
                last_name=user_create.last_name,
                phone=user_create.phone,
                mobile_number=user_create.mobile_number,
                role=user_create.role,
                is_active=True,
                password_set=True
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
            
        except Exception as e:
            db.rollback()
            return None
    
    @staticmethod
    def verify_email(db: Session, email: str) -> bool:
        """Mark user email as verified"""
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.is_email_verified = True
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def update_password_by_email(db: Session, email: str, new_password: str) -> bool:
        """Update user password by email"""
        try:
            user = db.query(User).filter(User.email == email).first()
            if user:
                user.password_hash = get_password_hash(new_password)
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Update user profile"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            update_data = user_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            db.commit()
            db.refresh(user)
            return user
            
        except Exception:
            db.rollback()
            return None