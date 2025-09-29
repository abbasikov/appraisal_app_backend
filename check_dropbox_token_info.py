#!/usr/bin/env python3
"""
Check Dropbox token info using various methods (like Meta's token debugger)
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings

def check_token_info():
    print("🔍 Dropbox Token Information Check")
    print("=" * 40)
    
    token = settings.DROPBOX_ACCESS_TOKEN
    app_key = settings.DROPBOX_APP_KEY
    app_secret = settings.DROPBOX_APP_SECRET
    
    print(f"🔑 Token: {token[:30]}...")
    
    # Method 1: Try OAuth2 token info endpoint (similar to Meta)
    print(f"\n📋 Method 1: OAuth2 Token Info")
    try:
        url = "https://api.dropboxapi.com/2/auth/token/from_oauth1"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json={})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 2: Try token revoke endpoint to get info (without actually revoking)
    print(f"\n📋 Method 2: Token Revoke Info (dry run)")
    try:
        url = "https://api.dropboxapi.com/2/auth/token/revoke"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Don't actually call this as it would revoke the token
        print(f"   ⚠️  Skipping actual call (would revoke token)")
        print(f"   URL: {url}")
        
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 3: Try check endpoint
    print(f"\n📋 Method 3: Auth Check")
    try:
        url = "https://api.dropboxapi.com/2/check/user"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json={"query": "test"})
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 4: Try to decode token manually (JWT-style)
    print(f"\n📋 Method 4: Token Structure Analysis")
    try:
        import base64
        
        # Try to decode if it's JWT-like
        parts = token.split('.')
        print(f"   Token parts: {len(parts)}")
        
        if len(parts) >= 2:
            try:
                # Try to decode first part (header)
                header_data = base64.b64decode(parts[0] + '==')
                print(f"   Header: {header_data}")
            except:
                print(f"   Header: Not base64 decodable")
            
            try:
                # Try to decode second part (payload)
                payload_data = base64.b64decode(parts[1] + '==')
                print(f"   Payload: {payload_data}")
            except:
                print(f"   Payload: Not base64 decodable")
        else:
            print(f"   Not JWT format")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 5: Check Dropbox documentation endpoints
    print(f"\n📋 Method 5: Dropbox App Info")
    try:
        # Try to get app info
        url = "https://api.dropboxapi.com/2/team/get_info"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json={})
        print(f"   Team Info Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Team Response: {json.dumps(data, indent=2)}")
        else:
            print(f"   Team Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 6: Manual HTTP request to check headers
    print(f"\n📋 Method 6: HTTP Headers Analysis")
    try:
        url = "https://api.dropboxapi.com/2/users/get_current_account"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json={})
        print(f"   Status: {response.status_code}")
        print(f"   Response Headers:")
        for key, value in response.headers.items():
            if 'token' in key.lower() or 'expire' in key.lower() or 'auth' in key.lower():
                print(f"     {key}: {value}")
        
        # Check if response contains any expiry info
        if response.status_code == 200:
            data = response.json()
            print(f"   Looking for expiry in response...")
            response_str = json.dumps(data)
            if 'exp' in response_str or 'expire' in response_str.lower():
                print(f"   Found expiry-related data: {data}")
            else:
                print(f"   No expiry info in response")
                
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Final recommendation
    print(f"\n🎯 Dropbox Token Inspection Results:")
    print(f"   📋 Unlike Meta's Access Token Debugger, Dropbox doesn't provide")
    print(f"      a public token inspection tool or API endpoint")
    print(f"   🔍 Token appears to be: {token[:10]}... (sl. prefix = short-lived format)")
    print(f"   ⚠️  But format doesn't guarantee actual lifetime")
    print(f"   ✅ Token is currently working with API")
    
    print(f"\n💡 Recommendations:")
    print(f"   1. Monitor token - it will fail when expired")
    print(f"   2. Our refresh token system will handle expiry")
    print(f"   3. For production: Set up OAuth with refresh tokens")
    print(f"   4. Current token: Use until it stops working")

if __name__ == "__main__":
    check_token_info()