#!/usr/bin/env python3
"""
Test direct database access to check chat_sessions.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_database():
    """Test direct database access."""
    print("🔍 Testing direct database access...")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()
        print(f"   ✅ Database connected")
        
        # Check collections
        collections = db_config.database.list_collection_names()
        print(f"   📚 Collections: {collections}")
        
        # Test chat_sessions collection
        if 'chat_sessions' in collections:
            print(f"\n   🔍 Testing chat_sessions collection...")
            
            # Count total sessions
            start_time = time.time()
            total_sessions = db_config.chat_sessions.count_documents({})
            count_time = (time.time() - start_time) * 1000
            print(f"     Total sessions: {total_sessions} (took {count_time:.2f}ms)")
            
            # Count sessions for admin user
            start_time = time.time()
            admin_sessions = db_config.chat_sessions.count_documents({"user_id": "admin"})
            admin_count_time = (time.time() - start_time) * 1000
            print(f"     Admin sessions: {admin_sessions} (took {admin_count_time:.2f}ms)")
            
            # Try to find one session for admin
            start_time = time.time()
            sample_session = db_config.chat_sessions.find_one({"user_id": "admin"})
            find_time = (time.time() - start_time) * 1000
            print(f"     Sample session query: (took {find_time:.2f}ms)")
            
            if sample_session:
                print(f"       Session ID: {sample_session.get('session_id', 'N/A')}")
                print(f"       Title: {sample_session.get('title', 'N/A')}")
                print(f"       Created: {sample_session.get('created_at', 'N/A')}")
            else:
                print(f"       No sessions found for admin")
            
            # Try the exact query from auth_server
            print(f"\n   🔍 Testing auth_server query...")
            start_time = time.time()
            
            sessions_cursor = db_config.chat_sessions.find({"user_id": "admin"}).sort("updated_at", -1)
            sessions = list(sessions_cursor)
            
            query_time = (time.time() - start_time) * 1000
            print(f"     Auth server query: {len(sessions)} sessions (took {query_time:.2f}ms)")
            
            if sessions:
                print(f"     First session:")
                session = sessions[0]
                print(f"       ID: {session.get('session_id', 'N/A')}")
                print(f"       Title: {session.get('title', 'N/A')}")
                print(f"       User: {session.get('user_id', 'N/A')}")
                print(f"       Created: {session.get('created_at', 'N/A')}")
                print(f"       Updated: {session.get('updated_at', 'N/A')}")
                print(f"       Active: {session.get('is_active', 'N/A')}")
                print(f"       Messages: {session.get('total_messages', 'N/A')}")
        
        # Check indexes
        print(f"\n   🔍 Checking indexes...")
        indexes = list(db_config.chat_sessions.list_indexes())
        print(f"     Chat sessions indexes:")
        for idx in indexes:
            print(f"       - {idx['name']}: {idx.get('key', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_create_indexes():
    """Create indexes for better performance."""
    print(f"\n🔍 Creating indexes...")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()
        
        # Create index on user_id
        try:
            result = db_config.chat_sessions.create_index("user_id")
            print(f"   ✅ Created chat_sessions.user_id index: {result}")
        except Exception as e:
            print(f"   ⚠️ Index may already exist: {e}")
        
        # Create compound index on user_id and updated_at
        try:
            result = db_config.chat_sessions.create_index([("user_id", 1), ("updated_at", -1)])
            print(f"   ✅ Created compound index: {result}")
        except Exception as e:
            print(f"   ⚠️ Compound index may already exist: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Index creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_simulation():
    """Simulate the API endpoint logic."""
    print(f"\n🔍 Simulating API endpoint logic...")
    
    try:
        from src.database.models import get_db_config
        from datetime import datetime
        
        db_config = get_db_config()
        user_id = "admin"
        
        start_time = datetime.utcnow()
        
        # Same logic as auth_server
        sessions_cursor = db_config.chat_sessions.find({"user_id": user_id}).sort("updated_at", -1)
        sessions = []
        
        for session_doc in sessions_cursor:
            session_data = {
                "session_id": session_doc["session_id"],
                "session_name": session_doc.get("title", f"Session {session_doc['session_id'][:8]}"),
                "user_id": session_doc["user_id"],
                "created_at": session_doc.get("created_at"),
                "updated_at": session_doc.get("updated_at"),
                "is_active": session_doc.get("is_active", True),
                "message_count": session_doc.get("total_messages", 0),
                "last_message_preview": ""
            }
            sessions.append(session_data)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        print(f"   ✅ API simulation completed")
        print(f"     Processing time: {processing_time:.2f}ms")
        print(f"     Sessions found: {len(sessions)}")
        print(f"     Response size: {len(str(sessions))} characters")
        
        if sessions:
            print(f"     Sample session:")
            sample = sessions[0]
            print(f"       ID: {sample['session_id']}")
            print(f"       Name: {sample['session_name']}")
            print(f"       Messages: {sample['message_count']}")
        
        return processing_time < 1000  # Should be under 1 second
        
    except Exception as e:
        print(f"❌ API simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 DIRECT DATABASE TEST")
    print("="*50)
    
    # Test 1: Direct database access
    db_success = test_direct_database()
    
    # Test 2: Create indexes
    index_success = test_create_indexes() if db_success else False
    
    # Test 3: API simulation
    api_sim_success = test_api_simulation() if db_success else False
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("="*30)
    print(f"Database Access: {'✅' if db_success else '❌'}")
    print(f"Index Creation: {'✅' if index_success else '❌'}")
    print(f"API Simulation: {'✅' if api_sim_success else '❌'}")
    
    if all([db_success, index_success, api_sim_success]):
        print(f"\n🎉 All tests passed! Database should be working properly.")
    else:
        print(f"\n⚠️ Some tests failed. There may be database issues.")

if __name__ == "__main__":
    main()
