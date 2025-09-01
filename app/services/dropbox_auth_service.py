import dropbox
import requests
from datetime import datetime, timedelta
from app.core.config import settings
import os

class DropboxAuthService:
    
    @staticmethod
    def refresh_access_token():
        """Refresh Dropbox access token using refresh token"""
        try:
            if not settings.DROPBOX_REFRESH_TOKEN:
                print("⚠️ No refresh token available - using current access token")
                return True  # Return True to continue with current token
            
            # Check if token needs refresh (expires in next 10 minutes)
            if settings.DROPBOX_TOKEN_EXPIRES_AT:
                expires_at = datetime.fromisoformat(settings.DROPBOX_TOKEN_EXPIRES_AT)
                if datetime.now() + timedelta(minutes=10) < expires_at:
                    print("Token still valid, no refresh needed")
                    return True
            
            print("Refreshing Dropbox access token...")
            
            # Refresh token request
            response = requests.post('https://api.dropbox.com/oauth2/token', data={
                'grant_type': 'refresh_token',
                'refresh_token': settings.DROPBOX_REFRESH_TOKEN,
                'client_id': settings.DROPBOX_APP_KEY,
                'client_secret': settings.DROPBOX_APP_SECRET
            })
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 14400)  # Default 4 hours
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update environment file
                DropboxAuthService.update_env_token(new_access_token, expires_at.isoformat())
                
                print("✅ Access token refreshed successfully")
                return True
            else:
                print(f"❌ Failed to refresh token: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False
    
    @staticmethod
    def update_env_token(access_token: str, expires_at: str):
        """Update .env file with new token"""
        try:
            env_path = '.env'
            if not os.path.exists(env_path):
                return
            
            # Read current .env
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update token lines
            updated_lines = []
            for line in lines:
                if line.startswith('DROPBOX_ACCESS_TOKEN='):
                    updated_lines.append(f'DROPBOX_ACCESS_TOKEN={access_token}\n')
                elif line.startswith('DROPBOX_TOKEN_EXPIRES_AT='):
                    updated_lines.append(f'DROPBOX_TOKEN_EXPIRES_AT={expires_at}\n')
                else:
                    updated_lines.append(line)
            
            # Write updated .env
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            # Update settings in memory
            settings.DROPBOX_ACCESS_TOKEN = access_token
            settings.DROPBOX_TOKEN_EXPIRES_AT = expires_at
            
        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
    
    @staticmethod
    def get_valid_client():
        """Get Dropbox client with valid token"""
        try:
            # First, test if current token works
            test_client = dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
            try:
                # Simple API call to test token validity
                test_client.users_get_current_account()
                print("✅ Current Dropbox token is valid")
                return test_client
            except dropbox.exceptions.AuthError as auth_error:
                print(f"⚠️ Token invalid: {auth_error}")
                # Try to refresh if we have refresh token
                if DropboxAuthService.refresh_access_token():
                    return dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
                else:
                    print("❌ Could not refresh token")
                    return None
            
        except Exception as e:
            print(f"❌ Error getting Dropbox client: {e}")
            return dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)  # Fallback to original token