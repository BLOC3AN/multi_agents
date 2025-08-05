#!/usr/bin/env python3
"""
Script to check actual data in MongoDB, S3, and Qdrant.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.models import get_db_config
from src.database.model_s3 import get_s3_manager
from src.services.file_embedding_service import get_file_embedding_service


def check_mongodb_data():
    """Check what's actually in MongoDB."""
    print("🔍 Checking MongoDB data...")
    
    try:
        db_config = get_db_config()
        
        # Check all collections
        collections = db_config.db.list_collection_names()
        print(f"📚 Available collections: {collections}")
        
        # Check file_metadata collection
        if 'file_metadata' in collections:
            total_files = db_config.file_metadata.count_documents({})
            active_files = db_config.file_metadata.count_documents({"is_active": True})
            inactive_files = db_config.file_metadata.count_documents({"is_active": False})
            
            print(f"📁 file_metadata collection:")
            print(f"   Total files: {total_files}")
            print(f"   Active files: {active_files}")
            print(f"   Inactive files: {inactive_files}")
            
            # Show some sample files
            if total_files > 0:
                print(f"\n📋 Sample files:")
                sample_files = list(db_config.file_metadata.find({}).limit(5))
                for i, file in enumerate(sample_files, 1):
                    print(f"   {i}. {file.get('file_name', 'Unknown')} (User: {file.get('user_id', 'Unknown')}, Active: {file.get('is_active', 'Unknown')})")
            
            # Check users
            users = db_config.file_metadata.distinct("user_id")
            print(f"\n👥 Users with files: {users}")
        
        # Check other relevant collections
        for collection_name in ['users', 'agents', 'conversations']:
            if collection_name in collections:
                count = db_config.db[collection_name].count_documents({})
                print(f"📊 {collection_name}: {count} documents")
        
    except Exception as e:
        print(f"❌ Error checking MongoDB: {e}")


def check_s3_data():
    """Check what's actually in S3."""
    print("\n🔍 Checking S3 data...")
    
    try:
        s3_manager = get_s3_manager()
        
        # List all files
        result = s3_manager.list_files()
        if result.get("success"):
            files = result.get("files", [])
            print(f"📁 S3 files found: {len(files)}")
            
            if files:
                print(f"\n📋 S3 files:")
                for i, file in enumerate(files[:10], 1):  # Show first 10
                    print(f"   {i}. {file.get('key', 'Unknown')} ({file.get('size', 0)} bytes, {file.get('last_modified', 'Unknown date')})")
                
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more files")
        else:
            print(f"❌ Failed to list S3 files: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ Error checking S3: {e}")


def check_qdrant_data():
    """Check what's actually in Qdrant."""
    print("\n🔍 Checking Qdrant data...")
    
    try:
        embedding_service = get_file_embedding_service()
        if not embedding_service or not embedding_service.is_available():
            print("❌ Qdrant service not available")
            return
        
        qdrant = embedding_service.qdrant
        
        # Get collection info
        collection_info = qdrant.client.get_collection(qdrant.collection_name)
        print(f"📊 Collection '{qdrant.collection_name}' info:")
        print(f"   Points count: {collection_info.points_count}")
        print(f"   Vectors count: {collection_info.vectors_count}")
        
        if collection_info.points_count > 0:
            # Get some sample points
            results, _ = qdrant.client.scroll(
                collection_name=qdrant.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False
            )
            
            print(f"\n📋 Sample Qdrant documents:")
            for i, point in enumerate(results, 1):
                payload = point.payload
                print(f"   {i}. ID: {point.id}")
                print(f"      Title: {payload.get('title', 'Unknown')}")
                print(f"      User: {payload.get('user_id', 'Unknown')}")
                print(f"      Source: {payload.get('source', 'Unknown')}")
                print(f"      File name: {payload.get('file_name', 'Unknown')}")
        
        # Check users in Qdrant
        try:
            # Get all unique user_ids
            results, _ = qdrant.client.scroll(
                collection_name=qdrant.collection_name,
                limit=1000,  # Adjust based on your data size
                with_payload=True,
                with_vectors=False
            )
            
            users = set()
            for point in results:
                user_id = point.payload.get('user_id')
                if user_id:
                    users.add(user_id)
            
            print(f"\n👥 Users in Qdrant: {list(users)}")
            
        except Exception as e:
            print(f"⚠️ Could not get user list from Qdrant: {e}")
    
    except Exception as e:
        print(f"❌ Error checking Qdrant: {e}")


def check_specific_user(user_id: str):
    """Check data for a specific user."""
    print(f"\n🔍 Checking data for user: {user_id}")
    
    try:
        # MongoDB
        db_config = get_db_config()
        mongo_files = list(db_config.file_metadata.find({"user_id": user_id}))
        print(f"📁 MongoDB files for {user_id}: {len(mongo_files)}")
        
        # S3 (need to match with MongoDB to filter by user)
        s3_manager = get_s3_manager()
        result = s3_manager.list_files()
        if result.get("success"):
            all_s3_files = result.get("files", [])
            # Filter S3 files that match this user's MongoDB records
            user_s3_files = []
            for s3_file in all_s3_files:
                # Check if this S3 file has a corresponding MongoDB record for this user
                mongo_match = db_config.file_metadata.find_one({
                    "file_key": s3_file.get("key"),
                    "user_id": user_id
                })
                if mongo_match:
                    user_s3_files.append(s3_file)
            
            print(f"📁 S3 files for {user_id}: {len(user_s3_files)}")
        
        # Qdrant
        embedding_service = get_file_embedding_service()
        if embedding_service and embedding_service.is_available():
            qdrant = embedding_service.qdrant
            user_files = qdrant.get_user_files(user_id)
            print(f"📁 Qdrant files for {user_id}: {len(user_files)}")
        
    except Exception as e:
        print(f"❌ Error checking user {user_id}: {e}")


def main():
    """Main function."""
    print("🔍 COMPREHENSIVE DATA CHECK")
    print("="*50)
    
    # Check all systems
    check_mongodb_data()
    check_s3_data()
    check_qdrant_data()
    
    # If there are users, check specific user data
    try:
        db_config = get_db_config()
        users = db_config.file_metadata.distinct("user_id")
        if users:
            print(f"\n🔍 CHECKING SPECIFIC USERS")
            print("="*30)
            for user in users[:3]:  # Check first 3 users
                check_specific_user(user)
    except Exception as e:
        print(f"⚠️ Could not check specific users: {e}")


if __name__ == "__main__":
    main()
