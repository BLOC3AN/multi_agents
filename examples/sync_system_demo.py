"""
Demo script for Data Synchronization System.
Shows complete sync workflow across MongoDB, S3, Qdrant, and UI.
"""
import sys
import os
import asyncio
import json
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.data_sync_service import get_data_sync_service
from src.services.realtime_sync_service import get_realtime_sync_service, setup_default_handlers
from src.services.file_manager import get_file_manager
from src.services.file_embedding_service import get_file_embedding_service


async def demo_sync_system():
    """Demo the complete sync system."""
    print("🔄 Data Synchronization System Demo")
    print("=" * 60)
    
    # Initialize services
    print("\n1️⃣ Initializing Services")
    sync_service = get_data_sync_service()
    realtime_sync = get_realtime_sync_service()
    file_manager = get_file_manager()
    embedding_service = get_file_embedding_service()
    
    # Setup event handlers
    setup_default_handlers()
    print("✅ Services initialized")
    
    # Test user
    user_id = "demo_sync_user"
    
    # Clean up any existing test data
    print("\n2️⃣ Cleaning up existing test data")
    try:
        # Delete any existing test files
        if embedding_service.is_available():
            embedding_service.delete_file_embedding(user_id, "sync_test_1.txt")
            embedding_service.delete_file_embedding(user_id, "sync_test_2.md")
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    # Create test files
    print("\n3️⃣ Creating Test Files")
    test_files = [
        {
            "filename": "sync_test_1.txt",
            "content": "This is a test file for sync system demonstration. It contains important data that should be synchronized across all storage systems.",
            "content_type": "text/plain"
        },
        {
            "filename": "sync_test_2.md",
            "content": "# Sync Test Document\n\nThis is a **markdown** document for testing the synchronization system.\n\n## Features\n- MongoDB storage\n- S3 file storage\n- Qdrant vector embedding\n- Real-time sync events",
            "content_type": "text/markdown"
        }
    ]
    
    uploaded_files = []
    
    for file_data in test_files:
        print(f"\n📄 Uploading: {file_data['filename']}")
        
        file_content = file_data["content"].encode('utf-8')
        
        # Upload through FileManager (simulates real upload)
        upload_result = file_manager.handle_file_upload(
            user_id=user_id,
            file_key=file_data["filename"],
            file_name=file_data["filename"],
            file_size=len(file_content),
            content_type=file_data["content_type"],
            file_content=file_content
        )
        
        if upload_result["success"]:
            print(f"✅ Uploaded: {file_data['filename']}")
            if upload_result.get("embedding_id"):
                print(f"✅ Embedded: {upload_result['embedding_id']}")
            uploaded_files.append(file_data["filename"])
            
            # Emit sync events
            await realtime_sync.handle_file_upload(
                user_id, upload_result["file_id"], 
                file_data["filename"], file_data["filename"],
                {"content_type": file_data["content_type"]}
            )
        else:
            print(f"❌ Failed to upload: {upload_result.get('error')}")
    
    # Wait a moment for async operations
    await asyncio.sleep(2)
    
    # Analyze sync status
    print("\n4️⃣ Analyzing Sync Status")
    
    # Get sync report
    report = sync_service.get_sync_report(user_id)
    
    print(f"📊 Sync Report for user {user_id}:")
    print(f"   Total files: {report['summary']['total_files']}")
    print(f"   Synced: {report['summary']['synced']}")
    print(f"   Out of sync: {report['summary']['out_of_sync']}")
    print(f"   Missing: {report['summary']['missing']}")
    print(f"   Errors: {report['summary']['errors']}")
    
    print(f"\n📍 Storage Distribution:")
    print(f"   MongoDB: {report['storage_counts']['mongodb']}")
    print(f"   S3: {report['storage_counts']['s3']}")
    print(f"   Qdrant: {report['storage_counts']['qdrant']}")
    
    if report['issues']:
        print(f"\n⚠️ Issues Found ({len(report['issues'])}):")
        for issue in report['issues']:
            print(f"   - {issue['file_name']}: {', '.join(issue['issues'])}")
    else:
        print("\n✅ No sync issues found!")
    
    # Test real-time sync status
    print("\n5️⃣ Real-time Sync Status")
    
    summary = realtime_sync.get_sync_status_summary(user_id)
    print(f"📈 Real-time Summary:")
    print(f"   Total files: {summary['total_files']}")
    print(f"   Synced files: {summary['synced_files']}")
    print(f"   Files with issues: {summary['files_with_issues']}")
    
    print(f"\n🗄️ Storage Distribution:")
    dist = summary['storage_distribution']
    print(f"   MongoDB only: {dist['mongodb_only']}")
    print(f"   S3 only: {dist['s3_only']}")
    print(f"   Qdrant only: {dist['qdrant_only']}")
    print(f"   All three systems: {dist['all_three']}")
    
    # Test search functionality
    print("\n6️⃣ Testing Search Functionality")
    
    if embedding_service.is_available():
        query = "sync system demonstration"
        print(f"🔍 Searching for: '{query}'")
        
        query_embedding = embedding_service.embedding_provider.encode(query)
        qdrant = embedding_service.qdrant
        
        search_results = qdrant.search_similar(
            query_vector=query_embedding,
            limit=5,
            score_threshold=0.3,
            filter_conditions={
                "must": [
                    {
                        "key": "user_id",
                        "match": {"value": user_id}
                    }
                ]
            }
        )
        
        if search_results:
            print(f"✅ Found {len(search_results)} results:")
            for i, result in enumerate(search_results, 1):
                doc = result['document']
                score = result['score']
                print(f"   {i}. {doc.title} (score: {score:.3f})")
        else:
            print("❌ No search results found")
    else:
        print("⚠️ Search functionality not available (Qdrant not connected)")
    
    # Simulate file deletion and sync
    print("\n7️⃣ Testing File Deletion Sync")
    
    if uploaded_files:
        test_file = uploaded_files[0]
        print(f"🗑️ Deleting file: {test_file}")
        
        # Delete through FileManager
        success = file_manager.delete_file(test_file, user_id)
        
        if success:
            print(f"✅ File deleted: {test_file}")
            
            # Emit deletion event
            await realtime_sync.handle_file_deletion(user_id, test_file, test_file)
            
            # Wait for async operations
            await asyncio.sleep(1)
            
            # Check sync status after deletion
            post_delete_report = sync_service.get_sync_report(user_id)
            print(f"📊 Post-deletion sync status:")
            print(f"   Total files: {post_delete_report['summary']['total_files']}")
            print(f"   Issues: {len(post_delete_report['issues'])}")
        else:
            print(f"❌ Failed to delete file: {test_file}")
    
    # Test sync repair (dry run)
    print("\n8️⃣ Testing Sync Repair (Dry Run)")
    
    repair_results = sync_service.fix_sync_issues(user_id, dry_run=True)
    
    print(f"🔧 Sync Repair Results (Dry Run):")
    print(f"   Total files: {repair_results['total_files']}")
    print(f"   Synced files: {repair_results['synced_files']}")
    print(f"   Would fix: {repair_results['fixed_files']}")
    print(f"   Would fail: {repair_results['failed_fixes']}")
    
    if repair_results['actions_taken']:
        print(f"   Actions that would be taken:")
        for action in repair_results['actions_taken']:
            print(f"     - {action}")
    
    # Final cleanup
    print("\n9️⃣ Final Cleanup")
    
    for filename in uploaded_files[1:]:  # Skip the already deleted file
        try:
            file_manager.delete_file(filename, user_id)
            if embedding_service.is_available():
                embedding_service.delete_file_embedding(user_id, filename)
            print(f"✅ Cleaned up: {filename}")
        except Exception as e:
            print(f"⚠️ Cleanup warning for {filename}: {e}")
    
    print("\n🎉 Sync System Demo Completed!")
    print("=" * 60)
    
    # Final summary
    final_report = sync_service.get_sync_report(user_id)
    print(f"\n📋 Final Summary:")
    print(f"   Files remaining: {final_report['summary']['total_files']}")
    print(f"   Sync issues: {len(final_report['issues'])}")
    print(f"   Demo timestamp: {datetime.utcnow().isoformat()}")


async def demo_api_endpoints():
    """Demo API endpoints for sync functionality."""
    print("\n🌐 Testing Sync API Endpoints")
    print("=" * 40)
    
    import requests
    
    base_url = "http://localhost:8000"
    user_id = "demo_sync_user"
    
    try:
        # Test sync status endpoint
        print("1️⃣ Testing sync status endpoint")
        response = requests.get(f"{base_url}/api/sync/status/{user_id}")
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                status = data["sync_status"]
                print(f"✅ Sync status: {status['total_files']} files, {status['issues']} issues")
            else:
                print(f"❌ API error: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
        
        # Test sync analysis endpoint
        print("\n2️⃣ Testing sync analysis endpoint")
        response = requests.post(f"{base_url}/api/sync/analyze", 
                               json={"user_id": user_id})
        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                report = data["report"]
                print(f"✅ Analysis complete: {report['summary']['total_files']} files analyzed")
            else:
                print(f"❌ API error: {data.get('error')}")
        else:
            print(f"❌ HTTP error: {response.status_code}")
        
        print("✅ API endpoints test completed")
        
    except Exception as e:
        print(f"⚠️ API test skipped: {e}")
        print("💡 Make sure the server is running: python auth_server.py")


if __name__ == "__main__":
    # Run the complete sync system demo
    asyncio.run(demo_sync_system())
    
    # Test API endpoints (optional)
    asyncio.run(demo_api_endpoints())
