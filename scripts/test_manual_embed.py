#!/usr/bin/env python3
"""
Test script for manual embedding functionality.
Tests the /api/s3/embed-existing endpoint.
"""

import sys
import os
import requests
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config


def test_manual_embed_api():
    """Test the manual embed API endpoint."""
    
    # Get some files from database
    db = get_db_config()
    active_files = list(db.file_metadata.find({"is_active": True}).limit(3))
    
    if not active_files:
        print("❌ No active files found to test")
        return False
    
    print("🧪 Testing Manual Embed API")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    for file_doc in active_files:
        user_id = file_doc['user_id']
        file_key = file_doc['file_key']
        file_name = file_doc['file_name']
        
        print(f"\n📄 Testing: {file_name} (user: {user_id})")
        
        try:
            # Test manual embed
            response = requests.post(
                f"{base_url}/api/s3/embed-existing",
                json={
                    "user_id": user_id,
                    "file_key": file_key
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"  ✅ Successfully embedded: {data.get('message', 'No message')}")
                    if data.get('embedding_id'):
                        print(f"  🔢 Embedding ID: {data['embedding_id']}")
                else:
                    print(f"  ❌ Embed failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Request error: {e}")
    
    return True


def check_embedding_status():
    """Check which files are embedded and which are missing."""
    
    print("\n🔍 Checking Embedding Status")
    print("=" * 40)
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        from src.database.model_qdrant import get_qdrant_config
        
        embedding_service = get_file_embedding_service()
        qdrant = get_qdrant_config()
        
        if not embedding_service.is_available():
            print("❌ Embedding service not available")
            return False
        
        # Get files from database
        db = get_db_config()
        active_files = list(db.file_metadata.find({"is_active": True}))
        
        print(f"📊 Found {len(active_files)} active files in MongoDB")
        
        embedded_count = 0
        missing_count = 0
        
        for file_doc in active_files:
            user_id = file_doc['user_id']
            file_name = file_doc['file_name']
            file_key = file_doc['file_key']
            
            # Check if embedded
            is_embedded = embedding_service.check_file_embedded(user_id, file_name, file_key)
            
            if is_embedded:
                embedded_count += 1
                print(f"  ✅ {file_name} (user: {user_id})")
            else:
                missing_count += 1
                print(f"  ❌ {file_name} (user: {user_id}) - Missing from Qdrant")
        
        print(f"\n📈 Summary:")
        print(f"  Embedded: {embedded_count}")
        print(f"  Missing: {missing_count}")
        print(f"  Total: {len(active_files)}")
        
        if missing_count > 0:
            print(f"\n💡 You can use the manual embed feature to embed the missing files")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking embedding status: {e}")
        return False


def test_search_functionality():
    """Test search functionality after embedding."""
    
    print("\n🔍 Testing Search Functionality")
    print("=" * 40)
    
    # Get a user with files
    db = get_db_config()
    user_files = list(db.file_metadata.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 0}}},
        {"$limit": 1}
    ]))
    
    if not user_files:
        print("❌ No users with files found")
        return False
    
    user_id = user_files[0]['_id']
    
    # Test search
    base_url = "http://localhost:8000"
    test_queries = [
        "document",
        "test",
        "file",
        "data"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        try:
            response = requests.post(
                f"{base_url}/api/s3/search",
                json={
                    "user_id": user_id,
                    "query": query,
                    "limit": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    results = data.get('results', [])
                    print(f"  ✅ Found {len(results)} results")
                    
                    for i, result in enumerate(results[:3], 1):
                        score = result.get('score', 0)
                        file_name = result.get('file_name', 'Unknown')
                        search_type = result.get('search_type', 'unknown')
                        print(f"    {i}. {file_name} (score: {score:.3f}, type: {search_type})")
                else:
                    print(f"  ❌ Search failed: {data.get('error', 'Unknown error')}")
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"  ❌ Search error: {e}")
    
    return True


def main():
    print("Manual Embedding Test Script")
    print("=" * 50)
    
    # Check current embedding status
    check_embedding_status()
    
    # Test manual embed API
    test_manual_embed_api()
    
    # Test search functionality
    test_search_functionality()
    
    print("\n✅ Manual embedding test completed!")
    print("\n💡 To use manual embedding in the UI:")
    print("   1. Go to Admin page")
    print("   2. Click on 'Sync' tab")
    print("   3. Look for files with missing Qdrant status (red icon)")
    print("   4. Click 'Embed' button for individual files")
    print("   5. Or click 'Embed All Missing' to embed all at once")


if __name__ == "__main__":
    main()
