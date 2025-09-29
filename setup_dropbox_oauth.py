#!/usr/bin/env python3
"""
Setup script for Dropbox OAuth with refresh tokens
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.dropbox_auth_service import DropboxAuthService

def main():
    print("🔧 Dropbox OAuth Setup with Refresh Tokens")
    print("=" * 50)
    
    # Step 1: Generate OAuth URL
    print("\n📋 Step 1: Get OAuth URL")
    oauth_url = DropboxAuthService.get_oauth_url()
    
    if not oauth_url:
        print("❌ Failed to generate OAuth URL")
        return
    
    print(f"\n🔗 Visit this URL to authorize your app:")
    print(f"   {oauth_url}")
    print(f"\n⚠️  IMPORTANT: This URL includes 'token_access_type=offline'")
    print(f"   This ensures you get BOTH access and refresh tokens")
    
    # Step 2: Get authorization code
    print(f"\n📋 Step 2: Get Authorization Code")
    print(f"   After authorizing, you'll be redirected to a URL like:")
    print(f"   http://localhost:8000/auth/dropbox/callback?code=AUTHORIZATION_CODE")
    
    auth_code = input("\n🔑 Enter the authorization code from the redirect URL: ").strip()
    
    if not auth_code:
        print("❌ No authorization code provided")
        return
    
    # Step 3: Exchange code for tokens
    print(f"\n📋 Step 3: Exchange Code for Tokens")
    tokens = DropboxAuthService.exchange_code_for_tokens(auth_code)
    
    if tokens:
        print(f"\n✅ SUCCESS! Dropbox OAuth setup complete")
        print(f"   Access Token: {tokens['access_token'][:20]}...")
        print(f"   Refresh Token: {'Yes' if tokens['refresh_token'] else 'No'}")
        print(f"   Expires At: {tokens['expires_at']}")
        print(f"\n🔄 Your tokens have been saved to .env file")
        print(f"   The system will automatically refresh tokens when needed")
    else:
        print(f"\n❌ Failed to exchange code for tokens")

if __name__ == "__main__":
    main()