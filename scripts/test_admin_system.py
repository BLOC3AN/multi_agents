#!/usr/bin/env python3
"""
Comprehensive test script for admin system with collections separation.
Tests authentication, API endpoints, and permissions.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE = "http://localhost:8000"

def test_authentication():
    """Test authentication for different admin types."""
    print("🔐 Testing Authentication")
    print("=" * 40)
    
    test_cases = [
        {
            "name": "Super Admin",
            "user_id": "superadmin",
            "password": "SuperAdmin@2024",
            "expected_role": "super_admin"
        },
        {
            "name": "Test Admin", 
            "user_id": "testadmin",
            "password": "test123",
            "expected_role": "admin"
        },
        {
            "name": "Hai LT Admin",
            "user_id": "hailt_admin", 
            "password": "HaiLT@2024",
            "expected_role": "super_admin"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n👤 Testing {test['name']}")
        
        try:
            response = requests.post(f"{API_BASE}/auth/login", json={
                "user_id": test["user_id"],
                "password": test["password"]
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    user = data.get("user", {})
                    role = user.get("role")
                    
                    if role == test["expected_role"]:
                        print(f"✅ Login successful - Role: {role}")
                        print(f"   Permissions: {user.get('can_delete_users', False)}")
                        results.append({"test": test["name"], "status": "PASS"})
                    else:
                        print(f"❌ Wrong role - Expected: {test['expected_role']}, Got: {role}")
                        results.append({"test": test["name"], "status": "FAIL"})
                else:
                    print(f"❌ Login failed: {data.get('error', 'Unknown error')}")
                    results.append({"test": test["name"], "status": "FAIL"})
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                results.append({"test": test["name"], "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"test": test["name"], "status": "ERROR"})
    
    return results


def test_api_endpoints():
    """Test API endpoints for users and admins collections."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 40)
    
    endpoints = [
        {
            "name": "Users Collection",
            "url": f"{API_BASE}/admin/users",
            "expected_type": "regular users"
        },
        {
            "name": "Admins Collection", 
            "url": f"{API_BASE}/admin/users?collection=admins",
            "expected_type": "super admins"
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📊 Testing {endpoint['name']}")
        
        try:
            response = requests.get(endpoint["url"], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    users = data.get("users", [])
                    total = data.get("total", 0)
                    
                    print(f"✅ {endpoint['name']}: {total} {endpoint['expected_type']}")
                    
                    # Show sample user roles
                    if users:
                        roles = [user.get("role") for user in users[:3]]
                        print(f"   Sample roles: {roles}")
                    
                    results.append({"test": endpoint["name"], "status": "PASS", "count": total})
                else:
                    print(f"❌ API error: {data.get('error', 'Unknown error')}")
                    results.append({"test": endpoint["name"], "status": "FAIL"})
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                results.append({"test": endpoint["name"], "status": "FAIL"})
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({"test": endpoint["name"], "status": "ERROR"})
    
    return results


def test_delete_permissions():
    """Test delete user permissions with force parameter."""
    print("\n🗑️ Testing Delete Permissions")
    print("=" * 40)
    
    # First create a test user to delete
    print("📝 Creating test user for deletion...")
    
    test_user_id = f"test_delete_{datetime.now().strftime('%H%M%S')}"
    
    try:
        # Create test user via direct database (simpler)
        from src.database.models import get_db_config
        db = get_db_config()
        
        test_user = {
            "user_id": test_user_id,
            "display_name": "Test Delete User",
            "email": "test@delete.com",
            "password_hash": "dummy_hash",
            "is_active": True,
            "role": "user",
            "created_at": datetime.utcnow().isoformat()
        }
        
        db.users.insert_one(test_user)
        print(f"✅ Created test user: {test_user_id}")
        
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return [{"test": "Delete Permissions", "status": "ERROR"}]
    
    # Test delete without force (should fail for admin users, succeed for regular users)
    print(f"\n🚫 Testing delete {test_user_id} without force...")
    
    try:
        response = requests.delete(f"{API_BASE}/admin/users/{test_user_id}", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✅ Regular user deleted successfully (expected)")
                return [{"test": "Delete Permissions", "status": "PASS"}]
            else:
                print(f"❌ Delete failed: {data.get('error')}")
                return [{"test": "Delete Permissions", "status": "FAIL"}]
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return [{"test": "Delete Permissions", "status": "FAIL"}]
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return [{"test": "Delete Permissions", "status": "ERROR"}]


def main():
    """Run all tests and generate report."""
    print("🧪 Admin System Comprehensive Test")
    print("=" * 50)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    # Run all tests
    all_results.extend(test_authentication())
    all_results.extend(test_api_endpoints()) 
    all_results.extend(test_delete_permissions())
    
    # Generate summary report
    print("\n📋 Test Summary Report")
    print("=" * 50)
    
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL") 
    errors = sum(1 for r in all_results if r["status"] == "ERROR")
    total = len(all_results)
    
    print(f"📊 Total Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Errors: {errors}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"🎯 Success Rate: {success_rate:.1f}%")
    
    # Detailed results
    print("\n📝 Detailed Results:")
    for result in all_results:
        status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}[result["status"]]
        print(f"   {status_icon} {result['test']}: {result['status']}")
    
    # Final verdict
    if failed == 0 and errors == 0:
        print("\n🎉 All tests passed! Admin system is working correctly.")
        return 0
    else:
        print(f"\n⚠️ {failed + errors} tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
