#!/usr/bin/env python3
"""
One-off script to regenerate thumbnails for existing photos.
Fixes sideways images by re-running thumbnail creation with EXIF orientation applied.

Usage:
  cd appraisal_app_backend
  python regenerate_thumbnails.py              # all projects
  python regenerate_thumbnails.py --project 5 # only project_id 5

Optional:
  --dry-run   Print what would be done without writing to DB or disk.
"""

import os
import sys
import argparse
from typing import Optional

# Ensure app is importable when run from backend root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.photo import Photo
from app.services.photo_service import PhotoService


def regenerate_thumbnails(project_id: Optional[int] = None, dry_run: bool = False) -> None:
    db = SessionLocal()
    try:
        query = db.query(Photo).filter(Photo.is_deleted == False)
        if project_id is not None:
            query = query.filter(Photo.project_id == project_id)
        photos = query.all()

        if not photos:
            scope = f"project_id={project_id}" if project_id else "all projects"
            print(f"No photos found for {scope}.")
            return

        scope = f"project {project_id}" if project_id else "all projects"
        print(f"Regenerating thumbnails for {len(photos)} photo(s) in {scope}. Dry run={dry_run}")

        ok = 0
        skipped = 0
        failed = 0

        for photo in photos:
            if not photo.file_path or not os.path.isfile(photo.file_path):
                print(f"  ⏭ Skip photo id={photo.id} (file missing): {photo.file_path or 'None'}")
                skipped += 1
                continue

            if dry_run:
                print(f"  [dry-run] Would regenerate: id={photo.id} {photo.original_filename}")
                ok += 1
                continue

            new_path = PhotoService.create_thumbnail(photo.file_path, photo.project_id)
            if not new_path:
                print(f"  ❌ Failed to create thumbnail: id={photo.id} {photo.original_filename}")
                failed += 1
                continue

            old_path = photo.thumbnail_path
            photo.thumbnail_path = new_path
            db.commit()

            if old_path and old_path != new_path and os.path.isfile(old_path):
                try:
                    os.remove(old_path)
                except OSError as e:
                    print(f"  ⚠ Could not remove old thumbnail: {old_path} ({e})")

            ok += 1
            print(f"  ✅ id={photo.id} {photo.original_filename}")

        print(f"\nDone: {ok} regenerated, {skipped} skipped, {failed} failed.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Regenerate photo thumbnails (fix EXIF orientation).")
    parser.add_argument("--project", type=int, default=None, help="Limit to this project_id")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to DB or disk")
    args = parser.parse_args()

    regenerate_thumbnails(project_id=args.project, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
