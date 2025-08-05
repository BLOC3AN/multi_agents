#!/usr/bin/env python3
"""
Script to create user accounts for the Multi-Agent System
Supports creating both regular users and super admin accounts
"""
import sys
import hashlib
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config, User, Admin, create_admin

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with salt."""
    salt = "multi_agent_salt_2024"
    return hashlib.sha256((password + salt).encode()).hexdigest()

def create_user_account(user_id: str, password: str, display_name: str = None, 
                       email: str = None, role: str = "user"):
    """Create a regular user account in users collection."""
    try:
        db_config = get_db_config()
        
        # Check if user already exists
        existing_user = db_config.users.find_one({"user_id": user_id})
        if existing_user:
            print(f"❌ User '{user_id}' already exists!")
            return False
        
        # Create user
        user = User(
            user_id=user_id,
            password_hash=hash_password(password),
            display_name=display_name or user_id,
            email=email or f"{user_id}@system.local",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add role to user document
        user_doc = user.to_dict()
        user_doc["role"] = role
        
        db_config.users.insert_one(user_doc)
        
        print(f"✅ User account created successfully!")
        print(f"   Username: {user_id}")
        print(f"   Password: {password}")
        print(f"   Display Name: {display_name or user_id}")
        print(f"   Email: {email or f'{user_id}@system.local'}")
        print(f"   Role: {role}")
        print(f"   Collection: users")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def create_super_admin(admin_id: str, password: str, display_name: str = None, 
                      email: str = None):
    """Create a super admin account in admins collection."""
    try:
        db_config = get_db_config()
        
        # Check if admin already exists
        existing_admin = db_config.admins.find_one({"admin_id": admin_id})
        if existing_admin:
            print(f"❌ Super admin '{admin_id}' already exists!")
            return False
        
        # Use create_admin function
        success = create_admin(
            admin_id=admin_id,
            password=password,
            display_name=display_name or admin_id,
            email=email or f"{admin_id}@admin.local",
            role="super_admin"
        )
        
        if success:
            print(f"✅ Super admin account created successfully!")
            print(f"   Username: {admin_id}")
            print(f"   Password: {password}")
            print(f"   Display Name: {display_name or admin_id}")
            print(f"   Email: {email or f'{admin_id}@admin.local'}")
            print(f"   Role: super_admin")
            print(f"   Collection: admins")
            return True
        else:
            print(f"❌ Failed to create super admin")
            return False
            
    except Exception as e:
        print(f"❌ Error creating super admin: {e}")
        return False

def interactive_create():
    """Interactive account creation."""
    print("🔧 Multi-Agent System - Account Creator")
    print("=" * 50)
    
    while True:
        print("\n📋 Choose account type:")
        print("1. Regular User (role: user)")
        print("2. Editor User (role: editor)")
        print("3. Super Admin (role: super_admin)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "4":
            break
            
        if choice not in ["1", "2", "3"]:
            print("❌ Invalid choice! Please enter 1, 2, 3, or 4.")
            continue
        
        # Get account details
        print(f"\n📝 Enter account details:")
        username = input("Username: ").strip()
        if not username:
            print("❌ Username cannot be empty!")
            continue
            
        password = input("Password: ").strip()
        if not password:
            print("❌ Password cannot be empty!")
            continue
            
        display_name = input("Display Name (optional): ").strip()
        email = input("Email (optional): ").strip()
        
        print(f"\n🔍 Creating account...")
        
        if choice == "1":
            # Regular user
            success = create_user_account(username, password, display_name, email, "user")
        elif choice == "2":
            # Editor user
            success = create_user_account(username, password, display_name, email, "editor")
        elif choice == "3":
            # Super admin
            success = create_super_admin(username, password, display_name, email)
        
        if success:
            print(f"\n🎉 Account created successfully!")
        else:
            print(f"\n❌ Failed to create account!")
        
        print("\n" + "-" * 50)

def quick_create():
    """Quick create with command line arguments."""
    if len(sys.argv) < 4:
        print("❌ Usage: python create_account.py <type> <username> <password> [display_name] [email]")
        print("   Types: user, editor, admin")
        print("   Example: python create_account.py user john john123 'John Doe' john@example.com")
        return
    
    account_type = sys.argv[1].lower()
    username = sys.argv[2]
    password = sys.argv[3]
    display_name = sys.argv[4] if len(sys.argv) > 4 else None
    email = sys.argv[5] if len(sys.argv) > 5 else None
    
    print(f"🔧 Creating {account_type} account: {username}")
    
    if account_type == "user":
        success = create_user_account(username, password, display_name, email, "user")
    elif account_type == "editor":
        success = create_user_account(username, password, display_name, email, "editor")
    elif account_type == "admin":
        success = create_super_admin(username, password, display_name, email)
    else:
        print("❌ Invalid account type! Use: user, editor, or admin")
        return
    
    if success:
        print(f"\n🎉 {account_type.title()} account created successfully!")
    else:
        print(f"\n❌ Failed to create {account_type} account!")

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            # Command line mode
            quick_create()
        else:
            # Interactive mode
            interactive_create()
            
        print(f"\n🚀 You can now login at: http://localhost:3000")
        
    except KeyboardInterrupt:
        print(f"\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
