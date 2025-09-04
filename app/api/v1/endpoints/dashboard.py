from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.database import get_db
from app.services.dashboard_service import DashboardService
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/open-projects")
async def get_open_projects(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get open/active projects for dashboard"""
    return DashboardService.get_open_projects(db, limit)

@router.get("/completed-projects")
async def get_completed_projects(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Get completed projects for dashboard"""
    return DashboardService.get_completed_projects(db, limit)

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get dashboard statistics"""
    return DashboardService.get_dashboard_stats(db)