from fastapi import APIRouter
from app.api.v1.endpoints import appraisals, projects, users, reports, auth, otp, clients, photos, templates, accounts, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(otp.router, prefix="/otp", tags=["otp"]) 
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(clients.router, prefix="/clients", tags=["clients"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(photos.router, prefix="/photos", tags=["photos"])
api_router.include_router(appraisals.router, prefix="/appraisals", tags=["appraisals"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])