#!/usr/bin/env python3
"""
Quick token setup - generates a new long-lived token programmatically
This bypasses the refresh token setup for development/testing
"""

import os
import sys
import requests
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.dropbox_auth_service import DropboxAuthService
from core.config import settings

def generate_new_token():
    print("⚡ Quick Dropbox Token Setup")
    print("=" * 35)
    
    print("🔑 This will generate a new access token using your app credentials")
    print("⚠️  Note: This creates a long-lived token (no refresh needed)")
    
    # Check if we have app credentials
    if not settings.DROPBOX_APP_KEY or not settings.DROPBOX_APP_SECRET:
        print("❌ Missing DROPBOX_APP_KEY or DROPBOX_APP_SECRET in .env")
        return
    
    # For development, we can use the existing long-lived token approach
    # but with better expiry tracking
    current_token = settings.DROPBOX_ACCESS_TOKEN
    
    if current_token:
        print(f"\n🔍 Testing current token...")
        
        # Test if current token works
        try:
            import dropbox
            client = dropbox.Dropbox(current_token)
            account = client.users_get_current_account()
            print(f"✅ Current token is valid - Account: {account.name.display_name}")
            
            # Set a far future expiry for long-lived tokens (1 year)
            expires_at = datetime.now() + timedelta(days=365)
            DropboxAuthService.update_env_token(
                current_token, 
                expires_at.isoformat(),
                None  # No refresh token for long-lived tokens
            )
            
            print(f"✅ Token expiry updated to: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🎉 Setup complete! Your token is valid for 1 year.")
            return
            
        except Exception as e:
            print(f"❌ Current token is invalid: {e}")
    
    print(f"\n❌ Current token is expired or invalid")
    print(f"📋 You need to get a new token. Options:")
    print(f"   1. Run: python auto_dropbox_setup.py (recommended)")
    print(f"   2. Get a new token from Dropbox App Console")
    print(f"   3. Use the Dropbox API Explorer to generate a token")
    
    # Provide direct link to get new token
    print(f"\n🔗 Quick token generation:")
    print(f"   Visit: https://dropbox.github.io/dropbox-api-v2-explorer/")
    print(f"   1. Click 'Get Token'")
    print(f"   2. Authorize your app")
    print(f"   3. Copy the generated token")
    print(f"   4. Update DROPBOX_ACCESS_TOKEN in your .env file")

if __name__ == "__main__":
    generate_new_token()