from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.otp_service import OTPService
from app.schemas.otp import OTPSetupResponse, OTPVerifyRequest, OTPStatusResponse

router = APIRouter()

@router.get("/status", response_model=OTPStatusResponse)
async def get_otp_status(current_user: User = Depends(get_current_user)):
    """Get current OTP status for user"""
    return OTPStatusResponse(enabled=current_user.otp_enabled)

@router.post("/setup", response_model=OTPSetupResponse)
async def setup_otp(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate QR code for OTP setup"""
    if current_user.otp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is already enabled"
        )
    
    secret = OTPService.generate_secret()
    qr_code = OTPService.generate_qr_code(current_user, secret)
    
    # Store the secret temporarily (but don't enable OTP yet)
    current_user.otp_secret = secret
    db.commit()
    
    return OTPSetupResponse(qr_code=qr_code, secret=secret)

@router.post("/enable")
async def enable_otp(
    request: OTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enable OTP after verifying setup"""
    if current_user.otp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is already enabled"
        )
    
    if not current_user.otp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP setup found. Please run setup first."
        )
    
    # Verify the OTP code with the stored secret
    if not OTPService.verify_otp(current_user.otp_secret, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    # Enable OTP with the existing secret
    current_user.otp_enabled = True
    db.commit()
    
    return {"message": "OTP enabled successfully"}

@router.post("/disable")
async def disable_otp(
    request: OTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable OTP after verification"""
    if not current_user.otp_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP is not enabled"
        )
    
    if not OTPService.verify_otp(current_user.otp_secret, request.otp_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code"
        )
    
    success = OTPService.disable_otp(db, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable OTP"
        )
    
    return {"message": "OTP disabled successfully"}