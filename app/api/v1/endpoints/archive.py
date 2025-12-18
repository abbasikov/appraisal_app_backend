from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.archive import ArchiveCreate, ArchiveUpdate, ArchiveResponse
from app.services.archive_service import ArchiveService
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ArchiveResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_archive(
    archive: ArchiveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create or update an archive record for a client-account pair."""
    db_archive = ArchiveService.create_or_update_archive(
        db,
        archive.client_id,
        archive.account_id,
        archive.archive_status
    )
    if not db_archive:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create or update archive"
        )
    return db_archive


@router.get("/client/{client_id}/account/{account_id}", response_model=ArchiveResponse)
async def get_archive_status(
    client_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get archive status for a specific client-account pair."""
    archive = ArchiveService.get_archive_by_client_and_account(db, client_id, account_id)
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive record not found for this client-account pair"
        )
    return archive


@router.get("/check/{client_id}/{account_id}")
async def check_is_archived(
    client_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a client-account pair is archived.
    Returns: {"is_archived": true/false}
    """
    is_archived = ArchiveService.is_archived(db, client_id, account_id)
    return {"is_archived": is_archived}


@router.get("/client/{client_id}", response_model=List[ArchiveResponse])
async def get_client_archives(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all archive records for a specific client."""
    archives = ArchiveService.get_archives_for_client(db, client_id)
    return archives


@router.get("/account/{account_id}", response_model=List[ArchiveResponse])
async def get_account_archives(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all archive records for a specific account."""
    archives = ArchiveService.get_archives_for_account(db, account_id)
    return archives


@router.put("/{client_id}/{account_id}", response_model=ArchiveResponse)
async def update_archive_status(
    client_id: int,
    account_id: int,
    archive_update: ArchiveUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update the archive status for a client-account pair."""
    archive = ArchiveService.update_archive(db, client_id, account_id, archive_update)
    if not archive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive record not found"
        )
    return archive


@router.delete("/{client_id}/{account_id}")
async def delete_archive(
    client_id: int,
    account_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an archive record for a client-account pair."""
    success = ArchiveService.delete_archive(db, client_id, account_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archive record not found"
        )
    return {"message": "Archive record deleted successfully"}
