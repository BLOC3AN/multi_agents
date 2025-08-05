#!/usr/bin/env python3
"""
Debug script to test the getUserSessions API performance.
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test database connection and basic operations."""
    print("🔍 Testing database connection...")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()
        print(f"   ✅ Database connected")

        # Test collections
        collections = db_config.database.list_collection_names()
        print(f"   📚 Available collections: {collections}")

        # Check sessions collection
        if 'sessions' in collections:
            total_sessions = db_config.sessions.count_documents({})
            print(f"   📊 Total sessions: {total_sessions}")

            # Check indexes
            indexes = list(db_config.sessions.list_indexes())
            print(f"   🔍 Sessions indexes: {[idx['name'] for idx in indexes]}")

            return True
        else:
            print(f"   ❌ Sessions collection not found")
            return False
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_sessions_query(user_id: str = "admin"):
    """Test the user sessions query performance."""
    print(f"\n🔍 Testing user sessions query for: {user_id}")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()
        
        # Time the query
        start_time = time.time()
        
        # Same query as in the API
        sessions_cursor = db_config.sessions.find({"user_id": user_id}).sort("updated_at", -1)
        sessions = list(sessions_cursor)
        
        query_time = (time.time() - start_time) * 1000
        
        print(f"   ⏱️ Query time: {query_time:.2f}ms")
        print(f"   📊 Sessions found: {len(sessions)}")
        
        if sessions:
            print(f"   📋 Sample session:")
            sample = sessions[0]
            print(f"     ID: {sample.get('session_id', 'N/A')}")
            print(f"     Title: {sample.get('title', 'N/A')}")
            print(f"     Created: {sample.get('created_at', 'N/A')}")
            print(f"     Messages: {sample.get('total_messages', 0)}")
        
        return query_time < 1000  # Should be under 1 second
        
    except Exception as e:
        print(f"❌ User sessions query failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoint_directly():
    """Test the API endpoint directly."""
    print(f"\n🔍 Testing API endpoint directly...")
    
    try:
        import requests
        import time
        
        # Test with different users
        test_users = ["admin", "hailt", "test_user"]
        
        for user_id in test_users:
            print(f"\n   Testing user: {user_id}")
            
            start_time = time.time()
            
            try:
                # Make request to the API
                response = requests.get(
                    f"http://localhost:8001/user/{user_id}/sessions",
                    timeout=15
                )
                
                request_time = (time.time() - start_time) * 1000
                
                print(f"     ⏱️ Request time: {request_time:.2f}ms")
                print(f"     📊 Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    sessions = data.get('sessions', [])
                    print(f"     📋 Sessions: {len(sessions)}")
                else:
                    print(f"     ❌ Error: {response.text}")
                
            except requests.exceptions.Timeout:
                request_time = (time.time() - start_time) * 1000
                print(f"     ⏱️ Request timeout after: {request_time:.2f}ms")
            except Exception as e:
                request_time = (time.time() - start_time) * 1000
                print(f"     ❌ Request failed after {request_time:.2f}ms: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_database_indexes():
    """Create database indexes to improve performance."""
    print(f"\n🔍 Creating database indexes...")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()

        # Create index on user_id for sessions
        try:
            result = db_config.sessions.create_index("user_id")
            print(f"   ✅ Created sessions.user_id index: {result}")
        except Exception as e:
            print(f"   ⚠️ Sessions.user_id index may already exist: {e}")

        # Create compound index on user_id and updated_at for better sorting
        try:
            result = db_config.sessions.create_index([("user_id", 1), ("updated_at", -1)])
            print(f"   ✅ Created sessions compound index: {result}")
        except Exception as e:
            print(f"   ⚠️ Sessions compound index may already exist: {e}")

        # Create index on session_id for messages
        try:
            result = db_config.messages.create_index("session_id")
            print(f"   ✅ Created messages.session_id index: {result}")
        except Exception as e:
            print(f"   ⚠️ Messages.session_id index may already exist: {e}")

        # List all indexes
        print(f"\n   📋 Current sessions indexes:")
        for idx in db_config.sessions.list_indexes():
            print(f"     - {idx['name']}: {idx.get('key', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Index creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_data_consistency():
    """Check data consistency and potential issues."""
    print(f"\n🔍 Checking data consistency...")
    
    try:
        from src.database.models import get_db_config
        
        db_config = get_db_config()

        # Check for sessions without user_id
        sessions_without_user = db_config.sessions.count_documents({"user_id": {"$exists": False}})
        print(f"   📊 Sessions without user_id: {sessions_without_user}")

        # Check for sessions with null user_id
        sessions_null_user = db_config.sessions.count_documents({"user_id": None})
        print(f"   📊 Sessions with null user_id: {sessions_null_user}")

        # Check for very old sessions
        from datetime import datetime, timedelta
        old_date = datetime.utcnow() - timedelta(days=30)
        old_sessions = db_config.sessions.count_documents({"updated_at": {"$lt": old_date}})
        print(f"   📊 Sessions older than 30 days: {old_sessions}")

        # Check for sessions with many messages
        pipeline = [
            {"$group": {"_id": "$session_id", "count": {"$sum": 1}}},
            {"$match": {"count": {"$gt": 100}}},
            {"$count": "sessions_with_many_messages"}
        ]

        result = list(db_config.messages.aggregate(pipeline))
        many_messages = result[0]["sessions_with_many_messages"] if result else 0
        print(f"   📊 Sessions with >100 messages: {many_messages}")

        # Get user distribution
        user_pipeline = [
            {"$group": {"_id": "$user_id", "session_count": {"$sum": 1}}},
            {"$sort": {"session_count": -1}},
            {"$limit": 5}
        ]

        top_users = list(db_config.sessions.aggregate(user_pipeline))
        print(f"   👥 Top users by session count:")
        for user in top_users:
            print(f"     - {user['_id']}: {user['session_count']} sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Data consistency check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("🐛 SESSIONS API DEBUG")
    print("="*50)
    
    # Test 1: Database connection
    db_success = test_database_connection()
    
    # Test 2: Create indexes
    index_success = create_database_indexes() if db_success else False
    
    # Test 3: User sessions query
    query_success = test_user_sessions_query() if db_success else False
    
    # Test 4: Data consistency
    consistency_success = check_data_consistency() if db_success else False
    
    # Test 5: API endpoint
    api_success = test_api_endpoint_directly()
    
    # Summary
    print(f"\n📊 DEBUG SUMMARY")
    print("="*30)
    print(f"Database Connection: {'✅' if db_success else '❌'}")
    print(f"Index Creation: {'✅' if index_success else '❌'}")
    print(f"Query Performance: {'✅' if query_success else '❌'}")
    print(f"Data Consistency: {'✅' if consistency_success else '❌'}")
    print(f"API Endpoint: {'✅' if api_success else '❌'}")
    
    if all([db_success, index_success, query_success, consistency_success, api_success]):
        print(f"\n🎉 All tests passed! Sessions API should be working properly.")
    else:
        print(f"\n⚠️ Some tests failed. Sessions API may have performance issues.")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if not index_success:
            print(f"  • Create database indexes for better performance")
        if not query_success:
            print(f"  • Optimize database queries or add pagination")
        if not consistency_success:
            print(f"  • Clean up inconsistent data")
        if not api_success:
            print(f"  • Check API server status and network connectivity")

if __name__ == "__main__":
    main()
