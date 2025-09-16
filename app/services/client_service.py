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
            query = db.query(Client).outerjoin(Account, Client.parent_account_id == Account.id).filter(Client.is_active == True)
            
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
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            print(f"Error fetching clients: {e}")
            return []
    
    @staticmethod  
    def get_client_by_id(db: Session, client_id: int) -> Optional[Client]:
        try:
            if not client_id or client_id <= 0:
                return None
            return db.query(Client).filter(Client.id == client_id, Client.is_active == True).first()
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
    def delete_client(db: Session, client_id: int, user_id: int) -> bool:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return False
        
        # Soft delete - set is_active = False
        client.is_active = False
        db.commit()
        
        # Log activity
        activity = ActivityLog(
            user_id=user_id,
            action=f"Deleted client: {client.name}",
            details={"client_id": client_id}
        )
        db.add(activity)
        db.commit()
        
        return True
    