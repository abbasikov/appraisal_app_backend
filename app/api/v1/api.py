from fastapi import APIRouter
from app.api.v1.endpoints import appraisals, projects, users, reports, auth, otp, clients

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(otp.router, prefix="/otp", tags=["otp"]) 
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(appraisals.router, prefix="/appraisals", tags=["appraisals"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])