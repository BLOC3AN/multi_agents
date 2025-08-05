#!/usr/bin/env python3
"""
Script to create super admin with full control permissions.
This admin will have complete access to all system functions.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config, create_admin


def create_super_admin():
    """Create super admin with full control permissions."""
    print("🔧 Creating Super Admin with Full Control")
    print("=" * 50)
    
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Super admin details
        admin_data = {
            "admin_id": "superadmin",
            "password": "SuperAdmin@2024",
            "display_name": "Super Administrator", 
            "email": "superadmin@system.local",
            "role": "super_admin",
            "store_plain_password": True,  # Store plain password for reference
        }
        
        print(f"👤 Creating admin: {admin_data['admin_id']}")
        print(f"📧 Email: {admin_data['email']}")
        print(f"🔑 Password: {admin_data['password']}")
        print(f"👑 Role: {admin_data['role']}")
        
        # Create super admin
        success = create_admin(**admin_data)
        
        if success:
            print("\n🎉 Super Admin created successfully!")
            print("\n🔐 Login Credentials:")
            print(f"   Username: {admin_data['admin_id']}")
            print(f"   Password: {admin_data['password']}")
            
            print("\n👑 Full Control Permissions:")
            print("   ✅ Can manage users")
            print("   ✅ Can manage system")
            print("   ✅ Can view logs")
            print("   ✅ Can delete users")
            print("   ✅ Can manage admins")
            print("   ✅ Can access all data")
            
            # Verify creation
            verify_admin_creation(admin_data['admin_id'])
            
        else:
            print("\n❌ Failed to create super admin")
            return False
            
    except Exception as e:
        print(f"\n❌ Error creating super admin: {e}")
        return False
    
    return True


def verify_admin_creation(admin_id: str):
    """Verify that the admin was created correctly."""
    print(f"\n🔍 Verifying admin creation: {admin_id}")
    
    try:
        db_config = get_db_config()
        admin = db_config.admins.find_one({"admin_id": admin_id})
        
        if admin:
            print("✅ Admin found in database")
            print(f"   Admin ID: {admin.get('admin_id')}")
            print(f"   Display Name: {admin.get('display_name')}")
            print(f"   Email: {admin.get('email')}")
            print(f"   Role: {admin.get('role')}")
            print(f"   Has Password: {bool(admin.get('password'))}")
            print(f"   Has Password Hash: {bool(admin.get('password_hash'))}")
            print(f"   Is Active: {admin.get('is_active')}")
            print(f"   Created At: {admin.get('created_at')}")
            
            # Check permissions
            permissions = [
                ('can_manage_users', admin.get('can_manage_users')),
                ('can_manage_system', admin.get('can_manage_system')),
                ('can_view_logs', admin.get('can_view_logs')),
                ('can_delete_users', admin.get('can_delete_users')),
                ('can_manage_admins', admin.get('can_manage_admins')),
                ('can_access_all_data', admin.get('can_access_all_data')),
            ]
            
            print("\n🔐 Permissions:")
            for perm_name, perm_value in permissions:
                status = "✅" if perm_value else "❌"
                print(f"   {status} {perm_name}: {perm_value}")
                
        else:
            print("❌ Admin not found in database")
            
    except Exception as e:
        print(f"❌ Error verifying admin: {e}")


def create_additional_admins():
    """Create additional admin users for different purposes."""
    print("\n🔧 Creating Additional Admin Users")
    print("=" * 40)
    
    additional_admins = [
        {
            "admin_id": "admin",
            "password": "admin123",
            "display_name": "Default Administrator",
            "email": "admin@system.local",
            "role": "admin",
            "store_plain_password": True,
        },
        {
            "admin_id": "hailt_admin",
            "password": "HaiLT@2024",
            "display_name": "Hai Le Thanh - Admin",
            "email": "hailt@admin.local",
            "role": "super_admin",
            "store_plain_password": True,
        }
    ]
    
    created_count = 0
    
    for admin_data in additional_admins:
        print(f"\n👤 Creating: {admin_data['admin_id']}")
        
        success = create_admin(**admin_data)
        
        if success:
            created_count += 1
            print(f"✅ Created: {admin_data['admin_id']} / {admin_data['password']}")
        else:
            print(f"⚠️ Skipped: {admin_data['admin_id']} (already exists)")
    
    print(f"\n📊 Summary: {created_count} new admins created")


def list_all_admins():
    """List all admins in the system."""
    print("\n📋 Current Admins in System")
    print("=" * 30)
    
    try:
        db_config = get_db_config()
        admins = list(db_config.admins.find({}))
        
        if not admins:
            print("❌ No admins found")
            return
        
        print(f"📊 Total admins: {len(admins)}")
        
        for i, admin in enumerate(admins, 1):
            print(f"\n{i}. {admin.get('admin_id', 'unknown')}")
            print(f"   Display Name: {admin.get('display_name', 'N/A')}")
            print(f"   Email: {admin.get('email', 'N/A')}")
            print(f"   Role: {admin.get('role', 'N/A')}")
            print(f"   Password: {admin.get('password', 'N/A')}")
            print(f"   Active: {admin.get('is_active', False)}")
            print(f"   Created: {admin.get('created_at', 'N/A')}")
            
            # Show key permissions
            key_perms = []
            if admin.get('can_manage_users'): key_perms.append('Users')
            if admin.get('can_manage_system'): key_perms.append('System')
            if admin.get('can_delete_users'): key_perms.append('Delete')
            if admin.get('can_manage_admins'): key_perms.append('Admins')
            
            print(f"   Permissions: {', '.join(key_perms) if key_perms else 'None'}")
            
    except Exception as e:
        print(f"❌ Error listing admins: {e}")


def main():
    print("Super Admin Creation Script")
    print("=" * 50)
    
    # Create super admin
    if create_super_admin():
        print("\n" + "="*50)
        
        # Ask if user wants additional admins
        response = input("\n📝 Create additional admin users? (y/n): ").lower().strip()
        if response == 'y':
            create_additional_admins()
        
        # List all admins
        list_all_admins()
        
        print("\n🎯 Next Steps:")
        print("1. Use these credentials to login to admin panel")
        print("2. Change passwords after first login")
        print("3. Create additional users as needed")
        print("4. Configure system settings")
        
        print("\n🔗 Access Points:")
        print("- Admin Panel: http://localhost:3000/admin")
        print("- API Docs: http://localhost:8000/docs")
        
    else:
        print("\n❌ Failed to create super admin")
        sys.exit(1)


if __name__ == "__main__":
    main()
