#!/usr/bin/env python3
"""
Script to update existing users with password hashes
"""
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.database.models import get_db_config

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def update_existing_users():
    """Update existing users with password hashes."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Find users without password field
        users_without_password = db_config.users.find({"password": {"$exists": False}})
        
        updated_count = 0
        
        for user in users_without_password:
            user_id = user.get("user_id")
            
            # Set default password based on user_id
            if user_id == "admin":
                default_password = "admin123"
            else:
                default_password = f"{user_id}123"  # user_id + "123"
            
            # Update user with password and hash
            result = db_config.users.update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "password": default_password,  # Store plain password
                        "password_hash": hash_password(default_password),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                updated_count += 1
                print(f"✅ Updated user: {user_id} (password: {default_password})")
        
        if updated_count > 0:
            print(f"\n🎉 Updated {updated_count} users with password hashes")
        else:
            print("ℹ️  All users already have password hashes")
            
        # Show all users
        print("\n📋 Current users in database:")
        all_users = db_config.users.find()
        for user in all_users:
            has_password = "✅" if user.get("password") else "❌"
            password_display = user.get("password", "N/A")
            print(f"   {has_password} {user.get('user_id')} - {user.get('display_name', 'N/A')} (password: {password_display})")
            
    except Exception as e:
        print(f"❌ Error updating users: {e}")

if __name__ == "__main__":
    print("🔧 Updating existing users with password hashes")
    print("=" * 50)
    update_existing_users()
    print("\n🚀 Update complete!")
