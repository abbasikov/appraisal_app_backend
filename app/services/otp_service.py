import pyotp
import qrcode
import io
import base64
from sqlalchemy.orm import Session
from app.models.user import User

class OTPService:
    @staticmethod
    def generate_secret() -> str:
        """Generate a new OTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(user: User, secret: str) -> str:
        """Generate QR code for OTP setup"""
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="Appraisal App"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def verify_otp(secret: str, token: str) -> bool:
        """Verify OTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=2)
    
    @staticmethod
    def enable_otp(db: Session, user_id: int, secret: str) -> bool:
        """Enable OTP for user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.otp_secret = secret
        user.otp_enabled = True
        db.commit()
        return True
    
    @staticmethod
    def disable_otp(db: Session, user_id: int) -> bool:
        """Disable OTP for user"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        user.otp_secret = None
        user.otp_enabled = False
        db.commit()
        return True