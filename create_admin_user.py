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

from gui.database.models import get_db_config, User

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_admin_user():
    """Create default admin user."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Check if admin user already exists
        existing_admin = db_config.users.find_one({"user_id": "admin"})
        
        if existing_admin:
            print("✅ Admin user already exists")
            print(f"   Username: admin")
            print(f"   Display Name: {existing_admin.get('display_name', 'N/A')}")
            print(f"   Created: {existing_admin.get('created_at', 'N/A')}")
            return
        
        # Create admin user
        admin_user = User(
            user_id="admin",
            password_hash=hash_password("admin123"),  # Default password
            display_name="Administrator",
            email="admin@example.com",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        user_doc = admin_user.to_dict()
        db_config.users.insert_one(user_doc)
        
        print("🎉 Admin user created successfully!")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Display Name: Administrator")
        print(f"   Email: admin@example.com")
        print("")
        print("🔐 You can now login with these credentials")
        print("💡 Please change the password after first login")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        return False
    
    return True

def create_demo_users():
    """Create some demo users for testing."""
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
                # Create user
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
            print(f"🎉 Created {created_count} demo users")
        else:
            print("ℹ️  All demo users already exist")
            
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")

if __name__ == "__main__":
    print("🔧 Setting up default users for Multi-Agent System")
    print("=" * 50)
    
    # Create admin user
    if create_admin_user():
        print("")
        
        # Ask if user wants demo users
        response = input("📝 Create demo users? (y/n): ").lower().strip()
        if response == 'y':
            create_demo_users()
    
    print("")
    print("🚀 Setup complete! You can now start the system:")
    print("   make up-gui")
    print("   http://localhost:8502")
