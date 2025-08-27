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
    def import_photos_from_dropbox(db: Session, project_id: int, dropbox_links: List[str], user_id: int) -> List[Photo]:
        """Import photos from multiple Dropbox links"""
        imported_photos = []
        dropbox_service = DropboxService()
        
        try:
            for link in dropbox_links:
                print(f"🔄 Processing Dropbox link: {link}")
                
                # Validate folder access
                if not dropbox_service.validate_folder_access(link):
                    print(f"❌ Cannot access folder: {link}")
                    continue
                
                # Get files from the shared folder
                files = dropbox_service.list_folder_contents(link)
                print(f"✅ Found {len(files)} files in folder")
                
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
                        print(f"⚠️  Photo {file_info['name']} already exists, skipping...")
                        continue
                    
                    # Create local directory
                    local_dir = f"uploads/projects/{project_id}/photos"
                    os.makedirs(local_dir, exist_ok=True)
                    local_path = os.path.join(local_dir, file_info['name'])
                    
                    print(f"📥 Downloading: {file_info['name']}")
                    
                    # Download file using the correct path from file_info
                    if dropbox_service.download_file(file_info['path'], local_path, link):
                        # Extract EXIF data with improved method
                        exif_date = PhotoService.extract_exif_date(local_path)
                        
                        # Get image dimensions
                        width, height = PhotoService.get_image_dimensions(local_path)
                        
                        # Generate thumbnail with unique naming
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
                            dropbox_file_id=file_info.get('id')
                        )
                        
                        db.add(photo)
                        imported_photos.append(photo)
                        print(f"✅ Imported: {file_info['name']} | Size: {file_info.get('size', 0)} bytes | EXIF Date: {exif_date}")
                    else:
                        print(f"❌ Failed to download: {file_info['name']}")
            
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
            
            return imported_photos
            
        except Exception as e:
            db.rollback()
            print(f"❌ Error importing photos: {e}")
            import traceback
            traceback.print_exc()
            return []
    
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
                
                # Create thumbnail (150x150 max, maintain aspect ratio)
                image.thumbnail((150, 150), Image.Resampling.LANCZOS)
                
                # Always save as JPEG to ensure consistency
                image.save(thumbnail_path, 'JPEG', optimize=True, quality=85)
            
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
    def get_photos_by_project(db: Session, project_id: int) -> List[Photo]:
        """Get all photos for a project, ordered by EXIF date"""
        try:
            return db.query(Photo).filter(
                Photo.project_id == project_id,
                Photo.is_deleted == False
            ).order_by(Photo.exif_date.asc().nullslast(), Photo.sort_order.asc()).all()
        except Exception as e:
            print(f"❌ Error fetching photos: {e}")
            return []
    
    @staticmethod
    def delete_photo(db: Session, photo_id: int, user_id: int) -> bool:
        """Soft delete photo (set is_deleted = True)"""
        try:
            photo = db.query(Photo).filter(Photo.id == photo_id).first()
            if not photo:
                return False
            
            photo.is_deleted = True
            db.commit()
            
            # Log activity
            activity = ActivityLog(
                user_id=user_id,
                action=f"Deleted photo: {photo.original_filename}",
                details={"photo_id": photo_id, "project_id": photo.project_id}
            )
            db.add(activity)
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            print(f"❌ Error deleting photo: {e}")
            return False