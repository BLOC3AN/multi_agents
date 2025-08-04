#!/usr/bin/env python3
"""
Script to create default admin user for the system
"""
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.database.models import get_db_config, User, Admin, create_admin

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_admin_user():
    """Create default admin user in admins collection."""
    try:
        # Get database connection
        db_config = get_db_config()

        # Check if admin user already exists in admins collection
        existing_admin = db_config.admins.find_one({"admin_id": "admin"})

        if existing_admin:
            print("✅ Admin user already exists in admins collection")
            print(f"   Username: admin")
            print(f"   Display Name: {existing_admin.get('display_name', 'N/A')}")
            print(f"   Role: {existing_admin.get('role', 'N/A')}")
            print(f"   Created: {existing_admin.get('created_at', 'N/A')}")
            return True

        # Use the new create_admin function
        success = create_admin(
            admin_id="admin",
            password="admin123",  # Default password
            display_name="Administrator",
            email="admin@example.com",
            role="super_admin",
            can_manage_users=True,
            can_manage_system=True,
            can_view_logs=True
        )

        if success:
            print("🎉 Admin user created successfully in admins collection!")
            print(f"   Username: admin")
            print(f"   Password: admin123")
            print(f"   Display Name: Administrator")
            print(f"   Email: admin@example.com")
            print(f"   Role: super_admin")
            print("")
            print("🔐 You can now login with these credentials")
            print("💡 Please change the password after first login")
        else:
            print("❌ Failed to create admin user")
            return False

    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False

    return True

def create_demo_users():
    """Create some demo users for testing (still in users collection)."""
    try:
        db_config = get_db_config()

        demo_users = [
            {
                "user_id": "demo",
                "password": "demo123",
                "display_name": "Demo User",
                "email": "demo@example.com"
            },
            {
                "user_id": "test",
                "password": "test123",
                "display_name": "Test User",
                "email": "test@example.com"
            }
        ]

        created_count = 0

        for user_data in demo_users:
            # Check if user exists
            existing_user = db_config.users.find_one({"user_id": user_data["user_id"]})

            if not existing_user:
                # Create user (demo users remain in users collection)
                demo_user = User(
                    user_id=user_data["user_id"],
                    password_hash=hash_password(user_data["password"]),
                    display_name=user_data["display_name"],
                    email=user_data["email"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )

                user_doc = demo_user.to_dict()
                db_config.users.insert_one(user_doc)
                created_count += 1

                print(f"✅ Created demo user: {user_data['user_id']} / {user_data['password']}")

        if created_count > 0:
            print(f"🎉 Created {created_count} demo users in users collection")
        else:
            print("ℹ️  All demo users already exist")

    except Exception as e:
        print(f"❌ Error creating demo users: {e}")


def create_demo_admins():
    """Create some demo admin users for testing."""
    try:
        demo_admins = [
            {
                "admin_id": "demo_admin",
                "password": "demo123",
                "display_name": "Demo Admin",
                "email": "demo.admin@example.com",
                "role": "admin"
            },
            {
                "admin_id": "test_admin",
                "password": "test123",
                "display_name": "Test Admin",
                "email": "test.admin@example.com",
                "role": "admin"
            }
        ]

        created_count = 0

        for admin_data in demo_admins:
            success = create_admin(
                admin_id=admin_data["admin_id"],
                password=admin_data["password"],
                display_name=admin_data["display_name"],
                email=admin_data["email"],
                role=admin_data["role"]
            )

            if success:
                created_count += 1
                print(f"✅ Created demo admin: {admin_data['admin_id']} / {admin_data['password']}")

        if created_count > 0:
            print(f"🎉 Created {created_count} demo admins in admins collection")
        else:
            print("ℹ️  All demo admins already exist")

    except Exception as e:
        print(f"❌ Error creating demo admins: {e}")

if __name__ == "__main__":
    print("🔧 Setting up default users and admins for Multi-Agent System")
    print("=" * 60)

    # Create admin user
    if create_admin_user():
        print("")

        # Ask if user wants demo users
        response = input("📝 Create demo users? (y/n): ").lower().strip()
        if response == 'y':
            create_demo_users()

        print("")

        # Ask if user wants demo admins
        response = input("📝 Create demo admins? (y/n): ").lower().strip()
        if response == 'y':
            create_demo_admins()

    print("")
    print("🚀 Setup complete! You can now start the system:")
    print("   make up-gui")
    print("   http://localhost:8502")
    print("")
    print("📋 Summary:")
    print("   - Admin users are now stored in 'admins' collection")
    print("   - Regular users remain in 'users' collection")
    print("   - Authentication supports both types of accounts")
