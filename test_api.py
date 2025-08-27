import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json

def test_project_api():
    """Test project API endpoints"""
    
    base_url = "http://localhost:8000/api/v1"
    
    # Test login first to get token
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🔐 Testing login...")
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Login successful")
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # Test get project
            print("📋 Testing get project...")
            response = requests.get(f"{base_url}/projects/1", headers=headers)
            if response.status_code == 200:
                project = response.json()
                print("✅ Get project successful")
                print(f"   dropbox_links: {project.get('dropbox_links')}")
                
                # Test update dropbox links
                print("🔗 Testing update dropbox links...")
                test_links = ["https://www.dropbox.com/test1", "https://www.dropbox.com/test2"]
                response = requests.post(f"{base_url}/projects/1/dropbox-links", 
                                       json=test_links, headers=headers)
                print(f"   Status: {response.status_code}")
                print(f"   Response: {response.text}")
                
                if response.status_code == 200:
                    print("✅ Update dropbox links successful")
                    
                    # Verify the update
                    response = requests.get(f"{base_url}/projects/1", headers=headers)
                    if response.status_code == 200:
                        project = response.json()
                        print(f"   Updated dropbox_links: {project.get('dropbox_links')}")
                else:
                    print("❌ Update dropbox links failed")
            else:
                print(f"❌ Get project failed: {response.status_code}")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_project_api()