#!/usr/bin/env python3
"""
Fix admin authentication by ensuring correct password hashing.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config
from auth_server import hash_password, verify_password


def fix_admin_passwords():
    """Fix admin passwords using correct hash function."""
    print("🔧 Fixing Admin Authentication")
    print("=" * 40)
    
    try:
        db = get_db_config()
        
        # Admin accounts to fix
        admin_accounts = [
            {
                "admin_id": "admin",
                "password": "admin123",
                "display_name": "Default Administrator"
            },
            {
                "admin_id": "superadmin", 
                "password": "SuperAdmin@2024",
                "display_name": "Super Administrator"
            },
            {
                "admin_id": "hailt_admin",
                "password": "HaiLT@2024", 
                "display_name": "Hai Le Thanh - Admin"
            }
        ]
        
        for admin_data in admin_accounts:
            admin_id = admin_data["admin_id"]
            password = admin_data["password"]
            
            print(f"\n👤 Fixing: {admin_id}")
            
            # Check if admin exists
            admin = db.admins.find_one({"admin_id": admin_id})
            if not admin:
                print(f"❌ Admin not found: {admin_id}")
                continue
            
            # Generate correct password hash
            correct_hash = hash_password(password)
            
            # Test verification
            if verify_password(password, correct_hash):
                print(f"✅ Password hash verification successful")
            else:
                print(f"❌ Password hash verification failed")
                continue
            
            # Update admin with correct hash
            result = db.admins.update_one(
                {"admin_id": admin_id},
                {
                    "$set": {
                        "password_hash": correct_hash,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            )
            
            if result.modified_count > 0:
                print(f"✅ Updated password hash for {admin_id}")
                
                # Test login
                test_login(admin_id, password)
            else:
                print(f"❌ Failed to update {admin_id}")
        
    except Exception as e:
        print(f"❌ Error fixing admin passwords: {e}")


def test_login(admin_id: str, password: str):
    """Test login with fixed password."""
    try:
        db = get_db_config()
        admin = db.admins.find_one({"admin_id": admin_id})
        
        if admin:
            stored_hash = admin.get("password_hash")
            if verify_password(password, stored_hash):
                print(f"  ✅ Login test successful for {admin_id}")
            else:
                print(f"  ❌ Login test failed for {admin_id}")
        else:
            print(f"  ❌ Admin not found: {admin_id}")
            
    except Exception as e:
        print(f"  ❌ Login test error: {e}")


def create_test_admin():
    """Create a simple test admin for verification."""
    print("\n🧪 Creating Test Admin")
    print("=" * 25)
    
    try:
        db = get_db_config()
        
        # Simple test admin
        admin_id = "testadmin"
        password = "test123"
        
        # Check if exists
        existing = db.admins.find_one({"admin_id": admin_id})
        if existing:
            print(f"⚠️ Test admin already exists: {admin_id}")
            return
        
        # Create with correct hash
        password_hash = hash_password(password)
        
        admin_doc = {
            "admin_id": admin_id,
            "display_name": "Test Administrator",
            "email": "test@admin.local",
            "password": password,  # Store plain for reference
            "password_hash": password_hash,
            "role": "admin",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "can_manage_users": True,
            "can_manage_system": True,
            "can_view_logs": True,
            "can_delete_users": True,
            "can_manage_admins": True,
            "can_access_all_data": True,
        }
        
        db.admins.insert_one(admin_doc)
        print(f"✅ Created test admin: {admin_id} / {password}")
        
        # Test login
        test_login(admin_id, password)
        
    except Exception as e:
        print(f"❌ Error creating test admin: {e}")


def list_all_admins():
    """List all admins with their status."""
    print("\n📋 All Admins Status")
    print("=" * 25)
    
    try:
        db = get_db_config()
        admins = list(db.admins.find({}))
        
        for admin in admins:
            admin_id = admin.get("admin_id")
            password = admin.get("password", "N/A")
            has_hash = bool(admin.get("password_hash"))
            
            print(f"\n👤 {admin_id}")
            print(f"   Password: {password}")
            print(f"   Has Hash: {has_hash}")
            print(f"   Role: {admin.get('role', 'N/A')}")
            print(f"   Active: {admin.get('is_active', False)}")
            
            # Test login if password available
            if password != "N/A":
                test_login(admin_id, password)
                
    except Exception as e:
        print(f"❌ Error listing admins: {e}")


def main():
    print("Admin Authentication Fix Script")
    print("=" * 50)
    
    # Fix existing admin passwords
    fix_admin_passwords()
    
    # Create test admin
    create_test_admin()
    
    # List all admins
    list_all_admins()
    
    print("\n🎯 Next Steps:")
    print("1. Test login via API: curl -X POST http://localhost:8000/auth/login")
    print("2. Test frontend login at: http://localhost:3000/login")
    print("3. Access admin page at: http://localhost:3000/admin")
    
    print("\n🔐 Test Credentials:")
    print("- admin / admin123")
    print("- testadmin / test123")
    print("- superadmin / SuperAdmin@2024")


if __name__ == "__main__":
    main()
