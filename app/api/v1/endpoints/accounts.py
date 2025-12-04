from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_user
from app.models.user import User, UserRole
from app.services.account_service import AccountService
from app.services.client_service import ClientService
from app.schemas.account import (
    AccountResponse, 
    AccountCreate, 
    AccountUpdate,
    AccountListResponse
)
from app.schemas.client import ClientCreate, ClientResponse
from app.models.account import AccountType
from typing import Union

router = APIRouter()

@router.get("/", response_model=AccountListResponse)
def list_accounts(
    account_type: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List accounts with filtering"""
    accounts = AccountService.get_accounts(db, account_type, is_active)
    return AccountListResponse(
        accounts=[AccountResponse.model_validate(a) for a in accounts],
        total=len(accounts)
    )

@router.post("/", response_model=Union[AccountResponse, ClientResponse])
def create_account(
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new account or client based on account_type"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # If account_type is 'client', create a client record instead
    print(f"DEBUG: account_type = {account_data.account_type}, AccountType.CLIENT = {AccountType.CLIENT}")
    print(f"DEBUG: Comparison result = {account_data.account_type == AccountType.CLIENT}")
    
    if account_data.account_type == AccountType.CLIENT:
        print("DEBUG: Creating client record instead of account")
        # Convert account data to client data
        client_data = ClientCreate(
            name=account_data.name,
            email=account_data.email,
            phone=account_data.phone,
            address=account_data.address,
            city=account_data.city,
            state=account_data.state,
            zip_code=account_data.zip_code,
            parent_account_id=account_data.parent_account_id,
            notes=account_data.notes
        )
        
        client = ClientService.create_client(db, client_data, current_user.id)
        if not client:
            raise HTTPException(status_code=400, detail="Failed to create client")
        
        print(f"DEBUG: Client created successfully with ID {client.id}")
        return ClientResponse.model_validate(client)
    
    print("DEBUG: Creating regular account")
    
    # Otherwise, create a regular account
    account = AccountService.create_account(db, account_data)
    return AccountResponse.model_validate(account)

@router.get("/{account_id}", response_model=AccountResponse)
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get account details"""
    account = AccountService.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    return AccountResponse.model_validate(account)

@router.put("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: int,
    account_data: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update account"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    account = AccountService.update_account(db, account_id, account_data)
    return AccountResponse.model_validate(account)

@router.delete("/{account_id}")
def delete_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete account"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = AccountService.delete_account(db, account_id)
    if success:
        return {"message": "Account deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete account")

@router.get("/{account_id}/sub-accounts", response_model=List[AccountResponse])
def get_sub_accounts(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get sub-accounts for a parent account"""
    sub_accounts = AccountService.get_sub_accounts(db, account_id)
    return [AccountResponse.model_validate(a) for a in sub_accounts]

@router.post("/{account_id}/sub-accounts", response_model=AccountResponse)
def create_sub_account(
    account_id: int,
    account_data: AccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create sub-account for a parent account"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Create new account data with parent account ID
    account_dict = account_data.model_dump()
    account_dict['parent_account_id'] = account_id
    updated_account_data = AccountCreate(**account_dict)
    
    account = AccountService.create_account(db, updated_account_data)
    return AccountResponse.model_validate(account)

@router.get("/{account_id}/clients", response_model=List[ClientResponse])
def get_account_clients(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get clients for an account"""
    from app.models.client import Client
    clients = db.query(Client).filter(Client.parent_account_id == account_id, Client.is_active == True).all()
    return [ClientResponse.model_validate(c) for c in clients]

@router.post("/{account_id}/clients", response_model=ClientResponse)
def create_account_client(
    account_id: int,
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create client for an account"""
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Create new client data with parent account ID
    client_dict = client_data.model_dump()
    client_dict['parent_account_id'] = account_id
    updated_client_data = ClientCreate(**client_dict)
    
    client = ClientService.create_client(db, updated_client_data, current_user.id)
    if not client:
        raise HTTPException(status_code=400, detail="Failed to create client")
    
    return ClientResponse.model_validate(client)
@router.get("/{account_id}/clients-by-projects")
def get_account_clients_by_projects(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all clients for an account based on project relationships.
    Returns clients with their associated project names for this account.
    A client can appear under multiple accounts if they have projects with different accounts.
    """
    from app.models.project import Project
    from app.models.client import Client
    
    # Query for all projects with this account_id, joined with clients
    results = db.query(
        Client,
        Project.project_name,
        Project.id.label('project_id')
    ).join(
        Project, Client.id == Project.client_id
    ).filter(
        Project.account_id == account_id
    ).all()
    
    # Group clients by client_id with their project names
    clients_dict = {}
    for client, project_name, project_id in results:
        if client.id not in clients_dict:
            clients_dict[client.id] = {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'phone': client.phone,
                'address': client.address,
                'city': client.city,
                'state': client.state,
                'zip_code': client.zip_code,
                'is_active': client.is_active,
                'case_name': client.case_name,
                'projects': []
            }
        clients_dict[client.id]['projects'].append({
            'id': project_id,
            'name': project_name
        })
    
    return list(clients_dict.values())
