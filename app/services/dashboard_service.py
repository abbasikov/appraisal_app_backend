from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from app.models.project import Project, ProjectStatus
from app.models.client import Client

class DashboardService:
    
    @staticmethod
    def get_open_projects(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get open/active projects"""
        open_statuses = [ProjectStatus.DRAFT, ProjectStatus.IN_PROGRESS, ProjectStatus.REVIEW]
        
        projects = db.query(Project, Client).join(
            Client, Project.client_id == Client.id
        ).filter(
            Project.status.in_(open_statuses)
        ).order_by(Project.created_at.desc()).limit(limit).all()
        
        result = []
        for project, client in projects:
            # Handle timezone-aware datetime comparison
            if project.created_at:
                if project.created_at.tzinfo is None:
                    # If created_at is naive, make it timezone-aware
                    created_at_aware = project.created_at.replace(tzinfo=timezone.utc)
                else:
                    created_at_aware = project.created_at
                days_since_created = (datetime.now(timezone.utc) - created_at_aware).days
            else:
                days_since_created = 0
            
            result.append({
                "id": project.id,
                "project_name": project.project_name,
                "client_name": client.name,
                "status": project.status.value,
                "created_at": project.created_at,
                "days_since_created": days_since_created,
                "case_number": project.case_number,
                "appraisal_type": project.appraisal_type.value if project.appraisal_type else None
            })
        
        return result
    
    @staticmethod
    def get_completed_projects(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Get completed projects"""
        completed_statuses = [ProjectStatus.COMPLETED, ProjectStatus.DELIVERED]
        
        projects = db.query(Project, Client).join(
            Client, Project.client_id == Client.id
        ).filter(
            Project.status.in_(completed_statuses)
        ).order_by(Project.updated_at.desc()).limit(limit).all()
        
        result = []
        for project, client in projects:
            result.append({
                "id": project.id,
                "project_name": project.project_name,
                "client_name": client.name,
                "status": project.status.value,
                "updated_at": project.updated_at,
                "case_number": project.case_number,
                "appraisal_type": project.appraisal_type.value if project.appraisal_type else None,
                "total_value": float(project.total_value) if project.total_value else 0.0
            })
        
        return result
    
    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Get dashboard statistics"""
        total_projects = db.query(Project).count()
        open_projects = db.query(Project).filter(
            Project.status.in_([ProjectStatus.DRAFT, ProjectStatus.IN_PROGRESS, ProjectStatus.REVIEW])
        ).count()
        completed_projects = db.query(Project).filter(
            Project.status.in_([ProjectStatus.COMPLETED, ProjectStatus.DELIVERED])
        ).count()
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_projects = db.query(Project).filter(
            Project.created_at >= thirty_days_ago
        ).count()
        
        return {
            "total_projects": total_projects,
            "open_projects": open_projects,
            "completed_projects": completed_projects,
            "recent_projects": recent_projects
        }