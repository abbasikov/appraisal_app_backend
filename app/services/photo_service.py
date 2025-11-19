import os
import shutil
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS

from app.models.photo import Photo
from app.models.activity_log import ActivityLog
from app.services.dropbox_service import DropboxService

class PhotoService:
    
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
                    # Process image
                    exif_date = PhotoService.extract_exif_date(local_path)
                    width, height = PhotoService.get_image_dimensions(local_path)
                    thumbnail_path = PhotoService.create_thumbnail(local_path, project_id)
                    
                    # Create photo record
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
                        # Extract EXIF data with improved method
                        exif_date = PhotoService.extract_exif_date(local_path)
                        
                        # Get image dimensions
                        width, height = PhotoService.get_image_dimensions(local_path)
                        
                        # Generate thumbnail with unique naming
                        thumbnail_path = PhotoService.create_thumbnail(local_path, project_id)
                        
                        # Create photo record with folder tracking
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
            
            # Sort imported photos chronologically by EXIF date
            imported_photos.sort(key=lambda p: p.exif_date or datetime.min)
            
            # Update sort_order based on chronological order
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
        """Extract date taken from EXIF data using modern PIL approach"""
        try:
            with Image.open(image_path) as image:
                # Get EXIF data using the modern approach
                exif_dict = image.getexif()
                
                if exif_dict:
                    # Try different EXIF date tags in order of preference
                    date_tags = [
                        'DateTimeOriginal',      # Camera's date when photo was taken
                        'DateTime',              # File modification date
                        'DateTimeDigitized'      # Date when photo was digitized
                    ]
                    
                    for tag_name in date_tags:
                        # Get the tag ID for the tag name
                        tag_id = None
                        for tag, name in ExifTags.TAGS.items():
                            if name == tag_name:
                                tag_id = tag
                                break
                        
                        if tag_id and tag_id in exif_dict:
                            date_str = exif_dict[tag_id]
                            try:
                                # Parse the EXIF date format: "YYYY:MM:DD HH:MM:SS"
                                return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                            except ValueError:
                                # Try alternative format
                                try:
                                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                except ValueError:
                                    continue
                
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
        """Get photos for a project, ordered by EXIF date (chronological order) with pagination"""
        try:
            query = db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(Photo.exif_date.asc().nullslast(), Photo.sort_order.asc())
            
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