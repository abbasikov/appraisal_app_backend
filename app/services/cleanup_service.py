from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.verification_code import VerificationCode
from app.models.user import User

class CleanupService:
    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """Remove expired verification codes"""
        expired_codes = db.query(VerificationCode).filter(
            VerificationCode.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        return expired_codes
    
    @staticmethod
    def cleanup_unverified_users(db: Session, days: int = 7) -> int:
        """Remove unverified users older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        unverified_users = db.query(User).filter(
            User.is_email_verified == False,
            User.created_at < cutoff_date
        ).delete()
        db.commit()
        return unverified_users
    
    @staticmethod
    def get_user_verification_status(db: Session, email: str) -> dict:
        """Get detailed verification status for a user"""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return {"exists": False}
        
        # Check for pending verification codes
        pending_code = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        return {
            "exists": True,
            "is_verified": user.is_email_verified,
            "has_pending_code": pending_code is not None,
            "code_expires_at": pending_code.expires_at if pending_code else None,
            "created_at": user.created_at
        }