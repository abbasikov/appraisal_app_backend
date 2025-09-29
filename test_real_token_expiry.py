#!/usr/bin/env python3
"""
Test script to get REAL token expiry from Dropbox API (not from .env file)
"""

import os
import sys
import requests
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings
import dropbox

def test_real_token_expiry():
    print("🔍 REAL Dropbox Token Expiry Check")
    print("=" * 40)
    
    token = settings.DROPBOX_ACCESS_TOKEN
    
    print(f"📋 Checking REAL token expiry from Dropbox API...")
    print(f"   Token: {token[:20]}...")
    
    # Method 1: Try to get token info from Dropbox API
    try:
        print(f"\n🔍 Method 1: Dropbox API Token Info")
        
        # Use Dropbox API to check token
        client = dropbox.Dropbox(token)
        
        # Try to get account info (this will fail if token is expired)
        account = client.users_get_current_account()
        print(f"   ✅ Token is currently valid")
        print(f"   Account: {account.name.display_name}")
        
        # Try to get more detailed token info
        try:
            # Some tokens have expiry info in the API response
            space_usage = client.users_get_space_usage()
            print(f"   ✅ API calls working (Space used: {space_usage.used} bytes)")
        except Exception as e:
            print(f"   ⚠️  Secondary API call failed: {e}")
            
    except dropbox.exceptions.AuthError as auth_error:
        print(f"   ❌ Token is invalid/expired: {auth_error}")
        return
    except Exception as e:
        print(f"   ❌ API error: {e}")
        return
    
    # Method 2: Try to introspect token (if supported)
    print(f"\n🔍 Method 2: Token Introspection")
    try:
        # Try OAuth2 token introspection endpoint
        introspect_url = "https://api.dropbox.com/oauth2/token/introspect"
        
        response = requests.post(introspect_url, 
            data={'token': token},
            auth=(settings.DROPBOX_APP_KEY, settings.DROPBOX_APP_SECRET)
        )
        
        if response.status_code == 200:
            token_info = response.json()
            print(f"   ✅ Token introspection successful:")
            
            if 'exp' in token_info:
                exp_timestamp = token_info['exp']
                exp_date = datetime.fromtimestamp(exp_timestamp)
                days_left = (exp_date - datetime.now()).days
                print(f"   📅 Real expiry: {exp_date}")
                print(f"   ⏰ Days left: {days_left}")
            else:
                print(f"   ⚠️  No expiry info in response")
                
            if 'active' in token_info:
                print(f"   🔄 Active: {token_info['active']}")
                
            print(f"   📋 Full response: {token_info}")
        else:
            print(f"   ❌ Introspection failed (HTTP {response.status_code}): {response.text}")
            
    except Exception as e:
        print(f"   ❌ Introspection error: {e}")
    
    # Method 3: Check token characteristics
    print(f"\n🔍 Method 3: Token Analysis")
    
    # Long-term tokens from API Explorer typically don't have expiry
    if len(token) > 1000:
        print(f"   📏 Very long token ({len(token)} chars) - likely long-term")
    
    # Check token format
    if token.startswith('sl.'):
        print(f"   🔤 Token format: Short-lived token format")
        print(f"   ⚠️  This suggests it might be a short-term token")
    elif token.startswith('oauth2:'):
        print(f"   🔤 Token format: OAuth2 token")
    else:
        print(f"   🔤 Token format: Unknown format")
    
    # Method 4: Test with a simple API call and measure response
    print(f"\n🔍 Method 4: Stress Test")
    try:
        import time
        start_time = time.time()
        
        # Make multiple API calls to see if token is stable
        for i in range(3):
            client.users_get_current_account()
            time.sleep(0.5)
        
        end_time = time.time()
        print(f"   ✅ Multiple API calls successful ({end_time - start_time:.2f}s)")
        print(f"   🔄 Token appears stable and valid")
        
    except Exception as e:
        print(f"   ❌ Stress test failed: {e}")
    
    # Final assessment
    print(f"\n📊 REAL Token Assessment:")
    print(f"   🔍 Based on actual Dropbox API responses:")
    
    # Compare with .env expiry
    env_expiry = settings.DROPBOX_TOKEN_EXPIRES_AT
    if env_expiry:
        print(f"   📝 .env file says: {env_expiry}")
        print(f"   ⚠️  Note: .env expiry is just our tracking, not from Dropbox")
    
    print(f"\n🎯 Conclusion:")
    print(f"   ✅ Token is currently working with Dropbox API")
    print(f"   📋 Real expiry can only be determined by:")
    print(f"      1. Token stops working (you'll get auth errors)")
    print(f"      2. Dropbox provides expiry info (rare for long-term tokens)")
    print(f"   🔄 Our refresh token system will handle expiry automatically")

if __name__ == "__main__":
    test_real_token_expiry()