import dropbox
import os
import re
from typing import List, Optional, Dict
from app.core.config import settings

class DropboxService:
    def __init__(self):
        self.client = dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
    
    @staticmethod
    def extract_folder_id_from_link(share_link: str) -> Optional[str]:
        """Extract folder ID from Dropbox share URL"""
        try:
            # Pattern for Dropbox share links
            patterns = [
                r'dropbox\.com/sh/([a-zA-Z0-9_-]+)',
                r'dropbox\.com/s/([a-zA-Z0-9_-]+)',
                r'dropbox\.com/scl/fo/([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, share_link)
                if match:
                    return match.group(1)
            return None
        except Exception:
            return None
    
    def validate_folder_access(self, share_link: str) -> bool:
        """Check if shared folder is accessible"""
        try:
            # For shared folders, use sharing API
            shared_link_metadata = self.client.sharing_get_shared_link_metadata(share_link)
            return True
        except Exception as e:
            print(f"Folder access error: {e}")
            return False
    
    def list_folder_contents(self, share_link: str) -> List[Dict]:
        """List all images in shared folder using proper Dropbox API"""
        try:
            files = []
            print(f"Listing folder contents for: {share_link}")
            
            # Use files_list_folder with shared_link parameter (as per Dropbox API docs)
            shared_link_obj = dropbox.files.SharedLink(url=share_link)
            result = self.client.files_list_folder(path="", shared_link=shared_link_obj)
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    # Check if file is an image
                    file_ext = os.path.splitext(entry.name)[1].lower()
                    if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                        print(f"Found image: {entry.name} (ID: {entry.id})")
                        files.append({
                            'name': entry.name,
                            'path': entry.path_lower,
                            'size': entry.size,
                            'modified': entry.server_modified.isoformat() if entry.server_modified else None,
                            'id': entry.id,
                            'rev': getattr(entry, 'rev', None)  # For caching
                        })
            
            print(f"Total images found: {len(files)}")
            return files
        except Exception as e:
            print(f"Error listing folder contents: {e}")
            return []
    
    def download_file(self, file_path: str, local_path: str, share_link: str = None) -> bool:
        """Download file from Dropbox to local storage"""
        try:
            import requests
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            if share_link:
                # Convert Dropbox share link to direct download link
                # Change dl=0 to dl=1 for direct download
                if 'dl=0' in share_link:
                    direct_link = share_link.replace('dl=0', 'dl=1')
                elif '?' in share_link:
                    direct_link = share_link + '&dl=1'
                else:
                    direct_link = share_link + '?dl=1'
                
                # Extract filename from file_path
                filename = os.path.basename(file_path)
                
                # Use Dropbox API to download from shared link
                try:
                    print(f"Downloading {filename} from shared folder...")
                    
                    # Use the sharing API to download the file
                    shared_link_obj = dropbox.files.SharedLink(url=share_link)
                    metadata, response = self.client.sharing_get_shared_link_file(
                        url=share_link, 
                        path=file_path
                    )
                    
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"✅ Successfully downloaded {filename}")
                    return True
                    
                except Exception as e:
                    print(f"Shared API download failed for {filename}: {e}")
                    
                    # Fallback: try direct HTTP download
                    try:
                        print(f"Trying direct download for {filename}...")
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        }
                        response = requests.get(direct_link, stream=True, timeout=30, headers=headers)
                        response.raise_for_status()
                        
                        # Check content type
                        content_type = response.headers.get('content-type', '')
                        if 'text/html' in content_type:
                            print(f"Got HTML instead of image for {filename}")
                            return False
                        
                        # Download to temporary file first
                        temp_path = local_path + '.tmp'
                        with open(temp_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                        
                        # Check if it's a ZIP file (Dropbox sometimes returns ZIP)
                        import zipfile
                        try:
                            if zipfile.is_zipfile(temp_path):
                                print(f"Extracting {filename} from ZIP archive...")
                                with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                                    # Find the SPECIFIC file we want, not just any image
                                    target_file_found = False
                                    
                                    for zip_info in zip_ref.infolist():
                                        # Check if this is the exact file we're looking for
                                        zip_filename = os.path.basename(zip_info.filename).lower()
                                        target_filename = filename.lower()
                                        
                                        print(f"🔍 ZIP contains: {zip_info.filename}")
                                        print(f"🎯 Looking for: {filename}")
                                        
                                        # Match by exact filename (case insensitive)
                                        if zip_filename == target_filename:
                                            print(f"✅ Found exact match: {zip_info.filename}")
                                            with zip_ref.open(zip_info) as source, open(local_path, 'wb') as target:
                                                target.write(source.read())
                                            os.remove(temp_path)  # Clean up temp file
                                            target_file_found = True
                                            break
                                    
                                    if not target_file_found:
                                        print(f"❌ Could not find {filename} in ZIP archive")
                                        # List all files in ZIP for debugging
                                        print("📋 ZIP contents:")
                                        for zip_info in zip_ref.infolist():
                                            print(f"   - {zip_info.filename}")
                                        os.remove(temp_path)
                                        return False
                                    
                                    print(f"✅ Successfully extracted {filename} from ZIP")
                                    return True
                            
                            else:
                                # Not a ZIP, rename temp file to final name
                                os.rename(temp_path, local_path)
                                print(f"✅ Successfully downloaded {filename} via direct link")
                                return True
                        except Exception as zip_error:
                            print(f"Error processing download for {filename}: {zip_error}")
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            return False
                        
                    except Exception as e2:
                        print(f"Both download methods failed for {filename}: {e2}")
                        return False
            else:
                # Regular Dropbox API download for user's own files
                with open(local_path, 'wb') as f:
                    metadata, response = self.client.files_download(file_path)
                    f.write(response.content)
                return True
                
        except Exception as e:
            print(f"Error downloading file {file_path}: {e}")
            return False
    
    def get_file_metadata(self, file_path: str) -> Dict:
        """Get file size, modified date, etc."""
        try:
            metadata = self.client.files_get_metadata(file_path)
            if isinstance(metadata, dropbox.files.FileMetadata):
                return {
                    'name': metadata.name,
                    'size': metadata.size,
                    'modified': metadata.server_modified.isoformat() if metadata.server_modified else None,
                    'id': metadata.id
                }
            return {}
        except Exception as e:
            print(f"Error getting file metadata: {e}")
            return {}