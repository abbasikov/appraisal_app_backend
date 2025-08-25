from fastapi import APIRouter
from app.api.v1.endpoints import appraisals, properties, users, reports, auth, otp

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(otp.router, prefix="/otp", tags=["otp"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(appraisals.router, prefix="/appraisals", tags=["appraisals"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])