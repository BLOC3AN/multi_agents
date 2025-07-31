#!/usr/bin/env python3
"""
Script to create demo sessions for testing
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config, ChatSession

def create_demo_sessions():
    """Create demo sessions for testing."""
    try:
        # Get database connection
        db_config = get_db_config()
        
        # Demo sessions data
        demo_sessions = [
            {
                "session_id": "session_demo_math_001",
                "user_id": "admin",
                "title": "Math Problem Solving",
                "total_messages": 5,
                "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                "is_active": True
            },
            {
                "session_id": "session_demo_writing_002", 
                "user_id": "admin",
                "title": "Creative Writing Help",
                "total_messages": 8,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                "is_active": True
            },
            {
                "session_id": "session_demo_code_003",
                "user_id": "admin", 
                "title": "Python Coding Assistance",
                "total_messages": 12,
                "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "is_active": True
            },
            {
                "session_id": "session_demo_user1_001",
                "user_id": "user1",
                "title": "General Questions",
                "total_messages": 3,
                "created_at": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "updated_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "is_active": True
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for session_data in demo_sessions:
            # Check if session exists
            existing_session = db_config.sessions.find_one({"session_id": session_data["session_id"]})
            
            if not existing_session:
                # Create new session
                db_config.sessions.insert_one(session_data)
                created_count += 1
                print(f"✅ Created session: {session_data['title']} ({session_data['session_id']})")
            else:
                # Update existing session
                db_config.sessions.update_one(
                    {"session_id": session_data["session_id"]},
                    {"$set": {
                        "updated_at": session_data["updated_at"],
                        "total_messages": session_data["total_messages"]
                    }}
                )
                updated_count += 1
                print(f"🔄 Updated session: {session_data['title']} ({session_data['session_id']})")
        
        print("\n" + "="*50)
        if created_count > 0:
            print(f"🎉 Created {created_count} new sessions")
        if updated_count > 0:
            print(f"🔄 Updated {updated_count} existing sessions")
        if created_count == 0 and updated_count == 0:
            print("ℹ️  All demo sessions already exist")
        
        print("\n📋 Demo Sessions Created:")
        print("-" * 30)
        for session_data in demo_sessions:
            print(f"  {session_data['title']} - {session_data['user_id']}")
        
        print("\n🌐 You can now test sessions at:")
        print("  - React Frontend: http://localhost:3000")
        print("  - Login with admin/admin123 to see sessions")
        
    except Exception as e:
        print(f"❌ Error creating demo sessions: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("💬 Creating demo sessions for Multi-Agent System...")
    print("=" * 50)
    
    success = create_demo_sessions()
    
    if success:
        print("\n✅ Demo sessions setup completed successfully!")
    else:
        print("\n❌ Failed to setup demo sessions")
        sys.exit(1)
