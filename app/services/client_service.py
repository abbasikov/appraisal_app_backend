from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from app.models.client import Client
from app.models.activity_log import ActivityLog
from app.schemas.client import ClientCreate, ClientUpdate
from typing import Optional, List

class ClientService:
    @staticmethod
    def create_client(db: Session, client: ClientCreate, user_id: int) -> Optional[Client]:
        try:
            # Validate required fields
            if not client.name or not client.name.strip():
                return None
                
            db_client = Client(
                name=client.name.strip(),
                parent_account_id=client.parent_account_id,
                company=client.company.strip() if client.company else None,
                email=client.email.strip() if client.email else None,
                phone=client.phone.strip() if client.phone else None,
                address=client.address.strip() if client.address else None,
                city=client.city.strip() if client.city else None,
                state=client.state.strip() if client.state else None,
                zip_code=client.zip_code.strip() if client.zip_code else None,
                attorney_name=client.attorney_name.strip() if client.attorney_name else None,
                attorney_email=client.attorney_email.strip() if client.attorney_email else None,
                attorney_phone=client.attorney_phone.strip() if client.attorney_phone else None,
                case_name=client.case_name.strip() if client.case_name else None,
                case_number=client.case_number.strip() if client.case_number else None,
                date_of_death=client.date_of_death,
                notes=client.notes.strip() if client.notes else None
            )
            db.add(db_client)
            db.commit()
            db.refresh(db_client)
            
            # Log activity
            try:
                activity = ActivityLog(
                    user_id=user_id,
                    action=f"Created client: {client.name}",
                    details={"client_id": db_client.id, "client_name": client.name}
                )
                db.add(activity)
                db.commit()
            except Exception as log_error:
                print(f"Warning: Failed to log activity: {log_error}")
            
            return db_client
        except Exception as e:
            db.rollback()
            print(f"Error creating client: {e}")
            return None
    
    @staticmethod
    def get_clients(db: Session, skip: int = 0, limit: int = 100, search: str = None) -> List[Client]:
        try:
            from app.models.account import Account
            from sqlalchemy.orm import joinedload
            
            query = db.query(Client).options(joinedload(Client.parent_account)).filter(Client.is_active == True)
            
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                query = query.filter(
                    or_(
                        Client.name.ilike(search_term),
                        Client.company.ilike(search_term),
                        Client.case_name.ilike(search_term),
                        Client.attorney_name.ilike(search_term)
                    )
                )
            
            clients = query.offset(skip).limit(limit).all()
            
            # Manually set parent_account fields for response
            for client in clients:
                if client.parent_account:
                    client.parent_account_name = client.parent_account.name
                    client.parent_account_type = client.parent_account.account_type.value if hasattr(client.parent_account.account_type, 'value') else client.parent_account.account_type
                    client.parent_account_address = client.parent_account.address
                    client.parent_account_city = client.parent_account.city
                    client.parent_account_state = client.parent_account.state
                    client.parent_account_zip = client.parent_account.zip_code
                else:
                    client.parent_account_name = None
                    client.parent_account_type = None
                    client.parent_account_address = None
                    client.parent_account_city = None
                    client.parent_account_state = None
                    client.parent_account_zip = None
            
            return clients
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return []
    
    @staticmethod  
    def get_client_by_id(db: Session, client_id: int) -> Optional[Client]:
        try:
            if not client_id or client_id <= 0:
                return None
            from sqlalchemy.orm import joinedload
            
            client = db.query(Client).options(joinedload(Client.parent_account)).filter(Client.id == client_id, Client.is_active == True).first()
            
            if client and client.parent_account:
                client.parent_account_name = client.parent_account.name
                client.parent_account_type = client.parent_account.account_type.value if hasattr(client.parent_account.account_type, 'value') else client.parent_account.account_type
                client.parent_account_address = client.parent_account.address
                client.parent_account_city = client.parent_account.city
                client.parent_account_state = client.parent_account.state
                client.parent_account_zip = client.parent_account.zip_code
            elif client:
                client.parent_account_name = None
                client.parent_account_type = None
                client.parent_account_address = None
                client.parent_account_city = None
                client.parent_account_state = None
                client.parent_account_zip = None
                
            return client
        except Exception as e:
            print(f"Error fetching client {client_id}: {e}")
            return None
    
    @staticmethod
    def update_client(db: Session, client_id: int, client_update: ClientUpdate, user_id: int) -> Optional[Client]:
        client = db.query(Client).filter(Client.id == client_id, Client.is_active == True).first()
        if not client:
            return None
        
        update_data = client_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(client, field, value)
        
        db.commit()
        db.refresh(client)
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            action=f"Updated client: {client.name}",
            details={"client_id": client_id, "updated_fields": list(update_data.keys())}
        )
        db.add(activity)
        db.commit()
        
        return client
    
    @staticmethod
    def delete_client(db: Session, client_id: int, user_id: int, account_id: int = None) -> bool:
        """
        Delete/archive a client for a specific account (attorney).
        Only the specified client-account pair is archived, not all pairs.
        Client remains active in the system (is_active stays True).
        
        Args:
            db: Database session
            client_id: ID of the client to archive
            user_id: ID of the user performing the deletion
            account_id: ID of the account/attorney archiving this client-pair.
                       If provided, only this pair is archived.
                       If not provided, archives all pairs.
        """
        from app.services.archive_service import ArchiveService
        from app.models.project import Project
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False
        
        archived_pairs = set()
        
        if account_id:
            # Archive only the specific client-account pair
            ArchiveService.create_or_update_archive(
                db, 
                client_id, 
                account_id, 
                archive_status=False
            )
            archived_pairs.add((client_id, account_id))
        else:
            # If no specific account provided, archive all pairs for this client
            projects = db.query(Project).filter(Project.client_id == client_id).all()
            for project in projects:
                if project.account_id:
                    pair_key = (client_id, project.account_id)
                    if pair_key not in archived_pairs:
                        ArchiveService.create_or_update_archive(
                            db, 
                            client_id, 
                            project.account_id, 
                            archive_status=False
                        )
                        archived_pairs.add(pair_key)
        
        # NOTE: Client remains active (is_active stays True)
        # Only the client-account pair is archived in the archive table
        # Client is NOT soft-deleted
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            action=f"Archived client-account pair: Client {client.name} (ID: {client_id}), Account: {account_id}",
            details={"client_id": client_id, "account_id": account_id, "archived_pairs": list(archived_pairs)}
        )
        db.add(activity)
        db.commit()
        
        return True
    