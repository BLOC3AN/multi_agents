#!/usr/bin/env python3
"""
Script to create demo users for authentication testing
"""
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config, User

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_demo_users():
    """Create demo users for testing."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Demo users data
        demo_users = [
            {
                "user_id": "admin",
                "password": "admin123",
                "display_name": "Administrator",
                "email": "admin@example.com"
            },
            {
                "user_id": "user1",
                "password": "user1123",
                "display_name": "Demo User 1",
                "email": "user1@example.com"
            },
            {
                "user_id": "user2",
                "password": "user2123",
                "display_name": "Demo User 2",
                "email": "user2@example.com"
            },
            {
                "user_id": "test",
                "password": "test123",
                "display_name": "Test User",
                "email": "test@example.com"
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for user_data in demo_users:
            # Check if user exists
            existing_user = db_config.users.find_one({"user_id": user_data["user_id"]})
            
            if not existing_user:
                # Create new user
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
                
                print(f"✅ Created user: {user_data['user_id']} / {user_data['password']}")
            else:
                # Update existing user with password hash if missing
                if not existing_user.get("password_hash"):
                    db_config.users.update_one(
                        {"user_id": user_data["user_id"]},
                        {
                            "$set": {
                                "password_hash": hash_password(user_data["password"]),
                                "updated_at": datetime.utcnow().isoformat()
                            }
                        }
                    )
                    updated_count += 1
                    print(f"🔄 Updated user: {user_data['user_id']} / {user_data['password']}")
                else:
                    print(f"ℹ️  User exists: {user_data['user_id']} / {user_data['password']}")
        
        print("\n" + "="*50)
        if created_count > 0:
            print(f"🎉 Created {created_count} new users")
        if updated_count > 0:
            print(f"🔄 Updated {updated_count} existing users")
        if created_count == 0 and updated_count == 0:
            print("ℹ️  All demo users already exist with passwords")
        
        print("\n📋 Demo Login Credentials:")
        print("-" * 30)
        for user_data in demo_users:
            print(f"  {user_data['user_id']} / {user_data['password']}")
        
        print("\n🌐 You can now test authentication at:")
        print("  - React Frontend: http://localhost:3000")
        print("  - Auth API Docs: http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Error creating demo users: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🔐 Creating demo users for Multi-Agent System...")
    print("=" * 50)
    
    success = create_demo_users()
    
    if success:
        print("\n✅ Demo users setup completed successfully!")
    else:
        print("\n❌ Failed to setup demo users")
        sys.exit(1)
