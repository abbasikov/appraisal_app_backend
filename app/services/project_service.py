from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.project import Project
from app.models.client import Client  
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.schemas.project import ProjectCreate, ProjectUpdate
from typing import Optional, List
from datetime import datetime

class ProjectService:
    @staticmethod
    def create_project(db: Session, project: ProjectCreate, user_id: int) -> Optional[Project]:
        try:
            from app.services.archive_service import ArchiveService
            
            # Validate required fields
            if not project.project_name or not project.project_name.strip():
                return None
            
            if not project.client_id or project.client_id <= 0:
                return None
            
            # Get client for validation
            client = db.query(Client).filter(Client.id == project.client_id, Client.is_active == True).first()
            if not client:
                return None
            
            # Determine account_id: use provided value or fallback to client's parent_account_id
            account_id = project.account_id or client.parent_account_id
            
            # Check if this client-account pair is archived (archive_status = False)
            if account_id and ArchiveService.is_archived(db, project.client_id, account_id):
                print(f"Cannot create project: Client-Account pair ({project.client_id}, {account_id}) is archived")
                return None
            
            # Auto-create archive record for this client-account pair if it doesn't exist
            # Archive status will be True by default (active)
            if account_id:
                ArchiveService.create_or_update_archive(
                    db,
                    project.client_id,
                    account_id,
                    archive_status=True  # Always True unless client is deleted
                )
            
            # Update client's case_name if provided
            if project.case_name:
                client.case_name = project.case_name.strip()
                db.commit()
            
            # Update client's parent_account_id if project has an account_id
            # This establishes the client-account association through the project
            if project.account_id:
                client.parent_account_id = project.account_id
                db.commit()
            
            db_project = Project(
                project_name=project.project_name.strip(),
                client_id=project.client_id,
                account_id=account_id,  # Use determined account_id (from request or client's parent account)
                assigned_user_id=project.assigned_user_id or user_id,
                case_number=project.case_number.strip() if project.case_number else None,
                appraisal_type=project.appraisal_type,
                purpose=project.purpose.strip() if project.purpose else None,
                inspection_date=project.inspection_date,
                report_date=project.report_date,
                effective_date=project.effective_date,
                appraisal_location=project.appraisal_location.strip() if project.appraisal_location else None,
                estate_of=project.estate_of.strip() if project.estate_of else None,  # Estate name for ESTATE appraisals
                date_of_death=project.date_of_death,  # Date of death for ESTATE appraisals
                address_letter_to=project.address_letter_to.strip() if project.address_letter_to else None,
                template_id=project.template_id,
                notes=project.notes.strip() if project.notes else None
            )
            
            db.add(db_project)
            db.commit()
            db.refresh(db_project)
            
            # Log activity
            try:
                activity = ActivityLog(
                    user_id=user_id,
                    project_id=db_project.id,
                    action=f"Created project: {project.project_name}",
                    details={"project_id": db_project.id, "client_id": project.client_id, "account_id": account_id}
                )
                db.add(activity)
                db.commit()
            except Exception as log_error:
                pass
            
            # Create Recipient if provided
            if project.recipient:
                from app.models.recipient import Recipient
                recipient = Recipient(
                    project_id=db_project.id,
                    name=project.recipient.name,
                    title=project.recipient.title,
                    company=project.recipient.company,
                    address=project.recipient.address,
                    city=project.recipient.city,
                    state=project.recipient.state,
                    zip_code=project.recipient.zip_code
                )
                db.add(recipient)
                db.commit()
            
            return db_project
        except Exception as e:
            db.rollback()
            print(f"Error creating project: {e}")
            return None
    
    @staticmethod
    def get_projects(db: Session, skip: int = 0, limit: int = 100, client_id: int = None) -> List[dict]:
        try:
            query = db.query(
                Project,
                Client.name.label('client_name'),
                User.first_name.label('user_first_name'),
                User.last_name.label('user_last_name')
            ).join(Client, Project.client_id == Client.id)\
             .outerjoin(User, Project.assigned_user_id == User.id)
            
            if client_id and client_id > 0:
                query = query.filter(Project.client_id == client_id)
            
            results = query.offset(skip).limit(limit).all()
        except Exception as e:
            print(f"Error fetching projects: {e}")
            return []
        
        # Convert to response format
        projects = []
        for project, client_name, user_first, user_last in results:
            project_dict = {
                "id": project.id,
                "project_name": project.project_name,
                "client_id": project.client_id,
                "client_name": client_name,
                "case_number": project.case_number,
                "appraisal_type": project.appraisal_type.value,
                "purpose": project.purpose,
                "inspection_date": project.inspection_date,
                "report_date": project.report_date,
                "effective_date": project.effective_date,
                "appraisal_location": project.appraisal_location,
                "assigned_user_id": project.assigned_user_id,
                "assigned_user_name": f"{user_first} {user_last}" if user_first else None,
                "status": project.status.value,
                "dropbox_folder_link": project.dropbox_folder_link,
                "dropbox_links": project.dropbox_folder_link.split("|") if project.dropbox_folder_link else [],
                "notification_email": project.notification_email,
                "template_id": project.template_id,
                "total_value": float(project.total_value) if project.total_value else 0,
                "item_count": project.item_count,
                "notes": project.notes,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }
            projects.append(project_dict)
        
        return projects
    
    @staticmethod
    def get_project_by_id(db: Session, project_id: int) -> Optional[dict]:
        result = db.query(
            Project,
            Client.name.label('client_name'),
            Client.case_name.label('client_case_name'),
            User.first_name.label('user_first_name'),
            User.last_name.label('user_last_name')
        ).join(Client, Project.client_id == Client.id)\
         .outerjoin(User, Project.assigned_user_id == User.id)\
         .filter(Project.id == project_id).first()
        
        if not result:
            return None
        
        project, client_name, client_case_name, user_first, user_last = result
        
        return {
            "id": project.id,
            "project_name": project.project_name,
            "client_id": project.client_id,
            "client_name": client_name,
            "case_name": client_case_name,
            "case_number": project.case_number,
            "appraisal_type": project.appraisal_type.value,
            "purpose": project.purpose,
            "inspection_date": project.inspection_date,
            "report_date": project.report_date,
            "effective_date": project.effective_date,
            "estate_of": project.estate_of,
            "date_of_death": project.date_of_death,
            "address_letter_to": project.address_letter_to,
            "assigned_user_id": project.assigned_user_id,
            "assigned_user_name": f"{user_first} {user_last}" if user_first else None,
            "status": project.status.value,
            "dropbox_folder_link": project.dropbox_folder_link,
            "dropbox_links": project.dropbox_folder_link.split("|") if project.dropbox_folder_link else [],
            "notification_email": project.notification_email,
            "template_id": project.template_id,
            "total_value": float(project.total_value) if project.total_value else 0,
            "item_count": project.item_count,
            "notes": project.notes,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "recipient": {
                "id": project.recipient.id,
                "project_id": project.recipient.project_id,
                "name": project.recipient.name,
                "title": project.recipient.title,
                "company": project.recipient.company,
                "address": project.recipient.address,
                "city": project.recipient.city,
                "state": project.recipient.state,
                "zip_code": project.recipient.zip_code
            } if project.recipient else None
        }
    
    @staticmethod
    def update_project(db: Session, project_id: int, project_update: ProjectUpdate, user_id: int) -> Optional[Project]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        update_data = project_update.dict(exclude_unset=True)
        
        # Extract recipient before setting project fields
        recipient_data = update_data.pop('recipient', None)
        
        for field, value in update_data.items():
            if field == 'appraisal_location' and value:
                setattr(project, field, value.strip())
            else:
                setattr(project, field, value)
        
        db.commit()
        db.refresh(project)
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            project_id=project_id,
            action=f"Updated project: {project.project_name}",
            details={"updated_fields": list(update_data.keys())}
        )
        db.add(activity)
        db.commit()
        
        # Update Recipient if provided
        if recipient_data:
            from app.models.recipient import Recipient
            recipient = db.query(Recipient).filter(Recipient.project_id == project_id).first()
            
            if recipient:
                # Update existing - only update fields that are provided (not None)
                if recipient_data.get('name') is not None: recipient.name = recipient_data['name']
                if recipient_data.get('title') is not None: recipient.title = recipient_data['title']
                if recipient_data.get('company') is not None: recipient.company = recipient_data['company']
                if recipient_data.get('address') is not None: recipient.address = recipient_data['address']
                if recipient_data.get('city') is not None: recipient.city = recipient_data['city']
                if recipient_data.get('state') is not None: recipient.state = recipient_data['state']
                if recipient_data.get('zip_code') is not None: recipient.zip_code = recipient_data['zip_code']
                db.commit()
            else:
                # Only create new recipient if all required fields are provided
                if (recipient_data.get('name') and 
                    recipient_data.get('address') and 
                    recipient_data.get('city') and 
                    recipient_data.get('state') and 
                    recipient_data.get('zip_code')):
                    recipient = Recipient(
                        project_id=project_id,
                        name=recipient_data['name'],
                        title=recipient_data.get('title'),
                        company=recipient_data.get('company'),
                        address=recipient_data['address'],
                        city=recipient_data['city'],
                        state=recipient_data['state'],
                        zip_code=recipient_data['zip_code']
                    )
                    db.add(recipient)
                    db.commit()
        
        return project
    
    @staticmethod
    def update_dropbox_links(db: Session, project_id: int, folder_links: List[str], user_id: int, notification_email: str = None) -> Optional[Project]:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None
        
        # Store up to 10 Dropbox folder links
        links_str = "|".join(folder_links[:10]) if folder_links else None
        project.dropbox_folder_link = links_str
        
        # Update notification email
        project.notification_email = notification_email
        
        db.commit()
        db.refresh(project)
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            project_id=project_id,
            action=f"Updated Dropbox links for project: {project.project_name}",
            details={"links_count": len(folder_links), "notification_email": bool(notification_email)}
        )
        db.add(activity)
        db.commit()
        
        return project
    
    @staticmethod
    def delete_project(db: Session, project_id: int, user_id: int) -> bool:
        try:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                print(f"Project {project_id} not found in database")
                return False
            
            project_name = project.project_name
            print(f"Deleting project: {project_name} (ID: {project_id})")
            
            # Delete related records first to avoid foreign key constraints
            from app.models.photo import Photo
            from app.models.appraisal_item import AppraisalItem
            from app.models.activity_log import ActivityLog
            from app.models.report import Report
            
            # Delete task statuses first (since they have NOT NULL constraint on project_id)
            # Use raw SQL to avoid circular import issues with relationships
            from sqlalchemy import text
            task_statuses_deleted = db.execute(text("DELETE FROM task_status WHERE project_id = :project_id"), {"project_id": project_id})
            print(f"Deleted {task_statuses_deleted.rowcount} task status records")
            
            # Delete appraisal items first (they reference photos via photo_id)
            items_deleted = db.query(AppraisalItem).filter(AppraisalItem.project_id == project_id).delete()
            print(f"Deleted {items_deleted} appraisal items")
            
            # Delete photos after appraisal items (no more references)
            photos_deleted = db.query(Photo).filter(Photo.project_id == project_id).delete()
            print(f"Deleted {photos_deleted} photos")
            
            # Delete reports
            reports_deleted = db.query(Report).filter(Report.project_id == project_id).delete()
            print(f"Deleted {reports_deleted} reports")
            
            # Delete activity logs
            logs_deleted = db.query(ActivityLog).filter(ActivityLog.project_id == project_id).delete()
            print(f"Deleted {logs_deleted} activity logs")
            
            # Now delete the project
            db.delete(project)
            db.commit()
            print(f"Successfully deleted project: {project_name}")
            
            # Log activity (without project_id since project is deleted)
            try:
                activity = ActivityLog(
                    user_id=user_id,
                    action=f"Deleted project: {project_name}",
                    details={"project_id": project_id, "project_name": project_name}
                )
                db.add(activity)
                db.commit()
            except Exception as log_error:
                print(f"Failed to log deletion activity: {log_error}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting project {project_id}: {e}")
            db.rollback()
            return False