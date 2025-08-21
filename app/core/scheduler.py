import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.services.verification_service import VerificationService
from app.services.cleanup_service import CleanupService

async def cleanup_task():
    """Background task to cleanup expired codes and unverified users"""
    while True:
        try:
            db = SessionLocal()
            
            # Cleanup expired codes
            expired_codes = VerificationService.cleanup_expired_codes(db)
            
            # Cleanup unverified users older than 7 days
            unverified_users = CleanupService.cleanup_unverified_users(db, days=7)
            
            if expired_codes > 0 or unverified_users > 0:
                print(f"[{datetime.now()}] Cleanup: {expired_codes} expired codes, {unverified_users} unverified users")
            
            db.close()
            
        except Exception as e:
            print(f"Cleanup task error: {e}")
        
        # Run every hour
        await asyncio.sleep(3600)