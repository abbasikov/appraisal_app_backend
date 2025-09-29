import dropbox
import os
import re
from typing import List, Optional, Dict
from app.core.config import settings

class DropboxService:
    def __init__(self):
        from app.services.dropbox_auth_service import DropboxAuthService
        # Try to get a valid client with token refresh capability
        self.client = DropboxAuthService.get_valid_client() or dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
    
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
        """Check if shared folder is accessible - ENHANCED WITH AUTO-REFRESH"""
        try:
            # REFRESH TOKEN LOGIC: Ensure we have a valid client before API calls
            if not self.client:
                print("❌ No valid Dropbox client available")
                return False
                
            # For shared folders, use sharing API
            shared_link_metadata = self.client.sharing_get_shared_link_metadata(share_link)
            print(f"✅ Folder access validated: {share_link}")
            return True
            
        except dropbox.exceptions.AuthError as auth_error:
            print(f"⚠️ Auth error accessing folder: {auth_error}")
            
            # REFRESH TOKEN LOGIC: Auto-retry with token refresh
            from app.services.dropbox_auth_service import DropboxAuthService
            refreshed_client = DropboxAuthService.get_valid_client()
            
            if refreshed_client:
                try:
                    # Retry with refreshed client
                    self.client = refreshed_client
                    shared_link_metadata = self.client.sharing_get_shared_link_metadata(share_link)
                    print(f"✅ Folder access validated after token refresh: {share_link}")
                    return True
                except Exception as retry_error:
                    print(f"❌ Still cannot access folder after refresh: {retry_error}")
                    return False
            else:
                print("❌ Cannot refresh token - user re-authentication required")
                return False
                
        except Exception as e:
            print(f"❌ Folder access error: {e}")
            return False
    
    def list_folder_contents_recursive(self, share_link: str, path: str = "") -> List[Dict]:
        """Recursively list all images in shared folder and subfolders"""
        try:
            files = []
            print(f"📂 Scanning folder: {path or 'root'} in {share_link}")
            
            # Use files_list_folder with shared_link parameter
            shared_link_obj = dropbox.files.SharedLink(url=share_link)
            result = self.client.files_list_folder(path=path, shared_link=shared_link_obj)
            
            for entry in result.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    # Check if file is an image
                    file_ext = os.path.splitext(entry.name)[1].lower()
                    if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                        folder_path = path if path else "/"
                        print(f"🖼️  Found image: {entry.name} in {folder_path}")
                        files.append({
                            'name': entry.name,
                            'path': entry.path_lower or ('/' + entry.name),  # Use filename if path_lower is None
                            'folder_path': folder_path,
                            'size': entry.size,
                            'modified': entry.server_modified.isoformat() if entry.server_modified else None,
                            'id': entry.id,
                            'rev': getattr(entry, 'rev', None)
                        })
                elif isinstance(entry, dropbox.files.FolderMetadata):
                    # Try to scan subfolders, but ignore errors
                    print(f"📁 Found subfolder: {entry.name}")
                    try:
                        subfolder_files = self.list_folder_contents_recursive(share_link, entry.path_lower)
                        files.extend(subfolder_files)
                    except Exception as subfolder_error:
                        print(f"⚠️  Subfolder {entry.name} restricted, will extract from ZIP instead")
                        # Continue processing - we'll get these files from ZIP extraction
                        continue
            
            # Handle pagination if there are more files
            while result.has_more:
                result = self.client.files_list_folder_continue(result.cursor)
                for entry in result.entries:
                    if isinstance(entry, dropbox.files.FileMetadata):
                        file_ext = os.path.splitext(entry.name)[1].lower()
                        if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                            folder_path = path if path else "/"
                            files.append({
                                'name': entry.name,
                                'path': entry.path_lower or ('/' + entry.name),  # Use filename if path_lower is None
                                'folder_path': folder_path,
                                'size': entry.size,
                                'modified': entry.server_modified.isoformat() if entry.server_modified else None,
                                'id': entry.id,
                                'rev': getattr(entry, 'rev', None)
                            })
                    elif isinstance(entry, dropbox.files.FolderMetadata):
                        try:
                            subfolder_files = self.list_folder_contents_recursive(share_link, entry.path_lower)
                            files.extend(subfolder_files)
                        except Exception:
                            continue
            
            if path == "":
                print(f"✅ Total images found in all folders: {len(files)}")
            return files
        except Exception as e:
            print(f"❌ Error listing folder contents: {e}")
            return []
    
    def extract_all_images_from_zip(self, share_link: str) -> List[Dict]:
        """Extract all images from ZIP download, including subfolder images"""
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
            
            print(f"📦 Downloading ZIP to extract all images...")
            
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
            
            files = []
            
            # Extract all images from ZIP
            if zipfile.is_zipfile(temp_zip_path):
                with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                    for zip_info in zip_ref.infolist():
                        if not zip_info.is_dir():
                            filename = os.path.basename(zip_info.filename)
                            file_ext = os.path.splitext(filename)[1].lower()
                            
                            if file_ext in settings.ALLOWED_IMAGE_EXTENSIONS:
                                # Determine folder path
                                folder_path = os.path.dirname(zip_info.filename)
                                if not folder_path or folder_path == '.':
                                    folder_path = '/'
                                else:
                                    folder_path = '/' + folder_path
                                
                                print(f"🖼️  Found image in ZIP: {filename} in {folder_path}")
                                
                                files.append({
                                    'name': filename,
                                    'path': zip_info.filename,  # Full path in ZIP
                                    'folder_path': folder_path,
                                    'size': zip_info.file_size,
                                    'modified': None,  # ZIP doesn't have server_modified
                                    'id': None,
                                    'rev': None,
                                    'from_zip': True  # Flag to indicate this came from ZIP
                                })
            
            # Clean up temp file
            os.unlink(temp_zip_path)
            
            print(f"✅ Found {len(files)} images in ZIP (including subfolders)")
            return files
            
        except Exception as e:
            print(f"❌ Error extracting images from ZIP: {e}")
            return []
    
    def list_folder_contents(self, share_link: str) -> List[Dict]:
        """List all images in shared folder and subfolders"""
        # First try API method
        api_files = self.list_folder_contents_recursive(share_link)
        
        # Then try ZIP extraction to get subfolder images that API couldn't access
        zip_files = self.extract_all_images_from_zip(share_link)
        
        # Combine results, avoiding duplicates
        all_files = api_files.copy()
        api_filenames = {f['name'].lower() for f in api_files}
        
        for zip_file in zip_files:
            if zip_file['name'].lower() not in api_filenames:
                all_files.append(zip_file)
        
        print(f"✅ Total unique images found: {len(all_files)}")
        return all_files
    
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
                                        
                                        # Match by exact filename (case insensitive)
                                        if zip_filename == target_filename:
                                            print(f"✅ Found exact match: {zip_info.filename}")
                                            with zip_ref.open(zip_info) as source, open(local_path, 'wb') as target:
                                                target.write(source.read())
                                            os.remove(temp_path)  # Clean up temp file
                                            target_file_found = True
                                            break
                                    
                                    if not target_file_found:
                                        # Try to find by full path (for subfolder files)
                                        for zip_info in zip_ref.infolist():
                                            if zip_info.filename.lower().endswith(filename.lower()):
                                                print(f"✅ Found by path match: {zip_info.filename}")
                                                with zip_ref.open(zip_info) as source, open(local_path, 'wb') as target:
                                                    target.write(source.read())
                                                os.remove(temp_path)
                                                target_file_found = True
                                                break
                                        
                                        if not target_file_found:
                                            print(f"❌ Could not find {filename} in ZIP archive")
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