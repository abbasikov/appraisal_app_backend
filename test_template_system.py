#!/usr/bin/env python3
"""
Test script for template system functionality
"""

import os
import sys
import requests
import json
from pathlib import Path

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

def test_template_endpoints():
    """Test template system endpoints"""
    
    print("🧪 Testing Template System")
    print("=" * 50)
    
    # Test 1: List templates (should work without auth for testing)
    print("1. Testing GET /templates/")
    try:
        response = requests.get(f"{API_BASE}/templates/")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Templates found: {data.get('total', 0)}")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Check API documentation
    print("\n2. Testing API Documentation")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"   Docs Status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Check template directory structure
    print("\n3. Checking Template Directory Structure")
    template_dirs = ["templates/original", "templates/fillable", "templates/generated", "templates/temp"]
    for dir_path in template_dirs:
        if os.path.exists(dir_path):
            print(f"   ✓ {dir_path} exists")
        else:
            print(f"   ✗ {dir_path} missing")
    
    print("\n✅ Template system test completed")

if __name__ == "__main__":
    test_template_endpoints()