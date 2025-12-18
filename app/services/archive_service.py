from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.models.archive import Archive
from app.schemas.archive import ArchiveCreate, ArchiveUpdate
from typing import Optional, List


class ArchiveService:
    @staticmethod
    def create_or_update_archive(
        db: Session, 
        client_id: int, 
        account_id: int, 
        archive_status: bool = True
    ) -> Optional[Archive]:
        """
        Create a new archive record or update if it already exists for the client-account pair.
        This ensures only one record exists per unique client-account combination.
        """
        try:
            # Try to find existing archive for this client-account pair
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()

            if archive:
                # Update existing archive
                archive.archive_status = archive_status
                db.commit()
                db.refresh(archive)
                return archive
            else:
                # Create new archive
                new_archive = Archive(
                    client_id=client_id,
                    account_id=account_id,
                    archive_status=archive_status
                )
                db.add(new_archive)
                db.commit()
                db.refresh(new_archive)
                return new_archive
        except IntegrityError:
            db.rollback()
            # Unique constraint violation - update instead
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()
            if archive:
                archive.archive_status = archive_status
                db.commit()
                db.refresh(archive)
                return archive
            return None
        except Exception as e:
            db.rollback()
            print(f"Error creating/updating archive: {e}")
            return None

    @staticmethod
    def get_archive_by_client_and_account(
        db: Session, 
        client_id: int, 
        account_id: int
    ) -> Optional[Archive]:
        """
        Retrieve archive status for a specific client-account pair.
        """
        try:
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()
            return archive
        except Exception as e:
            print(f"Error fetching archive: {e}")
            return None

    @staticmethod
    def is_archived(db: Session, client_id: int, account_id: int) -> bool:
        """
        Check if a client-account pair is archived (archive_status = False).
        Returns True if archived, False otherwise.
        """
        try:
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()
            
            if archive and archive.archive_status == False:
                return True
            return False
        except Exception as e:
            print(f"Error checking archive status: {e}")
            return False

    @staticmethod
    def get_archives_for_client(db: Session, client_id: int) -> List[Archive]:
        """
        Retrieve all archive records for a specific client.
        """
        try:
            archives = db.query(Archive).filter(Archive.client_id == client_id).all()
            return archives if archives else []
        except Exception as e:
            print(f"Error fetching archives for client: {e}")
            return []

    @staticmethod
    def get_archives_for_account(db: Session, account_id: int) -> List[Archive]:
        """
        Retrieve all archive records for a specific account.
        """
        try:
            archives = db.query(Archive).filter(Archive.account_id == account_id).all()
            return archives if archives else []
        except Exception as e:
            print(f"Error fetching archives for account: {e}")
            return []

    @staticmethod
    def update_archive(
        db: Session, 
        client_id: int, 
        account_id: int, 
        archive_update: ArchiveUpdate
    ) -> Optional[Archive]:
        """
        Update the archive status for a client-account pair.
        """
        try:
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()
            
            if not archive:
                return None
            
            archive.archive_status = archive_update.archive_status
            db.commit()
            db.refresh(archive)
            return archive
        except Exception as e:
            db.rollback()
            print(f"Error updating archive: {e}")
            return None

    @staticmethod
    def delete_archive(db: Session, client_id: int, account_id: int) -> bool:
        """
        Delete an archive record (rarely used, but available if needed).
        """
        try:
            archive = db.query(Archive).filter(
                Archive.client_id == client_id,
                Archive.account_id == account_id
            ).first()
            
            if not archive:
                return False
            
            db.delete(archive)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(f"Error deleting archive: {e}")
            return False
