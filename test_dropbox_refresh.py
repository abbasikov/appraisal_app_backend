#!/usr/bin/env python3
"""
Test script to verify Dropbox refresh token functionality
"""

import os
import sys

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.dropbox_auth_service import DropboxAuthService
from services.dropbox_service import DropboxService
from core.config import settings

def test_token_refresh():
    print("🧪 Testing Dropbox Refresh Token Functionality")
    print("=" * 50)
    
    # Check current token configuration
    print(f"\n📋 Current Configuration:")
    print(f"   App Key: {settings.DROPBOX_APP_KEY[:10]}..." if settings.DROPBOX_APP_KEY else "   App Key: Not set")
    print(f"   Access Token: {'Set' if settings.DROPBOX_ACCESS_TOKEN else 'Not set'}")
    print(f"   Refresh Token: {'Set' if settings.DROPBOX_REFRESH_TOKEN else 'Not set'}")
    print(f"   Token Expires: {settings.DROPBOX_TOKEN_EXPIRES_AT or 'Not set'}")
    
    # Test getting a valid client
    print(f"\n🔍 Testing client creation...")
    client = DropboxAuthService.get_valid_client()
    
    if client:
        print("✅ Successfully obtained valid Dropbox client")
        
        # Test a simple API call
        try:
            account = client.users_get_current_account()
            print(f"✅ API test successful - Account: {account.name.display_name}")
        except Exception as e:
            print(f"❌ API test failed: {e}")
    else:
        print("❌ Failed to obtain valid Dropbox client")
    
    # Test DropboxService
    print(f"\n🔍 Testing DropboxService...")
    try:
        service = DropboxService()
        if service.client:
            print("✅ DropboxService initialized successfully")
        else:
            print("❌ DropboxService failed to initialize")
    except Exception as e:
        print(f"❌ DropboxService error: {e}")
    
    # Manual refresh test (if refresh token available)
    if settings.DROPBOX_REFRESH_TOKEN:
        print(f"\n🔄 Testing manual token refresh...")
        success = DropboxAuthService.refresh_access_token()
        if success:
            print("✅ Manual refresh successful")
        else:
            print("❌ Manual refresh failed")
    else:
        print(f"\n⚠️ No refresh token available for manual refresh test")
        print(f"   Use setup_dropbox_oauth.py to set up OAuth with refresh tokens")

if __name__ == "__main__":
    test_token_refresh()