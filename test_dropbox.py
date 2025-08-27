import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.dropbox_service import DropboxService
from app.core.config import settings

def test_dropbox_connection():
    """Test Dropbox API connection and folder access"""
    
    # Test URL
    test_url = "https://www.dropbox.com/scl/fo/1gkgokz0rax6gnjc4tqss/AF6FopkygVg_YggLJIEbzvI?rlkey=78a9vu2t2omp8k5jbji2rjwic&st=2ley29d7&dl=0"
    
    print(f"🔍 Testing Dropbox Integration")
    print(f"URL: {test_url}")
    print(f"Access Token: {settings.DROPBOX_ACCESS_TOKEN[:20]}...")
    print()
    
    try:
        # Test folder ID extraction
        folder_id = DropboxService.extract_folder_id_from_link(test_url)
        print(f"✅ Extracted folder ID: {folder_id}")
        
        if not folder_id:
            print("❌ Failed to extract folder ID from URL")
            return
        
        # Test Dropbox service initialization
        dropbox_service = DropboxService()
        print(f"✅ Dropbox service initialized")
        
        # Test folder access validation
        print(f"🔍 Testing folder access...")
        is_accessible = dropbox_service.validate_folder_access(test_url)
        print(f"{'✅' if is_accessible else '❌'} Folder accessible: {is_accessible}")
        
        if not is_accessible:
            print("❌ Cannot access folder. Check:")
            print("  - Dropbox access token is valid")
            print("  - Folder is shared publicly")
            print("  - App has proper permissions")
            return
        
        # Test listing folder contents
        print(f"🔍 Listing folder contents...")
        files = dropbox_service.list_folder_contents(test_url)
        print(f"✅ Found {len(files)} image files")
        
        for i, file_info in enumerate(files[:5]):  # Show first 5 files
            print(f"  {i+1}. {file_info['name']} ({file_info['size']} bytes)")
        
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more files")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dropbox_connection()