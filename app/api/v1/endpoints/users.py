from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserInvite, UserRoleUpdate, PasswordSetup
from app.services.user_service import UserService
from app.models.user import UserRole
from typing import List
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    updated_user = UserService.update_user(db, current_user.id, user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )
    return updated_user

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    users = UserService.get_users(db, skip, limit)
    return users

@router.post("/invite", response_model=UserResponse)
async def invite_user(
    user_invite: UserInvite,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if not UserService.can_invite_role(current_user.role, user_invite.role):
        raise HTTPException(status_code=403, detail=f"Cannot invite {user_invite.role.value} users")
    
    try:
        user = UserService.invite_user(db, user_invite, current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admin can change user roles")
    
    try:
        user = UserService.update_user_role(db, user_id, role_update.role, current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not UserService.can_delete_user(current_user.role, target_user.role):
        raise HTTPException(status_code=403, detail=f"Cannot delete {target_user.role.value} users")
    
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    try:
        UserService.delete_user(db, user_id, current_user.id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/setup-password")
async def setup_password(
    password_setup: PasswordSetup,
    db: Session = Depends(get_db)
):
    try:
        user = UserService.setup_password(db, password_setup.token, password_setup.password)
        return {"message": "Password set successfully", "user_id": user.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))