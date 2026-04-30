import os
import re
import shutil
import tempfile
from typing import List, Optional, Tuple, Union
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func
from PIL import Image, ImageOps
from PIL.ExifTags import TAGS as EXIF_TAG_NAMES

from app.models.photo import Photo
from app.models.activity_log import ActivityLog
from app.services.dropbox_service import DropboxService


def _exif_datetime_tag_order() -> Tuple[int, ...]:
    wanted = ('DateTimeOriginal', 'DateTime', 'DateTimeDigitized')
    ids: List[int] = []
    for name in wanted:
        tid = next((k for k, v in EXIF_TAG_NAMES.items() if v == name), None)
        if tid is not None:
            ids.append(tid)
    return tuple(ids)


_EXIF_DATE_TAG_IDS: Tuple[int, ...] = _exif_datetime_tag_order()


class PhotoService:
    
    @staticmethod
    def photo_sort_coalesce():
        """SQL expression used everywhere photos are ordered chronologically."""
        return func.coalesce(Photo.sort_timestamp, Photo.exif_date, Photo.created_at)

    @staticmethod
    def _ensure_utc(dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def parse_dropbox_modified(iso_val: Optional[str]) -> Optional[datetime]:
        if not iso_val or not isinstance(iso_val, str):
            return None
        s = iso_val.strip()
        if not s:
            return None
        if s.endswith('Z'):
            s = s[:-1] + '+00:00'
        try:
            return PhotoService._ensure_utc(datetime.fromisoformat(s))
        except ValueError:
            return None

    @staticmethod
    def parse_date_from_filename(filename: str) -> Optional[datetime]:
        if not filename:
            return None
        stem = os.path.splitext(os.path.basename(filename))[0].strip()
        formats = ('Photo %b %d %Y, %I %M %S %p',)
        for fmt in formats:
            try:
                dt = datetime.strptime(stem, fmt)
                return PhotoService._ensure_utc(dt)
            except ValueError:
                continue
        m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})h(\d{2})m(\d{2})(?:_\d+)?', stem)
        if not m:
            m = re.fullmatch(r'(\d{4})-(\d{2})-(\d{2})-(\d{2})h(\d{2})m(\d{2})\.\d+', stem)
        if m:
            y, mo, d, h, mi, sec = map(int, m.groups()[:6])
            return PhotoService._ensure_utc(datetime(y, mo, d, h, mi, sec))
        return None

    @staticmethod
    def compute_sort_timestamp(
        exif_date: Optional[datetime],
        original_filename: str,
        dropbox_server_modified: Optional[datetime],
        ingest_fallback: Optional[datetime],
    ) -> datetime:
        """Deterministic ordering: EXIF date → parsed filename → Dropbox modified → ingest time."""
        if exif_date:
            return PhotoService._ensure_utc(exif_date)
        fd = PhotoService.parse_date_from_filename(original_filename)
        if fd:
            return fd
        if dropbox_server_modified:
            return PhotoService._ensure_utc(dropbox_server_modified)
        if ingest_fallback:
            return PhotoService._ensure_utc(ingest_fallback)
        return datetime.now(timezone.utc)

    @staticmethod
    def _coerce_exif_date_text(val: Union[str, bytes]) -> Optional[str]:
        if val is None:
            return None
        if isinstance(val, bytes):
            val = val.decode('utf-8', errors='ignore').strip().strip('\x00')
        else:
            val = str(val).strip().strip('\x00')
        return val if val else None

    @staticmethod
    def _datetime_from_exif_string(date_str: str) -> Optional[datetime]:
        for fmt in ("%Y:%m:%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y:%m:%d %H-%M-%S"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _exif_date_from_flat_mapping(mapping) -> Optional[datetime]:
        if not mapping:
            return None
        getter = getattr(mapping, 'get', None)
        for tid in _EXIF_DATE_TAG_IDS:
            raw = getter(tid) if callable(getter) else None
            if raw is None:
                try:
                    raw = mapping[tid]
                except (KeyError, TypeError, IndexError):
                    continue
            text = PhotoService._coerce_exif_date_text(raw)
            if not text:
                continue
            parsed = PhotoService._datetime_from_exif_string(text)
            if parsed:
                return parsed
        return None

    @staticmethod
    def _jpeg_exif_bytes_orientation_normal(img: Image.Image) -> Optional[bytes]:
        """AFTER exif_transpose: pixels are upright; Orientation must be 1 so viewers do not rotate again."""
        try:
            ex = img.getexif()
            if not ex:
                return None
            try:
                ex[274] = 1  # Orientation: horizontal (normal)
            except Exception:
                pass
            out = ex.tobytes()
            return out if out and len(out) >= 8 else None
        except Exception:
            return None

    @staticmethod
    def canonicalize_imported_image(image_path: str) -> None:
        """Apply EXIF transpose to pixels, then save metadata consistent with upright pixels (JPEG: Orientation=1).
        Handles MPO, JPEG, PNG, BMP, TIFF. Skips GIF (palette/animation)."""
        try:
            ext = os.path.splitext(image_path)[1].lower()
            with Image.open(image_path) as img:
                fmt = getattr(img, 'format', None)
                if fmt == 'GIF' or ext == '.gif':
                    return
                if getattr(img, 'n_frames', 1) > 1:
                    return
                img.seek(0)
                img.load()
                img = ImageOps.exif_transpose(img)

                as_jpeg = ext in ('.jpg', '.jpeg') or fmt == 'MPO'
                if as_jpeg:
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    exout = PhotoService._jpeg_exif_bytes_orientation_normal(img)
                    fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                    os.close(fd)
                    try:
                        try:
                            if exout:
                                img.save(temp_path, 'JPEG', quality=92, exif=exout)
                            else:
                                img.save(temp_path, 'JPEG', quality=92)
                        except Exception:
                            img.save(temp_path, 'JPEG', quality=92)
                        os.replace(temp_path, image_path)
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except OSError:
                                pass
                    return

                if ext == '.png' or fmt == 'PNG':
                    fd, temp_path = tempfile.mkstemp(suffix='.png')
                    os.close(fd)
                    try:
                        if img.mode in ('RGBA', 'LA', 'P') or img.mode == 'RGB':
                            img.save(temp_path, 'PNG', optimize=True)
                        else:
                            img.convert('RGB').save(temp_path, 'PNG', optimize=True)
                        os.replace(temp_path, image_path)
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except OSError:
                                pass
                    return

                pil_save = {
                    '.bmp': 'BMP',
                    '.tif': 'TIFF',
                    '.tiff': 'TIFF',
                }.get(ext)
                if pil_save:
                    fd, temp_path = tempfile.mkstemp(suffix=ext)
                    os.close(fd)
                    try:
                        im2 = img.convert('RGB') if img.mode not in ('RGB', 'L') else img
                        im2.save(temp_path, pil_save)
                        os.replace(temp_path, image_path)
                    finally:
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                            except OSError:
                                pass
        except Exception as e:
            print(f"⚠️ Orientation canonicalize skipped for {os.path.basename(image_path)}: {e}")

    @staticmethod
    def import_photos_from_dropbox_batched(db: Session, project_id: int, dropbox_links: List[str], user_id: int, batch_size: int = 10) -> dict:
        """Import photos from Dropbox in batches to avoid timeouts"""
        imported_photos = []
        errors = []
        warnings = []
        dropbox_service = DropboxService()
        
        try:
            # First, get all available files without downloading
            all_files = []
            for link in dropbox_links:
                if not dropbox_service.validate_folder_access(link):
                    error_msg = f"Cannot access Dropbox folder: {link}"
                    errors.append(error_msg)
                    continue
                
                files = dropbox_service.list_folder_contents(link)
                for file_info in files:
                    if PhotoService.is_image_file(file_info['name']):
                        file_info['source_link'] = link
                        all_files.append(file_info)
            
            # Filter out already imported files
            new_files = []
            for file_info in all_files:
                existing = db.query(Photo).filter(
                    Photo.project_id == project_id,
                    Photo.original_filename == file_info['name'],
                    Photo.is_deleted == False
                ).first()
                
                if not existing:
                    new_files.append(file_info)
                else:
                    warnings.append(f"Photo '{file_info['name']}' already exists, skipping")
            
            # Process only the first batch
            files_to_process = new_files[:batch_size]
            
            for file_info in files_to_process:
                # Create local directory
                local_dir = f"uploads/projects/{project_id}/photos"
                os.makedirs(local_dir, exist_ok=True)
                local_path = os.path.join(local_dir, file_info['name'])
                
                # Download file
                if file_info.get('from_zip', False):
                    success = PhotoService.download_file_from_zip(file_info['source_link'], file_info['path'], local_path)
                else:
                    success = dropbox_service.download_file(file_info['path'], local_path, file_info['source_link'])
                
                if success:
                    drop_mod = PhotoService.parse_dropbox_modified(file_info.get('modified'))
                    ingest_fallback = datetime.now(timezone.utc)
                    PhotoService.canonicalize_imported_image(local_path)
                    exif_date = PhotoService.extract_exif_date(local_path)
                    sort_timestamp = PhotoService.compute_sort_timestamp(
                        exif_date, file_info['name'], drop_mod, ingest_fallback
                    )
                    width, height = PhotoService.get_image_dimensions(local_path)
                    thumbnail_path = PhotoService.create_thumbnail(local_path, project_id)

                    photo = Photo(
                        project_id=project_id,
                        original_filename=file_info['name'],
                        file_path=local_path,
                        thumbnail_path=thumbnail_path,
                        file_size=file_info.get('size', 0),
                        mime_type=PhotoService.get_mime_type(file_info['name']),
                        width=width,
                        height=height,
                        exif_date=exif_date,
                        sort_timestamp=sort_timestamp,
                        dropbox_server_modified=drop_mod,
                        sort_order=len(imported_photos) + 1,
                        dropbox_file_id=file_info.get('id'),
                        dropbox_folder_path=file_info.get('folder_path', '/'),
                        source_folder_link=file_info['source_link']
                    )
                    
                    db.add(photo)
                    imported_photos.append(photo)
                else:
                    errors.append(f"Failed to download '{file_info['name']}'")
            
            # Commit batch
            db.commit()
            
            # Log activity
            if imported_photos:
                activity = ActivityLog(
                    user_id=user_id,
                    action=f"Imported {len(imported_photos)} photos (batch) to project {project_id}",
                    details={"project_id": project_id, "photo_count": len(imported_photos)}
                )
                db.add(activity)
                db.commit()
            
            has_more = len(new_files) > batch_size
            
            return {
                "success": True,
                "imported_photos": imported_photos,
                "imported_count": len(imported_photos),
                "total_found": len(all_files),
                "errors": errors,
                "warnings": warnings,
                "has_more": has_more,
                "message": f"Imported {len(imported_photos)} photos" + (" (more available)" if has_more else "")
            }
            
        except Exception as e:
            db.rollback()
            error_msg = f"Batch import failed: {str(e)}"
            return {
                "success": False,
                "imported_photos": [],
                "imported_count": 0,
                "total_found": 0,
                "errors": [error_msg],
                "warnings": warnings,
                "has_more": False,
                "message": error_msg
            }
    
    @staticmethod
    def import_photos_from_dropbox(db: Session, project_id: int, dropbox_links: List[str], user_id: int) -> dict:
        """Import photos from multiple Dropbox links - returns dict with results and errors"""
        imported_photos = []
        errors = []
        warnings = []
        dropbox_service = DropboxService()
        
        try:
            for link in dropbox_links:
                print(f"🔄 Processing Dropbox link: {link}")
                
                # Validate folder access
                if not dropbox_service.validate_folder_access(link):
                    error_msg = f"Cannot access Dropbox folder: {link}. Please check if the link is valid and accessible."
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    continue
                
                # Get files from the shared folder
                files = dropbox_service.list_folder_contents(link)
                print(f"✅ Found {len(files)} files in folder")
                
                if not files:
                    warning_msg = f"No image files found in Dropbox folder: {link}"
                    warnings.append(warning_msg)
                    continue
                
                for file_info in files:
                    if not PhotoService.is_image_file(file_info['name']):
                        continue
                    
                    # Check if photo already exists
                    existing = db.query(Photo).filter(
                        Photo.project_id == project_id,
                        Photo.original_filename == file_info['name'],
                        Photo.is_deleted == False
                    ).first()
                    
                    if existing:
                        warning_msg = f"Photo '{file_info['name']}' already exists in project, skipping"
                        print(f"⚠️  {warning_msg}")
                        warnings.append(warning_msg)
                        continue
                    
                    # Create local directory
                    local_dir = f"uploads/projects/{project_id}/photos"
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, file_info['name'])
                    
                    print(f"📥 Downloading: {file_info['name']}")
                    
                    # Handle files from ZIP extraction differently
                    if file_info.get('from_zip', False):
                        # For ZIP files, download the entire ZIP and extract the specific file
                        success = PhotoService.download_file_from_zip(link, file_info['path'], local_path)
                    else:
                        # For regular API files, use normal download
                        success = dropbox_service.download_file(file_info['path'], local_path, link)
                    
                    if success:
                        drop_mod = PhotoService.parse_dropbox_modified(file_info.get('modified'))
                        ingest_fallback = datetime.now(timezone.utc)
                        PhotoService.canonicalize_imported_image(local_path)
                        exif_date = PhotoService.extract_exif_date(local_path)
                        sort_timestamp = PhotoService.compute_sort_timestamp(
                            exif_date, file_info['name'], drop_mod, ingest_fallback
                        )
                        width, height = PhotoService.get_image_dimensions(local_path)
                        thumbnail_path = PhotoService.create_thumbnail(local_path, project_id)

                        photo = Photo(
                            project_id=project_id,
                            original_filename=file_info['name'],
                            file_path=local_path,
                            thumbnail_path=thumbnail_path,
                            file_size=file_info.get('size', 0),
                            mime_type=PhotoService.get_mime_type(file_info['name']),
                            width=width,
                            height=height,
                            exif_date=exif_date,
                            sort_timestamp=sort_timestamp,
                            dropbox_server_modified=drop_mod,
                            sort_order=len(imported_photos) + 1,
                            dropbox_file_id=file_info.get('id'),
                            dropbox_folder_path=file_info.get('folder_path', '/'),
                            source_folder_link=link
                        )
                        
                        db.add(photo)
                        imported_photos.append(photo)
                        print(f"✅ Imported: {file_info['name']} | Size: {file_info.get('size', 0)} bytes | EXIF Date: {exif_date}")
                    else:
                        error_msg = f"Failed to download '{file_info['name']}' from Dropbox. The file may be corrupted or inaccessible."
                        print(f"❌ {error_msg}")
                        errors.append(error_msg)
            
            imported_photos.sort(key=lambda p: (p.sort_timestamp, p.id))
            for i, photo in enumerate(imported_photos):
                photo.sort_order = i + 1
            
            db.commit()
            
            # Log activity
            if imported_photos:
                activity = ActivityLog(
                    user_id=user_id,
                    action=f"Imported {len(imported_photos)} photos to project {project_id}",
                    details={"project_id": project_id, "photo_count": len(imported_photos)}
                )
                db.add(activity)
                db.commit()
                print(f"🎉 Successfully imported {len(imported_photos)} photos")
            
            return {
                "success": True,
                "imported_photos": imported_photos,
                "imported_count": len(imported_photos),
                "errors": errors,
                "warnings": warnings,
                "message": f"Successfully imported {len(imported_photos)} photos" + 
                          (f" with {len(warnings)} warnings" if warnings else "") +
                          (f" and {len(errors)} errors" if errors else "")
            }
            
        except Exception as e:
            db.rollback()
            error_msg = f"Critical error during photo import: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "imported_photos": [],
                "imported_count": 0,
                "errors": [error_msg],
                "warnings": warnings,
                "message": f"Photo import failed: {str(e)}"
            }
    
    @staticmethod
    def extract_exif_date(image_path: str) -> Optional[datetime]:
        """Extract date taken from EXIF (IFD0 + Exif sub-IFD); handles bytes values."""
        try:
            with Image.open(image_path) as image:
                exif_top = image.getexif()
                dt = PhotoService._exif_date_from_flat_mapping(exif_top)
                if dt:
                    return dt
                try:
                    from PIL.ExifTags import IFD
                    if exif_top:
                        sub = exif_top.get_ifd(IFD.Exif)
                        dt = PhotoService._exif_date_from_flat_mapping(sub)
                        if dt:
                            return dt
                except Exception:
                    pass
                print(f"⚠️  No EXIF date found for: {os.path.basename(image_path)}")
                return None
        except Exception as e:
            print(f"❌ Error extracting EXIF date from {os.path.basename(image_path)}: {e}")
            return None
    
    @staticmethod
    def get_image_dimensions(image_path: str) -> tuple:
        """Get image width and height"""
        try:
            with Image.open(image_path) as image:
                return image.size  # Returns (width, height)
        except Exception as e:
            print(f"❌ Error getting dimensions for {os.path.basename(image_path)}: {e}")
            return None, None
    
    @staticmethod
    def create_thumbnail(image_path: str, project_id: int) -> Optional[str]:
        """Create thumbnail for image with unique naming"""
        try:
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)
            
            # Create unique thumbnail name using timestamp to avoid conflicts
            import time
            timestamp = str(int(time.time() * 1000))  # milliseconds for uniqueness
            thumbnail_name = f"{name}_{timestamp}_thumb.jpg"  # Always use .jpg for thumbnails
            
            thumbnail_dir = f"uploads/projects/{project_id}/thumbnails"
            os.makedirs(thumbnail_dir, exist_ok=True)
            thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
            
            # Ensure we don't overwrite existing thumbnails
            if os.path.exists(thumbnail_path):
                timestamp = str(int(time.time() * 1000))
                thumbnail_name = f"{name}_{timestamp}_thumb.jpg"
                thumbnail_path = os.path.join(thumbnail_dir, thumbnail_name)
            
            with Image.open(image_path) as image:
                # Apply EXIF orientation so thumbnails display right-side-up (e.g. from phone cameras)
                image = ImageOps.exif_transpose(image)
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Create thumbnail with correct specifications from requirements
                # Horizontal (72 DPI): 180px (h) × 240px (w)
                # Vertical (72 DPI): 180px (h) × 136px (w)
                original_width, original_height = image.size
                
                if original_width > original_height:  # Horizontal image
                    target_size = (240, 180)
                else:  # Vertical image
                    target_size = (136, 180)
                
                # Resize maintaining aspect ratio within target dimensions
                image.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Always save as JPEG to ensure consistency with 72 DPI
                image.save(thumbnail_path, 'JPEG', optimize=True, quality=85, dpi=(72, 72))
            
            print(f"✅ Created unique thumbnail: {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            print(f"❌ Error creating thumbnail for {os.path.basename(image_path)}: {e}")
            return None
    
    @staticmethod
    def is_image_file(filename: str) -> bool:
        """Check if file is a supported image format"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif']
    
    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type from file extension"""
        ext = os.path.splitext(filename)[1].lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff',
            '.tif': 'image/tiff'
        }
        return mime_types.get(ext, 'image/jpeg')
    
    @staticmethod
    def get_photos_by_project(db: Session, project_id: int, skip: int = 0, limit: int = None) -> List[Photo]:
        """Get photos for a project, ordered chronologically (sort_timestamp → EXIF → created_at) with pagination"""
        try:
            query = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(PhotoService.photo_sort_coalesce().asc(), Photo.id.asc())
            
            if limit is not None:
                query = query.offset(skip).limit(limit)
            
            return query.all()
        except Exception as e:
            print(f"❌ Error fetching photos: {e}")
            return []
    
    @staticmethod
    def get_photos_by_project_with_pagination(db: Session, project_id: int, skip: int = 0, limit: int = 20) -> dict:
        """Get photos for a project with pagination metadata"""
        try:
            # Get total count
            total_count = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).count()
            
            # Get paginated results
            photos = PhotoService.get_photos_by_project(db, project_id, skip, limit)
            
            # Check if there are more photos
            has_more = (skip + limit) < total_count if limit else False
            
            return {
                "photos": photos,
                "total_count": total_count,
                "skip": skip,
                "limit": limit,
                "has_more": has_more
            }
        except Exception as e:
            print(f"❌ Error fetching paginated photos: {e}")
            return {
                "photos": [],
                "total_count": 0,
                "skip": skip,
                "limit": limit,
                "has_more": False
            }
    
    @staticmethod
    def download_file_from_zip(share_link: str, zip_file_path: str, local_path: str) -> bool:
        """Download a specific file from a Dropbox ZIP archive"""
        try:
            import requests
            import zipfile
            import tempfile
            
            # Convert to direct download link
            if 'dl=0' in share_link:
                direct_link = share_link.replace('dl=0', 'dl=1')
            elif '?' in share_link:
                direct_link = share_link + '&dl=1'
            else:
                direct_link = share_link + '?dl=1'
            
            filename = os.path.basename(zip_file_path)
            print(f"📦 Downloading ZIP to extract: {filename}")
            
            # Download ZIP file
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(direct_link, stream=True, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                temp_zip_path = temp_file.name
            
            # Extract the specific file
            if zipfile.is_zipfile(temp_zip_path):
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    # Find the specific file in the ZIP
                    for zip_info in zip_ref.infolist():
                        if zip_info.filename == zip_file_path:
                            # Extract the specific file
                            with zip_ref.open(zip_info) as source, open(local_path, 'wb') as target:
                                target.write(source.read())
                            
                            # Clean up temp file
                            os.unlink(temp_zip_path)
                            print(f"✅ Successfully extracted {filename} from ZIP")
                            return True
                    
                    print(f"❌ File {zip_file_path} not found in ZIP")
            else:
                print(f"❌ Downloaded file is not a valid ZIP")
            
            # Clean up temp file
            os.unlink(temp_zip_path)
            return False
            
        except Exception as e:
            print(f"❌ Error downloading file from ZIP: {e}")
            return False
    
    @staticmethod
    def delete_photo(db: Session, photo_id: int, user_id: int) -> bool:
        """Soft delete photo (set is_deleted = True) and delete associated appraisal items"""
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False
            
            # Import here to avoid circular dependency
            from app.models.appraisal_item import AppraisalItem
            
            # Delete any appraisal items referencing this photo
            deleted_items = db.query(AppraisalItem).filter(
                AppraisalItem.photo_id == photo_id
            ).delete(synchronize_session=False)
            
            # Soft delete the photo
            photo.is_deleted = True
            db.commit()
            
            # Log activity
            activity = ActivityLog(
                user_id=user_id,
                action=f"Deleted photo: {photo.original_filename}",
                details={
                    "photo_id": photo_id, 
                    "project_id": photo.project_id,
                    "deleted_appraisal_items": deleted_items
                }
            )
            db.add(activity)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Error deleting photo: {e}")
            return False