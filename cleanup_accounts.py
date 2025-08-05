#!/usr/bin/env python3
"""
Script to cleanup duplicate accounts and verify account isolation
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config

def cleanup_duplicates():
    """Find and cleanup duplicate accounts between users and admins collections."""
    print("🧹 Account Cleanup & Verification Tool")
    print("=" * 50)
    
    try:
        db_config = get_db_config()
        
        # Get all users and admins
        users = list(db_config.users.find({}, {"user_id": 1, "role": 1, "password_hash": 1}))
        admins = list(db_config.admins.find({}, {"admin_id": 1, "role": 1, "password_hash": 1}))
        
        print(f"📊 Current Status:")
        print(f"   Users collection: {len(users)} accounts")
        print(f"   Admins collection: {len(admins)} accounts")
        print()
        
        # Find duplicates
        user_ids = {user['user_id'] for user in users}
        admin_ids = {admin['admin_id'] for admin in admins}
        duplicates = user_ids.intersection(admin_ids)
        
        if duplicates:
            print(f"⚠️  Found {len(duplicates)} duplicate accounts:")
            for dup_id in duplicates:
                print(f"   - {dup_id}")
                
                # Show details
                user_doc = db_config.users.find_one({"user_id": dup_id})
                admin_doc = db_config.admins.find_one({"admin_id": dup_id})
                
                print(f"     Users:  role={user_doc.get('role')}, has_password={bool(user_doc.get('password_hash'))}")
                print(f"     Admins: role={admin_doc.get('role')}, has_password={bool(admin_doc.get('password_hash'))}")
                
                # Auto-cleanup: Remove from users if exists in admins with super_admin role
                if admin_doc and admin_doc.get('role') == 'super_admin':
                    print(f"     🗑️  Auto-removing duplicate from users collection...")
                    result = db_config.users.delete_one({"user_id": dup_id})
                    if result.deleted_count > 0:
                        print(f"     ✅ Removed duplicate user account")
                    else:
                        print(f"     ❌ Failed to remove duplicate")
                print()
        else:
            print("✅ No duplicate accounts found")
            print()
        
        # Show final status
        users_final = list(db_config.users.find({}, {"user_id": 1, "role": 1}))
        admins_final = list(db_config.admins.find({}, {"admin_id": 1, "role": 1}))
        
        print("📋 Final Account Summary:")
        print("   Users Collection:")
        for user in users_final:
            print(f"     - {user['user_id']} (role: {user.get('role', 'None')})")
        
        print("   Admins Collection:")
        for admin in admins_final:
            print(f"     - {admin['admin_id']} (role: {admin.get('role', 'None')})")
        
        print()
        print("✅ Cleanup completed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False

def verify_account_isolation():
    """Verify that accounts are properly isolated by role."""
    print("\n🔍 Account Isolation Verification")
    print("-" * 30)
    
    try:
        db_config = get_db_config()
        
        # Check users collection roles
        users = list(db_config.users.find({}, {"user_id": 1, "role": 1}))
        admins = list(db_config.admins.find({}, {"admin_id": 1, "role": 1}))
        
        print("Users Collection Roles:")
        user_roles = {}
        for user in users:
            role = user.get('role', 'None')
            user_roles[role] = user_roles.get(role, 0) + 1
            if role not in ['user', 'editor']:
                print(f"   ⚠️  {user['user_id']}: {role} (should be 'user' or 'editor')")
        
        for role, count in user_roles.items():
            print(f"   - {role}: {count} accounts")
        
        print("\nAdmins Collection Roles:")
        admin_roles = {}
        for admin in admins:
            role = admin.get('role', 'None')
            admin_roles[role] = admin_roles.get(role, 0) + 1
            if role != 'super_admin':
                print(f"   ⚠️  {admin['admin_id']}: {role} (should be 'super_admin')")
        
        for role, count in admin_roles.items():
            print(f"   - {role}: {count} accounts")
        
        # Validation
        issues = []
        for user in users:
            role = user.get('role')
            if role not in ['user', 'editor']:
                issues.append(f"User '{user['user_id']}' has invalid role: {role}")
        
        for admin in admins:
            role = admin.get('role')
            if role != 'super_admin':
                issues.append(f"Admin '{admin['admin_id']}' has invalid role: {role}")
        
        if issues:
            print(f"\n❌ Found {len(issues)} issues:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("\n✅ All accounts have correct role isolation!")
            return True
            
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        return False

if __name__ == "__main__":
    try:
        # Run cleanup
        cleanup_success = cleanup_duplicates()
        
        # Run verification
        verify_success = verify_account_isolation()
        
        if cleanup_success and verify_success:
            print("\n🎉 All checks passed! Account system is properly configured.")
        else:
            print("\n💥 Some issues found. Please review the output above.")
            
    except KeyboardInterrupt:
        print(f"\n\n👋 Cleanup cancelled!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
