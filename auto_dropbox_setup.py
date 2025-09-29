#!/usr/bin/env python3
"""
Automated Dropbox OAuth setup - opens browser and simplifies the process
"""

import os
import sys
import webbrowser
import time

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.dropbox_auth_service import DropboxAuthService

def automated_oauth_setup():
    print("🚀 Automated Dropbox OAuth Setup")
    print("=" * 40)
    
    # Generate OAuth URL
    print("📋 Generating OAuth URL...")
    oauth_url = DropboxAuthService.get_oauth_url()
    
    if not oauth_url:
        print("❌ Failed to generate OAuth URL")
        return
    
    print(f"🔗 OAuth URL generated successfully!")
    print(f"\n📱 Opening browser automatically...")
    
    # Open browser automatically
    try:
        webbrowser.open(oauth_url)
        print("✅ Browser opened!")
    except Exception as e:
        print(f"⚠️ Could not open browser automatically: {e}")
        print(f"📋 Please manually visit: {oauth_url}")
    
    print(f"\n📝 Instructions:")
    print(f"   1. Authorize the app in the browser")
    print(f"   2. You'll be redirected to a page that may show an error")
    print(f"   3. Copy the 'code' parameter from the URL")
    print(f"   4. Paste it below")
    
    # Wait for user to complete authorization
    print(f"\n⏳ Waiting for authorization...")
    code = input("📝 Paste the authorization code here: ").strip()
    
    if not code:
        print("❌ No code provided")
        return
    
    # Exchange code for tokens
    print(f"\n🔄 Exchanging code for tokens...")
    result = DropboxAuthService.exchange_code_for_tokens(code)
    
    if result:
        print(f"\n🎉 SUCCESS! Dropbox OAuth setup complete!")
        print(f"✅ Access token: Saved")
        print(f"✅ Refresh token: {'Saved' if result.get('refresh_token') else 'Not provided (using long-lived token)'}")
        print(f"✅ Expires: {result.get('expires_at', 'Unknown')}")
        print(f"\n🔄 The app will now automatically refresh tokens when needed!")
        
        # Test the new tokens
        print(f"\n🧪 Testing new tokens...")
        client = DropboxAuthService.get_valid_client()
        if client:
            try:
                account = client.users_get_current_account()
                print(f"✅ Token test successful - Account: {account.name.display_name}")
            except Exception as e:
                print(f"⚠️ Token test failed: {e}")
        
    else:
        print("❌ Failed to exchange code for tokens")

if __name__ == "__main__":
    automated_oauth_setup()