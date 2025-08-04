#!/usr/bin/env python3
"""
Migration script to move admin users from 'users' collection to 'admins' collection.
This script safely migrates existing admin accounts while preserving all data.
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add src to path to import models
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from database.models import get_db_config, Admin


def find_admin_users() -> List[Dict[str, Any]]:
    """Find users that should be migrated to admins collection."""
    try:
        db_config = get_db_config()
        
        # Find users with admin-like characteristics
        # You can customize this query based on your criteria
        admin_criteria = [
            {"user_id": "admin"},  # Default admin user
            {"user_id": {"$regex": "^admin", "$options": "i"}},  # Users starting with "admin"
            {"email": {"$regex": "admin", "$options": "i"}},  # Users with "admin" in email
            # Add more criteria as needed
        ]
        
        admin_users = []
        for criteria in admin_criteria:
            users = list(db_config.users.find(criteria))
            for user in users:
                if user not in admin_users:  # Avoid duplicates
                    admin_users.append(user)
        
        return admin_users
        
    except Exception as e:
        print(f"❌ Error finding admin users: {e}")
        return []


def migrate_user_to_admin(user_doc: Dict[str, Any]) -> bool:
    """Migrate a single user to admin collection."""
    try:
        db_config = get_db_config()
        
        # Check if admin already exists in admins collection
        existing_admin = db_config.admins.find_one({"admin_id": user_doc["user_id"]})
        if existing_admin:
            print(f"⚠️  Admin already exists in admins collection: {user_doc['user_id']}")
            return True
        
        # Create admin document
        admin_data = {
            "admin_id": user_doc["user_id"],
            "display_name": user_doc.get("display_name"),
            "email": user_doc.get("email"),
            "password_hash": user_doc.get("password_hash"),
            "is_active": user_doc.get("is_active", True),
            "created_at": user_doc.get("created_at"),
            "updated_at": datetime.utcnow().isoformat(),
            "last_login": user_doc.get("last_login"),
            "role": "admin",  # Default role
            "can_manage_users": True,
            "can_manage_system": True,
            "can_view_logs": True,
            "permissions": user_doc.get("preferences", {}),  # Migrate preferences as permissions
            "notes": f"Migrated from users collection on {datetime.utcnow().isoformat()}"
        }
        
        # Insert into admins collection
        db_config.admins.insert_one(admin_data)
        print(f"✅ Migrated user to admin: {user_doc['user_id']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error migrating user {user_doc.get('user_id', 'unknown')}: {e}")
        return False


def remove_migrated_users(migrated_user_ids: List[str], confirm: bool = False) -> bool:
    """Remove migrated users from users collection."""
    try:
        if not confirm:
            print("⚠️  Skipping removal of migrated users (confirm=False)")
            return True
            
        db_config = get_db_config()
        
        for user_id in migrated_user_ids:
            result = db_config.users.delete_one({"user_id": user_id})
            if result.deleted_count > 0:
                print(f"🗑️  Removed user from users collection: {user_id}")
            else:
                print(f"⚠️  User not found in users collection: {user_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error removing migrated users: {e}")
        return False


def main():
    """Main migration function."""
    print("🔄 Starting admin migration process...")
    print("=" * 60)
    
    # Find admin users
    print("1. Finding admin users in users collection...")
    admin_users = find_admin_users()
    
    if not admin_users:
        print("ℹ️  No admin users found to migrate.")
        return
    
    print(f"📋 Found {len(admin_users)} admin user(s) to migrate:")
    for user in admin_users:
        print(f"   - {user['user_id']} ({user.get('display_name', 'No display name')})")
    
    # Confirm migration
    print("\n2. Confirming migration...")
    response = input("🤔 Do you want to proceed with migration? (y/n): ").lower().strip()
    if response != 'y':
        print("❌ Migration cancelled by user.")
        return
    
    # Migrate users
    print("\n3. Migrating users to admins collection...")
    migrated_user_ids = []
    
    for user_doc in admin_users:
        if migrate_user_to_admin(user_doc):
            migrated_user_ids.append(user_doc["user_id"])
    
    if not migrated_user_ids:
        print("❌ No users were successfully migrated.")
        return
    
    print(f"\n✅ Successfully migrated {len(migrated_user_ids)} user(s) to admins collection.")
    
    # Ask about removing from users collection
    print("\n4. Cleanup options...")
    print("⚠️  The migrated users still exist in the users collection.")
    print("   You can:")
    print("   - Keep them in both collections (safer)")
    print("   - Remove them from users collection (cleaner)")
    
    cleanup_response = input("🗑️  Remove migrated users from users collection? (y/n): ").lower().strip()
    if cleanup_response == 'y':
        confirm_response = input("⚠️  Are you sure? This cannot be undone! (y/n): ").lower().strip()
        if confirm_response == 'y':
            remove_migrated_users(migrated_user_ids, confirm=True)
        else:
            print("ℹ️  Keeping users in both collections.")
    else:
        print("ℹ️  Keeping users in both collections.")
    
    print("\n🎉 Migration completed!")
    print("=" * 60)
    print("📝 Next steps:")
    print("   1. Test admin login functionality")
    print("   2. Update create_admin_user.py to use admins collection")
    print("   3. Restart your application services")
    print("   4. Verify everything works correctly")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user.")
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        sys.exit(1)
