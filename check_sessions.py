#!/usr/bin/env python3
"""
Script to check sessions in database
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.database.models import get_db_config

def check_sessions():
    """Check sessions in database."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        print("🔍 Checking sessions in database...")
        print("=" * 50)
        
        # Get all sessions
        all_sessions = list(db_config.sessions.find())
        
        print(f"📊 Total sessions: {len(all_sessions)}")
        print("")
        
        if all_sessions:
            for session in all_sessions:
                print(f"Session ID: {session.get('session_id')}")
                print(f"User ID: {session.get('user_id')}")
                print(f"Created: {session.get('created_at')}")
                print(f"Updated: {session.get('updated_at')}")
                print(f"Active: {session.get('is_active', True)}")
                
                # Count messages for this session
                message_count = db_config.messages.count_documents({"session_id": session.get("session_id")})
                print(f"Messages: {message_count}")
                print("-" * 30)
        else:
            print("❌ No sessions found in database")
            
        # Check by specific user
        print("\n🔍 Checking sessions by user...")
        users = ["hailt", "admin", "test_user_822462a9"]
        
        for user_id in users:
            user_sessions = list(db_config.sessions.find({"user_id": user_id}))
            print(f"👤 {user_id}: {len(user_sessions)} sessions")
            
            for session in user_sessions:
                print(f"   📝 {session.get('session_id')[:8]}... ({session.get('updated_at')})")
                
    except Exception as e:
        print(f"❌ Error checking sessions: {e}")

if __name__ == "__main__":
    check_sessions()
