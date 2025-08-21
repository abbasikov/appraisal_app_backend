import random
import string
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.verification_code import VerificationCode, CodeType
from app.utils.email import send_verification_email, send_password_reset_email

class VerificationService:
    @staticmethod
    def generate_code(length: int = 6) -> str:
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def create_verification_code(db: Session, email: str, code_type: CodeType) -> str:
        # Delete existing unused codes for this email and type
        db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False
        ).delete()
        
        # Generate new code
        code = VerificationService.generate_code()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        verification_code = VerificationCode(
            email=email,
            code=code,
            code_type=code_type,
            expires_at=expires_at
        )
        
        db.add(verification_code)
        db.commit()
        
        return code
    
    @staticmethod
    def verify_code(db: Session, email: str, code: str, code_type: CodeType) -> bool:
        verification_code = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code == code,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        if not verification_code:
            return False
        
        # Mark code as used
        verification_code.is_used = True
        db.commit()
        
        return True
    
    @staticmethod
    def send_email_verification(db: Session, email: str) -> bool:
        code = VerificationService.create_verification_code(db, email, CodeType.EMAIL_VERIFICATION)
        return send_verification_email(email, code)
    
    @staticmethod
    def send_password_reset_code(db: Session, email: str) -> bool:
        code = VerificationService.create_verification_code(db, email, CodeType.PASSWORD_RESET)
        return send_password_reset_email(email, code)
    
    @staticmethod
    def can_resend_code(db: Session, email: str, code_type: CodeType, cooldown_minutes: int = 2) -> dict:
        """Check if user can request a new code (rate limiting)"""
        last_code = db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type
        ).order_by(VerificationCode.created_at.desc()).first()
        
        if not last_code:
            return {"can_resend": True, "wait_time": 0}
        
        time_since_last = datetime.utcnow() - last_code.created_at
        cooldown_time = timedelta(minutes=cooldown_minutes)
        
        if time_since_last < cooldown_time:
            wait_seconds = int((cooldown_time - time_since_last).total_seconds())
            return {"can_resend": False, "wait_time": wait_seconds}
        
        return {"can_resend": True, "wait_time": 0}
    
    @staticmethod
    def get_code_attempts(db: Session, email: str, code_type: CodeType, hours: int = 1) -> int:
        """Get number of code attempts in the last hour"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.code_type == code_type,
            VerificationCode.created_at > since
        ).count()
    
    @staticmethod
    def cleanup_expired_codes(db: Session) -> int:
        """Remove expired verification codes"""
        expired_count = db.query(VerificationCode).filter(
            VerificationCode.expires_at < datetime.utcnow()
        ).delete()
        db.commit()
        return expired_count