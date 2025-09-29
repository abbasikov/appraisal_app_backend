#!/usr/bin/env python3
"""
Test script to determine if the Dropbox token is long-term or short-term
"""

import os
import sys
from datetime import datetime, timedelta

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from core.config import settings
import dropbox

def test_token_type():
    print("🔍 Dropbox Token Type Analysis")
    print("=" * 35)
    
    # Check token characteristics
    token = settings.DROPBOX_ACCESS_TOKEN
    expires_at = settings.DROPBOX_TOKEN_EXPIRES_AT
    
    print(f"📋 Token Analysis:")
    print(f"   Token length: {len(token)} characters")
    print(f"   Token prefix: {token[:10]}...")
    print(f"   Expires at: {expires_at}")
    
    # Parse expiry date
    if expires_at:
        try:
            expiry_date = datetime.fromisoformat(expires_at)
            now = datetime.now()
            time_until_expiry = expiry_date - now
            
            print(f"   Time until expiry: {time_until_expiry.days} days")
            
            # Determine token type based on expiry
            if time_until_expiry.days > 180:  # More than 6 months
                token_type = "🟢 LONG-TERM TOKEN"
                print(f"   Token type: {token_type}")
                print(f"   ✅ This is a long-lived token (expires in {time_until_expiry.days} days)")
            elif time_until_expiry.days > 1:
                token_type = "🟡 MEDIUM-TERM TOKEN"
                print(f"   Token type: {token_type}")
                print(f"   ⚠️  This token expires in {time_until_expiry.days} days")
            else:
                token_type = "🔴 SHORT-TERM TOKEN"
                print(f"   Token type: {token_type}")
                print(f"   ❌ This token expires soon ({time_until_expiry.days} days)")
                
        except ValueError:
            print(f"   ❌ Invalid expiry format")
    
    # Test token with API call
    print(f"\n🧪 API Test:")
    try:
        client = dropbox.Dropbox(token)
        account = client.users_get_current_account()
        
        print(f"   ✅ Token is valid")
        print(f"   Account: {account.name.display_name}")
        print(f"   Email: {account.email}")
        
        # Check if it's a team or personal account
        if hasattr(account, 'account_type'):
            print(f"   Account type: {account.account_type}")
            
    except Exception as e:
        print(f"   ❌ Token test failed: {e}")
    
    # Additional token characteristics
    print(f"\n🔬 Token Characteristics:")
    
    # Long-term tokens from API Explorer are usually very long
    if len(token) > 1000:
        print(f"   ✅ Very long token (typical of long-term tokens)")
    else:
        print(f"   ⚠️  Shorter token (might be short-term)")
    
    # Check if we have refresh token
    if settings.DROPBOX_REFRESH_TOKEN:
        print(f"   ✅ Has refresh token (short-term with refresh capability)")
    else:
        print(f"   ⚠️  No refresh token (likely long-term token)")
    
    print(f"\n📊 Summary:")
    if expires_at:
        expiry_date = datetime.fromisoformat(expires_at)
        days_left = (expiry_date - datetime.now()).days
        
        if days_left > 300:
            print(f"   🎉 You have a LONG-TERM token valid for {days_left} days!")
            print(f"   ✅ No immediate action needed")
        elif days_left > 30:
            print(f"   ⚠️  Token expires in {days_left} days")
            print(f"   📝 Consider setting up refresh tokens for automatic renewal")
        else:
            print(f"   🚨 Token expires soon ({days_left} days)")
            print(f"   🔄 Set up refresh tokens or get a new long-term token")

if __name__ == "__main__":
    test_token_type()