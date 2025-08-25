from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from sqlalchemy.sql import func
from app.db.database import get_db
from app.schemas.user import (
    UserCreate, UserLogin, Token, UserResponse, PasswordReset, 
    PasswordResetConfirm, EmailVerification, ResendVerification, VerificationStatus
)
from app.schemas.otp import LoginMFARequest
from app.services.otp_service import OTPService
from app.services.user_service import UserService
from app.services.verification_service import VerificationService
from app.services.cleanup_service import CleanupService
from app.models.verification_code import CodeType
from app.models.user import UserRole
from app.core.security import create_access_token
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    # Clean up expired codes first
    VerificationService.cleanup_expired_codes(db)
    
    # Check if username already exists
    if UserService.get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_user = UserService.get_user_by_email(db, user.email)
    if existing_user:
        if existing_user.is_email_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered and verified"
            )
        else:
            # Allow re-registration if email not verified (overwrite old account)
            db.delete(existing_user)
            db.commit()
    
    # Prevent admin role creation through signup
    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin accounts cannot be created through signup"
        )
    
    # Create user
    db_user = UserService.create_user(db, user)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    # Send verification email
    email_sent = VerificationService.send_email_verification(db, user.email)
    if not email_sent:
        # Don't fail registration if email fails, user can resend
        pass
    
    return db_user

@router.get("/verification-status/{email}", response_model=VerificationStatus)
async def get_verification_status(email: str, db: Session = Depends(get_db)):
    """Get verification status and resend capability for an email"""
    status_info = CleanupService.get_user_verification_status(db, email)
    
    if status_info["exists"] and not status_info["is_verified"]:
        # Check if user can resend verification code
        resend_info = VerificationService.can_resend_code(db, email, CodeType.EMAIL_VERIFICATION)
        status_info.update(resend_info)
    
    return status_info

@router.post("/verify-email")
async def verify_email(verification: EmailVerification, db: Session = Depends(get_db)):
    # Clean up expired codes
    VerificationService.cleanup_expired_codes(db)
    
    # Check if user exists
    user = UserService.get_user_by_email(db, verification.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Verify the code
    is_valid = VerificationService.verify_code(
        db, verification.email, verification.code, CodeType.EMAIL_VERIFICATION
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    # Mark email as verified
    success = UserService.verify_email(db, verification.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify email"
        )
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(resend: ResendVerification, db: Session = Depends(get_db)):
    # Clean up expired codes
    VerificationService.cleanup_expired_codes(db)
    
    # Check if user exists
    user = UserService.get_user_by_email(db, resend.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Check rate limiting
    resend_info = VerificationService.can_resend_code(db, resend.email, CodeType.EMAIL_VERIFICATION)
    if not resend_info["can_resend"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {resend_info['wait_time']} seconds before requesting a new code"
        )
    
    # Check daily limit (max 5 codes per hour)
    attempts = VerificationService.get_code_attempts(db, resend.email, CodeType.EMAIL_VERIFICATION)
    if attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many verification attempts. Please try again later."
        )
    
    # Send verification email
    email_sent = VerificationService.send_email_verification(db, resend.email)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )
    
    return {"message": "Verification email sent"}

@router.post("/signin")
async def signin(user_credentials: UserLogin, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Skip email verification for admin users
    if not user.is_email_verified and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email before signing in.",
            headers={"X-Verification-Required": "true"}
        )
    
    # Check if user has OTP enabled
    if user.otp_enabled:
        return {"requiresOTP": True, "message": "OTP required"}
    
    # Update last login
    user.last_login = func.now()
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/signin-mfa", response_model=Token)
async def signin_mfa(user_credentials: LoginMFARequest, db: Session = Depends(get_db)):
    user = UserService.authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Skip email verification for admin users
    if not user.is_email_verified and user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email before signing in.",
            headers={"X-Verification-Required": "true"}
        )
    
    # Verify OTP if enabled
    if user.otp_enabled:
        if not user.otp_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OTP secret not found"
            )
            
        if not OTPService.verify_otp(user.otp_secret, user_credentials.otp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP code"
            )
    
    # Update last login
    user.last_login = func.now()
    db.commit()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/password-reset")
async def request_password_reset(password_reset: PasswordReset, db: Session = Depends(get_db)):
    # Clean up expired codes
    VerificationService.cleanup_expired_codes(db)
    
    user = UserService.get_user_by_email(db, password_reset.email)
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a password reset code has been sent"}
    
    if not user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified. Please verify your email first."
        )
    
    # Check rate limiting
    resend_info = VerificationService.can_resend_code(db, password_reset.email, CodeType.PASSWORD_RESET)
    if not resend_info["can_resend"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {resend_info['wait_time']} seconds before requesting a new code"
        )
    
    # Send password reset code
    email_sent = VerificationService.send_password_reset_code(db, password_reset.email)
    if not email_sent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )
    
    return {"message": "Password reset code sent to your email"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    password_reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    # Clean up expired codes
    VerificationService.cleanup_expired_codes(db)
    
    # Verify the code
    is_valid = VerificationService.verify_code(
        db, password_reset_confirm.email, password_reset_confirm.code, CodeType.PASSWORD_RESET
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset code"
        )
    
    # Update password
    success = UserService.update_password_by_email(
        db, password_reset_confirm.email, password_reset_confirm.new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "Password updated successfully"}

@router.post("/refresh-token", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/cleanup")
async def cleanup_expired_data(db: Session = Depends(get_db)):
    """Admin endpoint to cleanup expired codes and unverified users"""
    expired_codes = VerificationService.cleanup_expired_codes(db)
    unverified_users = CleanupService.cleanup_unverified_users(db, days=7)
    
    return {
        "message": "Cleanup completed",
        "expired_codes_removed": expired_codes,
        "unverified_users_removed": unverified_users
    }