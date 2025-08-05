#!/usr/bin/env python3
"""
Debug script for sync status issues.
Helps identify why UI shows incorrect sync status.
"""

import sys
import os
import requests
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config
from src.services.file_embedding_service import get_file_embedding_service
from src.services.data_sync_service import get_data_sync_service


def debug_embedding_service():
    """Debug embedding service directly."""
    print("🔍 Debugging Embedding Service")
    print("=" * 40)
    
    try:
        embedding_service = get_file_embedding_service()
        print(f"✅ Embedding service available: {embedding_service.is_available()}")
        
        # Get files from database
        db = get_db_config()
        active_files = list(db.file_metadata.find({"is_active": True}))
        
        print(f"\n📊 Checking {len(active_files)} active files:")
        
        for file_doc in active_files:
            user_id = file_doc['user_id']
            file_name = file_doc['file_name']
            file_key = file_doc['file_key']
            
            print(f"\n📄 {file_name} (user: {user_id})")
            print(f"   File key: {file_key}")
            
            # Check embedding status
            is_embedded = embedding_service.check_file_embedded(user_id, file_name, file_key)
            print(f"   Embedded: {is_embedded}")
            
            # Check Qdrant directly
            try:
                qdrant = embedding_service.qdrant
                existing_doc = qdrant.check_file_exists(user_id, file_name, file_key)
                print(f"   Qdrant check: {existing_doc is not None}")
                
                if existing_doc:
                    print(f"   Document ID: {existing_doc.id}")
                    print(f"   Metadata: {existing_doc.payload}")
                
            except Exception as e:
                print(f"   Qdrant error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error debugging embedding service: {e}")
        return False


def debug_sync_service():
    """Debug sync service directly."""
    print("\n🔄 Debugging Sync Service")
    print("=" * 40)
    
    try:
        sync_service = get_data_sync_service()
        
        # Get users with files
        db = get_db_config()
        users = db.file_metadata.distinct("user_id", {"is_active": True})
        
        for user_id in users:
            print(f"\n👤 User: {user_id}")
            
            # Get sync report
            report = sync_service.get_sync_report(user_id)
            
            print(f"   Total files: {report['summary']['total_files']}")
            print(f"   Synced: {report['summary']['synced_files']}")
            print(f"   Issues: {len(report['issues'])}")
            
            # Check individual files
            file_records = sync_service.get_user_file_records(user_id)
            
            for record in file_records:
                print(f"\n   📄 {record.file_name}")
                print(f"      MongoDB: {record.in_mongodb}")
                print(f"      S3: {record.in_s3}")
                print(f"      Qdrant: {record.in_qdrant}")
                print(f"      Sync status: {record.sync_status.value}")
                if record.sync_issues:
                    print(f"      Issues: {record.sync_issues}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error debugging sync service: {e}")
        return False


def debug_api_endpoints():
    """Debug API endpoints."""
    print("\n🌐 Debugging API Endpoints")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Get users
    db = get_db_config()
    users = db.file_metadata.distinct("user_id", {"is_active": True})
    
    for user_id in users:
        print(f"\n👤 Testing API for user: {user_id}")
        
        try:
            # Test sync status API
            response = requests.get(f"{base_url}/api/sync/status/{user_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    sync_status = data['sync_status']
                    print(f"   ✅ API Response:")
                    print(f"      Total files: {sync_status['total_files']}")
                    print(f"      Synced: {sync_status['synced']}")
                    print(f"      Issues: {sync_status['issues']}")
                    
                    # Check individual files
                    for file_info in sync_status['files']:
                        print(f"\n      📄 {file_info['file_name']}")
                        print(f"         Sync status: {file_info['sync_status']}")
                        print(f"         MongoDB: {file_info['locations']['mongodb']}")
                        print(f"         S3: {file_info['locations']['s3']}")
                        print(f"         Qdrant: {file_info['locations']['qdrant']}")
                        if file_info['issues']:
                            print(f"         Issues: {file_info['issues']}")
                else:
                    print(f"   ❌ API Error: {data.get('error', 'Unknown')}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request Error: {e}")


def compare_results():
    """Compare results between different methods."""
    print("\n🔍 Comparing Results")
    print("=" * 40)
    
    try:
        # Get embedding service
        embedding_service = get_file_embedding_service()
        
        # Get files from database
        db = get_db_config()
        active_files = list(db.file_metadata.find({"is_active": True}))
        
        print("File | Embedding Service | API Response | Match")
        print("-" * 60)
        
        for file_doc in active_files:
            user_id = file_doc['user_id']
            file_name = file_doc['file_name']
            file_key = file_doc['file_key']
            
            # Check embedding service
            is_embedded = embedding_service.check_file_embedded(user_id, file_name, file_key)
            
            # Check API
            try:
                response = requests.get(f"http://localhost:8000/api/sync/status/{user_id}")
                api_qdrant = False
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        for file_info in data['sync_status']['files']:
                            if file_info['file_name'] == file_name:
                                api_qdrant = file_info['locations']['qdrant']
                                break
                
                match = "✅" if is_embedded == api_qdrant else "❌"
                print(f"{file_name[:20]:20} | {str(is_embedded):17} | {str(api_qdrant):12} | {match}")
                
            except Exception as e:
                print(f"{file_name[:20]:20} | {str(is_embedded):17} | ERROR        | ❌")
        
    except Exception as e:
        print(f"❌ Error comparing results: {e}")


def main():
    print("Sync Status Debug Script")
    print("=" * 50)
    
    # Debug embedding service
    debug_embedding_service()
    
    # Debug sync service
    debug_sync_service()
    
    # Debug API endpoints
    debug_api_endpoints()
    
    # Compare results
    compare_results()
    
    print("\n💡 Troubleshooting Tips:")
    print("1. If embedding service shows True but API shows False:")
    print("   - Check sync service logic")
    print("   - Verify Qdrant connection in sync service")
    print("2. If API is correct but UI shows wrong:")
    print("   - Clear browser cache")
    print("   - Use Force Refresh button")
    print("   - Check browser console for errors")
    print("3. If all show False but you see data in Qdrant:")
    print("   - Check file matching logic (user_id, file_name, file_key)")
    print("   - Verify Qdrant payload structure")


if __name__ == "__main__":
    main()
