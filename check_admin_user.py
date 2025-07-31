#!/usr/bin/env python3
"""
Script to check admin user in database
"""
import sys
import hashlib
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def check_admin_user():
    """Check admin user in database."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Find admin user
        admin_user = db_config.users.find_one({"user_id": "admin"})
        
        if not admin_user:
            print("❌ Admin user not found in database")
            return False
        
        print("✅ Admin user found:")
        print(f"  User ID: {admin_user.get('user_id')}")
        print(f"  Display Name: {admin_user.get('display_name')}")
        print(f"  Email: {admin_user.get('email')}")
        print(f"  Is Active: {admin_user.get('is_active')}")
        print(f"  Has Password Hash: {'Yes' if admin_user.get('password_hash') else 'No'}")
        
        if admin_user.get('password_hash'):
            stored_hash = admin_user.get('password_hash')
            expected_hash = hash_password("admin123")
            
            print(f"\n🔐 Password Hash Check:")
            print(f"  Stored Hash: {stored_hash[:20]}...")
            print(f"  Expected Hash: {expected_hash[:20]}...")
            print(f"  Match: {'✅ Yes' if stored_hash == expected_hash else '❌ No'}")
            
            if stored_hash != expected_hash:
                print(f"\n🔧 Fixing password hash...")
                # Update password hash
                result = db_config.users.update_one(
                    {"user_id": "admin"},
                    {"$set": {"password_hash": expected_hash}}
                )
                
                if result.modified_count > 0:
                    print("✅ Password hash updated successfully")
                    return True
                else:
                    print("❌ Failed to update password hash")
                    return False
        else:
            print(f"\n🔧 Adding password hash...")
            # Add password hash
            expected_hash = hash_password("admin123")
            result = db_config.users.update_one(
                {"user_id": "admin"},
                {"$set": {"password_hash": expected_hash}}
            )
            
            if result.modified_count > 0:
                print("✅ Password hash added successfully")
                return True
            else:
                print("❌ Failed to add password hash")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking admin user: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking admin user in database...")
    print("=" * 50)
    
    success = check_admin_user()
    
    if success:
        print("\n✅ Admin user check completed!")
        print("\n🔐 You can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
    else:
        print("\n❌ Admin user check failed")
        sys.exit(1)
