#!/usr/bin/env python3
"""
Helper script to fix MongoDB URI encoding issues
"""
import urllib.parse
import re

def fix_mongodb_uri(uri):
    """Fix MongoDB URI by properly encoding username and password."""
    
    # Pattern to match MongoDB URI with credentials
    pattern = r'mongodb(?:\+srv)?://([^:]+):([^@]+)@(.+)'
    match = re.match(pattern, uri)
    
    if not match:
        print("❌ Invalid MongoDB URI format")
        return None
    
    username, password, rest = match.groups()
    
    # Encode username and password
    encoded_username = urllib.parse.quote_plus(username)
    encoded_password = urllib.parse.quote_plus(password)
    
    # Reconstruct URI
    if uri.startswith('mongodb+srv://'):
        fixed_uri = f"mongodb+srv://{encoded_username}:{encoded_password}@{rest}"
    else:
        fixed_uri = f"mongodb://{encoded_username}:{encoded_password}@{rest}"
    
    return fixed_uri

def main():
    print("🔧 MongoDB URI Fixer")
    print("=" * 50)
    
    # Read current URI from .env
    try:
        with open('.env', 'r') as f:
            content = f.read()
        
        # Find MONGODB_URI line
        for line in content.split('\n'):
            if line.startswith('MONGODB_URI='):
                current_uri = line.split('=', 1)[1]
                print(f"📋 Current URI: {current_uri}")
                
                # Fix URI
                fixed_uri = fix_mongodb_uri(current_uri)
                
                if fixed_uri:
                    print(f"✅ Fixed URI: {fixed_uri}")
                    
                    # Ask if user wants to update .env
                    response = input("\n🔄 Update .env file? (y/n): ")
                    if response.lower() == 'y':
                        # Update .env file
                        new_content = content.replace(
                            f"MONGODB_URI={current_uri}",
                            f"MONGODB_URI={fixed_uri}"
                        )
                        
                        with open('.env', 'w') as f:
                            f.write(new_content)
                        
                        print("✅ .env file updated!")
                        print("🔄 Please restart the application: make restart-gui")
                    else:
                        print("📋 Copy this fixed URI to your .env file:")
                        print(f"MONGODB_URI={fixed_uri}")
                
                return
        
        print("❌ MONGODB_URI not found in .env file")
        
    except FileNotFoundError:
        print("❌ .env file not found")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
