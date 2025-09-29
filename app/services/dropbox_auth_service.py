import dropbox
import requests
from datetime import datetime, timedelta
from app.core.config import settings
import os

class DropboxAuthService:
    
    # REFRESH TOKEN LOGIC: New method to clear invalid tokens
    @staticmethod
    def clear_invalid_tokens():
        """Clear invalid tokens from .env and memory"""
        try:
            print("🧹 Clearing invalid tokens...")
            DropboxAuthService.update_env_token("", "", "")
            print("⚠️ Tokens cleared - user re-authentication required")
        except Exception as e:
            print(f"❌ Error clearing tokens: {e}")
    
    # REFRESH TOKEN LOGIC: Helper method for initial OAuth setup
    @staticmethod
    def get_oauth_url():
        """Generate OAuth URL for initial token setup with offline access"""
        try:
            import urllib.parse
            
            # REFRESH TOKEN LOGIC: Include token_access_type=offline for refresh tokens
            params = {
                'client_id': settings.DROPBOX_APP_KEY,
                'response_type': 'code',
                'token_access_type': 'offline',  # This is key for getting refresh tokens
            }
            
            oauth_url = 'https://www.dropbox.com/oauth2/authorize?' + urllib.parse.urlencode(params)
            print(f"🔗 OAuth URL (with offline access): {oauth_url}")
            print(f"⚠️  This will give you SHORT-LIVED tokens with REFRESH tokens")
            print(f"🔄 Unlike API Explorer tokens, these will show real expiry times")
            return oauth_url
            
        except Exception as e:
            print(f"❌ Error generating OAuth URL: {e}")
            return None
    
    # REFRESH TOKEN LOGIC: Helper method to exchange code for tokens
    @staticmethod
    def exchange_code_for_tokens(authorization_code: str, redirect_uri: str = None):
        """Exchange authorization code for access and refresh tokens"""
        try:
            print("🔄 Exchanging authorization code for tokens...")
            
            # REFRESH TOKEN LOGIC: Exchange code for both access and refresh tokens
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'client_id': settings.DROPBOX_APP_KEY,
                'client_secret': settings.DROPBOX_APP_SECRET
            }
            
            # Only add redirect_uri if provided
            if redirect_uri:
                data['redirect_uri'] = redirect_uri
            
            response = requests.post('https://api.dropbox.com/oauth2/token', 
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data['access_token']
                refresh_token = token_data.get('refresh_token')  # May not always be present
                expires_in = token_data.get('expires_in', 14400)  # Default 4 hours
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Update tokens
                DropboxAuthService.update_env_token(
                    access_token, 
                    expires_at.isoformat(),
                    refresh_token
                )
                
                print(f"✅ Tokens obtained successfully!")
                print(f"   Access token: {access_token[:20]}... (SHORT-LIVED)")
                print(f"   Refresh token: {'Yes' if refresh_token else 'No (this should not happen with offline access)'}")
                print(f"   🔥 REAL EXPIRY: {expires_in/3600:.1f} hours ({expires_in} seconds)")
                print(f"   📅 Expires at: {expires_at}")
                
                if not refresh_token:
                    print(f"   ⚠️  WARNING: No refresh token received!")
                    print(f"   🔗 Make sure you used token_access_type=offline in OAuth URL")
                
                return {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'expires_at': expires_at.isoformat()
                }
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ Failed to exchange code (HTTP {response.status_code}): {error_data}")
                return None
                
        except Exception as e:
            print(f"❌ Error exchanging code for tokens: {e}")
            return None
    
    @staticmethod
    def refresh_access_token():
        """Refresh Dropbox access token using refresh token - ENHANCED REFRESH TOKEN LOGIC"""
        try:
            if not settings.DROPBOX_REFRESH_TOKEN:
                print("⚠️ No refresh token available - using current access token")
                return True  # Return True to continue with current token
            
            # Check if token needs refresh (expires in next 10 minutes)
            if settings.DROPBOX_TOKEN_EXPIRES_AT:
                try:
                    expires_at = datetime.fromisoformat(settings.DROPBOX_TOKEN_EXPIRES_AT)
                    if datetime.now() + timedelta(minutes=10) < expires_at:
                        print("✅ Token still valid, no refresh needed")
                        return True
                except ValueError:
                    print("⚠️ Invalid expiry format, will refresh token")
            
            print("🔄 Refreshing Dropbox access token...")
            
            # REFRESH TOKEN LOGIC: Use official Dropbox OAuth2 endpoint
            response = requests.post('https://api.dropbox.com/oauth2/token', 
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': settings.DROPBOX_REFRESH_TOKEN,
                    'client_id': settings.DROPBOX_APP_KEY,
                    'client_secret': settings.DROPBOX_APP_SECRET
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 14400)  # Default 4 hours
                
                # REFRESH TOKEN LOGIC: Handle new refresh token if provided
                new_refresh_token = token_data.get('refresh_token')
                if new_refresh_token:
                    print("🔄 New refresh token received, updating...")
                
                # Calculate expiration time
                expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # REFRESH TOKEN LOGIC: Update both access and refresh tokens
                DropboxAuthService.update_env_token(
                    new_access_token, 
                    expires_at.isoformat(),
                    new_refresh_token
                )
                
                print(f"✅ Access token refreshed successfully (expires in {expires_in/3600:.1f} hours)")
                return True
            else:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"❌ Failed to refresh token (HTTP {response.status_code}): {error_data}")
                
                # REFRESH TOKEN LOGIC: Handle invalid refresh token
                if response.status_code == 400 and 'invalid_grant' in str(error_data):
                    print("❌ Refresh token is invalid or expired - user re-authentication required")
                    # Clear invalid tokens
                    DropboxAuthService.clear_invalid_tokens()
                
                return False
                
        except Exception as e:
            print(f"❌ Error refreshing token: {e}")
            return False
    
    @staticmethod
    def update_env_token(access_token: str, expires_at: str, refresh_token: str = None):
        """Update .env file with new tokens - ENHANCED TOKEN STORAGE"""
        try:
            env_path = '.env'
            if not os.path.exists(env_path):
                print("⚠️ .env file not found, tokens will only be updated in memory")
                # Update in-memory settings even if .env doesn't exist
                settings.DROPBOX_ACCESS_TOKEN = access_token
                settings.DROPBOX_TOKEN_EXPIRES_AT = expires_at
                if refresh_token:
                    settings.DROPBOX_REFRESH_TOKEN = refresh_token
                return
            
            # Read current .env
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # ENHANCED TOKEN STORAGE: Update all token-related lines
            updated_lines = []
            for line in lines:
                if line.startswith('DROPBOX_ACCESS_TOKEN='):
                    updated_lines.append(f'DROPBOX_ACCESS_TOKEN={access_token}\n')
                elif line.startswith('DROPBOX_TOKEN_EXPIRES_AT='):
                    updated_lines.append(f'DROPBOX_TOKEN_EXPIRES_AT={expires_at}\n')
                elif line.startswith('DROPBOX_REFRESH_TOKEN=') and refresh_token:
                    updated_lines.append(f'DROPBOX_REFRESH_TOKEN={refresh_token}\n')
                else:
                    updated_lines.append(line)
            
            # Write updated .env
            with open(env_path, 'w') as f:
                f.writelines(updated_lines)
            
            # ENHANCED TOKEN STORAGE: Update settings in memory
            settings.DROPBOX_ACCESS_TOKEN = access_token
            settings.DROPBOX_TOKEN_EXPIRES_AT = expires_at
            if refresh_token:
                settings.DROPBOX_REFRESH_TOKEN = refresh_token
                print("🔄 Refresh token updated in memory and .env")
            
            print(f"✅ Tokens updated successfully (expires: {expires_at})")
            
        except Exception as e:
            print(f"❌ Error updating .env file: {e}")
            # Still update in-memory settings as fallback
            settings.DROPBOX_ACCESS_TOKEN = access_token
            settings.DROPBOX_TOKEN_EXPIRES_AT = expires_at
            if refresh_token:
                settings.DROPBOX_REFRESH_TOKEN = refresh_token
    
    @staticmethod
    def get_valid_client():
        """Get Dropbox client with valid token - ENHANCED CLIENT WITH AUTO-REFRESH"""
        try:
            if not settings.DROPBOX_ACCESS_TOKEN:
                print("❌ No Dropbox access token configured")
                return None
            
            # ENHANCED CLIENT LOGIC: Check token expiry before making API calls
            if settings.DROPBOX_TOKEN_EXPIRES_AT:
                try:
                    expires_at = datetime.fromisoformat(settings.DROPBOX_TOKEN_EXPIRES_AT)
                    if datetime.now() + timedelta(minutes=5) >= expires_at:
                        print("⚠️ Token expires soon, refreshing proactively...")
                        if not DropboxAuthService.refresh_access_token():
                            print("❌ Proactive refresh failed")
                except ValueError:
                    print("⚠️ Invalid expiry format, will test token validity")
            
            # Test current token with API call
            test_client = dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
            try:
                # ENHANCED CLIENT LOGIC: Test token validity with minimal API call
                test_client.users_get_current_account()
                print("✅ Current Dropbox token is valid")
                return test_client
                
            except dropbox.exceptions.AuthError as auth_error:
                print(f"⚠️ Token invalid ({auth_error}), attempting refresh...")
                
                # ENHANCED CLIENT LOGIC: Auto-refresh on auth error
                if DropboxAuthService.refresh_access_token():
                    refreshed_client = dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
                    try:
                        # Verify refreshed token works
                        refreshed_client.users_get_current_account()
                        print("✅ Token refreshed and validated successfully")
                        return refreshed_client
                    except Exception as verify_error:
                        print(f"❌ Refreshed token still invalid: {verify_error}")
                        return None
                else:
                    print("❌ Could not refresh token - user re-authentication required")
                    return None
                    
            except Exception as api_error:
                print(f"⚠️ API error (not auth): {api_error}")
                return test_client  # Return client anyway, error might be temporary
            
        except Exception as e:
            print(f"❌ Error getting Dropbox client: {e}")
            # ENHANCED CLIENT LOGIC: Fallback with current token
            if settings.DROPBOX_ACCESS_TOKEN:
                return dropbox.Dropbox(settings.DROPBOX_ACCESS_TOKEN)
            return None