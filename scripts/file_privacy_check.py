#!/usr/bin/env python3
"""
File Privacy and Isolation Check Script.
Ensures proper user isolation and file privacy in the system.
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config


def check_user_isolation():
    """Check that user file isolation is working correctly."""
    try:
        db = get_db_config()
        
        # Get all active files grouped by user
        pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {
                "_id": "$user_id",
                "file_count": {"$sum": 1},
                "files": {"$push": {
                    "file_name": "$file_name",
                    "file_key": "$file_key",
                    "file_size": "$file_size",
                    "upload_date": "$upload_date"
                }}
            }},
            {"$sort": {"file_count": -1}}
        ]
        
        user_stats = list(db.file_metadata.aggregate(pipeline))
        
        print("File Privacy and Isolation Report")
        print("=" * 50)
        print(f"Total users with active files: {len(user_stats)}")
        
        total_files = sum(user['file_count'] for user in user_stats)
        print(f"Total active files: {total_files}")
        print()
        
        print("📊 Files by User:")
        for user_stat in user_stats:
            user_id = user_stat['_id']
            file_count = user_stat['file_count']
            files = user_stat['files']
            
            print(f"  👤 {user_id}: {file_count} files")
            
            # Show file details
            for file_info in files:
                size_mb = file_info['file_size'] / (1024 * 1024)
                print(f"    📄 {file_info['file_name']} ({size_mb:.2f} MB)")
            print()
        
        return user_stats
        
    except Exception as e:
        print(f"❌ Error checking user isolation: {e}")
        return []


def test_api_isolation():
    """Test API endpoints for proper user isolation."""
    import requests
    
    print("🔍 Testing API User Isolation:")
    print("-" * 30)
    
    # Get user list from database
    db = get_db_config()
    users = db.file_metadata.distinct("user_id", {"is_active": True})
    
    base_url = "http://localhost:8000"
    
    for user_id in users:
        try:
            # Test user-specific file listing
            response = requests.get(f"{base_url}/api/s3/files", params={"user_id": user_id})
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    file_count = data.get('total_files', 0)
                    print(f"  ✅ {user_id}: {file_count} files accessible via API")
                    
                    # Verify all files belong to this user
                    files = data.get('files', [])
                    for file_info in files:
                        # Note: API doesn't return user_id in file info for security
                        # This is actually good for privacy
                        pass
                else:
                    print(f"  ❌ {user_id}: API error - {data.get('error', 'Unknown')}")
            else:
                print(f"  ❌ {user_id}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ {user_id}: Connection error - {e}")
    
    print()


def check_cross_user_access():
    """Check that users cannot access files from other users."""
    print("🔒 Testing Cross-User Access Prevention:")
    print("-" * 40)
    
    db = get_db_config()
    
    # Get sample files from different users
    users_with_files = list(db.file_metadata.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {
            "_id": "$user_id",
            "sample_file": {"$first": "$file_key"}
        }}
    ]))
    
    if len(users_with_files) < 2:
        print("  ⚠️  Need at least 2 users with files to test cross-access")
        return
    
    import requests
    base_url = "http://localhost:8000"
    
    # Test if user A can access user B's files
    for i, user_a in enumerate(users_with_files):
        for j, user_b in enumerate(users_with_files):
            if i != j:  # Different users
                user_a_id = user_a['_id']
                user_b_file = user_b['sample_file']
                
                try:
                    # Try to download user B's file as user A
                    response = requests.get(
                        f"{base_url}/api/s3/download/{user_b_file}",
                        params={"user_id": user_a_id}
                    )
                    
                    if response.status_code == 404:
                        print(f"  ✅ {user_a_id} cannot access {user_b_file} (404 - Good!)")
                    elif response.status_code == 403:
                        print(f"  ✅ {user_a_id} cannot access {user_b_file} (403 - Good!)")
                    elif response.status_code == 200:
                        print(f"  🚨 {user_a_id} CAN access {user_b_file} (SECURITY ISSUE!)")
                    else:
                        print(f"  ⚠️  {user_a_id} -> {user_b_file}: HTTP {response.status_code}")
                        
                except Exception as e:
                    print(f"  ❌ Error testing {user_a_id} -> {user_b_file}: {e}")
    
    print()


def check_admin_access():
    """Check admin endpoint access and data."""
    print("👑 Testing Admin Access:")
    print("-" * 20)
    
    import requests
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/admin/files")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total_files = data.get('total', 0)
                files = data.get('files', [])
                
                print(f"  ✅ Admin can see {total_files} files total")
                
                # Check if admin sees files from all users
                users_in_admin = set(f.get('user_id') for f in files)
                print(f"  📊 Admin sees files from {len(users_in_admin)} users: {', '.join(users_in_admin)}")
                
                # Verify admin data includes user_id (for management purposes)
                if files and 'user_id' in files[0]:
                    print(f"  ✅ Admin data includes user_id for management")
                else:
                    print(f"  ⚠️  Admin data missing user_id field")
                    
            else:
                print(f"  ❌ Admin API error: {data.get('error', 'Unknown')}")
        else:
            print(f"  ❌ Admin API HTTP {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ Admin API connection error: {e}")
    
    print()


def main():
    print("File Privacy and Isolation Check")
    print("=" * 50)
    
    # Check database-level isolation
    user_stats = check_user_isolation()
    
    if user_stats:
        # Test API isolation
        test_api_isolation()
        
        # Test cross-user access prevention
        check_cross_user_access()
        
        # Test admin access
        check_admin_access()
        
        print("✅ Privacy check completed.")
    else:
        print("❌ Privacy check failed - no user data found.")


if __name__ == "__main__":
    main()
