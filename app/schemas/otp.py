from pydantic import BaseModel

class OTPSetupResponse(BaseModel):
    qr_code: str  # Base64 encoded QR code image
    secret: str   # Backup secret for manual entry

class OTPVerifyRequest(BaseModel):
    otp_code: str

class OTPStatusResponse(BaseModel):
    enabled: bool

class LoginMFARequest(BaseModel):
    username: str
    password: str
    otp_code: str