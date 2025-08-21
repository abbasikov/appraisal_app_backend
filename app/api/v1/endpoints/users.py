from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
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