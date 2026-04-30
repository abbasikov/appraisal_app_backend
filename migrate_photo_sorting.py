#!/usr/bin/env python3
"""
Adds sort_timestamp / dropbox_server_modified to photos and backfills sort_timestamp.

Run from appraisal_app_backend:  python migrate_photo_sorting.py
Requires DATABASE_URL (same .env as the app).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from app.db.database import engine, SessionLocal
    from app.models.photo import Photo
    from app.services.photo_service import PhotoService

    ddl = """
    ALTER TABLE photos ADD COLUMN IF NOT EXISTS sort_timestamp TIMESTAMP WITH TIME ZONE;
    ALTER TABLE photos ADD COLUMN IF NOT EXISTS dropbox_server_modified TIMESTAMP WITH TIME ZONE;
    CREATE INDEX IF NOT EXISTS idx_photos_project_sort
        ON photos (project_id, sort_timestamp, id)
        WHERE is_deleted = FALSE;
    """
    with engine.begin() as conn:
        for stmt in ddl.strip().split(";"):
            stmt = stmt.strip()
            if not stmt:
                continue
            conn.execute(text(stmt))
    print("✅ DDL applied (columns + index)")

    db = SessionLocal()
    try:
        rows = db.query(Photo).filter(Photo.is_deleted == False).all()
        updated = 0
        for p in rows:
            st = PhotoService.compute_sort_timestamp(
                exif_date=p.exif_date,
                original_filename=p.original_filename or "",
                dropbox_server_modified=p.dropbox_server_modified,
                ingest_fallback=p.created_at,
            )
            if p.sort_timestamp != st:
                p.sort_timestamp = st
                updated += 1
        db.commit()
        print(f"✅ Backfill complete: updated {updated} / {len(rows)} photos")
    finally:
        db.close()


if __name__ == "__main__":
    main()
