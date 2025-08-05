#!/usr/bin/env python3
"""
Database-S3 Sync Script for Multi-Agent System.
Ensures MongoDB and S3 are properly synchronized.
Only files that exist in S3 should be marked as active in MongoDB.
"""

import sys
import os
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config


def get_s3_files():
    """Get list of files actually in S3."""
    try:
        from src.database.model_s3 import get_s3_manager
        s3_manager = get_s3_manager()
        
        # Get files from S3
        result = s3_manager.list_files(limit=1000)
        
        if result.get('success', False):
            s3_files = result.get('files', [])
            # Extract just the keys/names
            s3_file_keys = set()
            for file_info in s3_files:
                # Handle both 'key' and 'Key' fields
                key = file_info.get('key') or file_info.get('Key') or file_info.get('name', '')
                if key:
                    s3_file_keys.add(key)
            
            print(f"✅ Found {len(s3_file_keys)} files in S3")
            return s3_file_keys
        else:
            print(f"❌ Failed to list S3 files: {result.get('error', 'Unknown error')}")
            return set()
            
    except Exception as e:
        print(f"❌ S3 connection error: {e}")
        return set()


def sync_database_with_s3(dry_run=True):
    """
    Sync MongoDB with S3 - mark files as inactive if they don't exist in S3.
    
    Args:
        dry_run (bool): If True, only show what would be changed without making changes
    """
    try:
        # Get S3 files
        s3_file_keys = get_s3_files()
        
        # Get MongoDB files
        db = get_db_config()
        all_files = list(db.file_metadata.find({}))
        active_files = [f for f in all_files if f.get('is_active', False)]
        
        print(f"\n📊 Current State:")
        print(f"  Total files in MongoDB: {len(all_files)}")
        print(f"  Active files in MongoDB: {len(active_files)}")
        print(f"  Files in S3: {len(s3_file_keys)}")
        
        # Check sync status
        db_file_keys = {f['file_key'] for f in active_files}
        
        # Files in DB but missing in S3 (should be deactivated)
        missing_in_s3 = db_file_keys - s3_file_keys
        
        # Files in S3 but missing in DB (informational)
        missing_in_db = s3_file_keys - db_file_keys
        
        print(f"\n🔍 Sync Analysis:")
        print(f"  Files in DB but missing in S3: {len(missing_in_s3)}")
        print(f"  Files in S3 but missing in DB: {len(missing_in_db)}")
        
        if missing_in_s3:
            print(f"\n⚠️  Files to deactivate (missing in S3):")
            for i, file_key in enumerate(sorted(missing_in_s3), 1):
                # Get file info
                file_doc = next((f for f in active_files if f['file_key'] == file_key), None)
                if file_doc:
                    user_id = file_doc.get('user_id', 'unknown')
                    upload_date = file_doc.get('upload_date', 'unknown')
                    print(f"  {i:2d}. {file_key} (user: {user_id}, uploaded: {upload_date})")
        
        if missing_in_db:
            print(f"\n📁 Files in S3 but not in DB (orphaned):")
            for i, file_key in enumerate(sorted(missing_in_db), 1):
                print(f"  {i:2d}. {file_key}")
        
        if not missing_in_s3 and not missing_in_db:
            print(f"\n✅ MongoDB and S3 are perfectly synchronized!")
            return True
        
        if dry_run:
            print(f"\n🔍 DRY RUN MODE - No changes made.")
            print(f"Run with --apply to actually sync the databases.")
            return True
        
        # Apply changes - deactivate files missing in S3
        if missing_in_s3:
            print(f"\n🔄 Deactivating files missing in S3...")
            deactivated_count = 0
            
            for file_key in missing_in_s3:
                result = db.file_metadata.update_one(
                    {"file_key": file_key, "is_active": True},
                    {
                        "$set": {
                            "is_active": False,
                            "deleted_at": datetime.utcnow().isoformat(),
                            "sync_reason": "missing_in_s3"
                        }
                    }
                )
                
                if result.modified_count > 0:
                    deactivated_count += 1
                    print(f"  ✅ Deactivated: {file_key}")
                else:
                    print(f"  ❌ Failed to deactivate: {file_key}")
            
            print(f"\n📊 Sync Results:")
            print(f"  Deactivated {deactivated_count} out of {len(missing_in_s3)} files")
        
        return True
        
    except Exception as e:
        print(f"❌ Sync error: {e}")
        return False


def check_user_files(user_id):
    """Check files for a specific user."""
    try:
        db = get_db_config()
        s3_file_keys = get_s3_files()
        
        # Get user files from DB
        user_files = list(db.file_metadata.find({
            "user_id": user_id,
            "is_active": True
        }))
        
        print(f"\n👤 User: {user_id}")
        print(f"  Active files in DB: {len(user_files)}")
        
        if not user_files:
            print(f"  No active files found for user")
            return
        
        # Check which files exist in S3
        existing_in_s3 = []
        missing_in_s3 = []
        
        for file_doc in user_files:
            file_key = file_doc['file_key']
            if file_key in s3_file_keys:
                existing_in_s3.append(file_doc)
            else:
                missing_in_s3.append(file_doc)
        
        print(f"  Files existing in S3: {len(existing_in_s3)}")
        print(f"  Files missing in S3: {len(missing_in_s3)}")
        
        if existing_in_s3:
            print(f"  ✅ Valid files:")
            for file_doc in existing_in_s3:
                print(f"    - {file_doc['file_name']} ({file_doc['file_size']} bytes)")
        
        if missing_in_s3:
            print(f"  ❌ Invalid files (should be deactivated):")
            for file_doc in missing_in_s3:
                print(f"    - {file_doc['file_name']} ({file_doc['file_size']} bytes)")
        
    except Exception as e:
        print(f"❌ Error checking user files: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync MongoDB with S3")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default: dry run)")
    parser.add_argument("--user", type=str, help="Check files for specific user")
    
    args = parser.parse_args()
    
    print("Database-S3 Sync Script")
    print("=" * 50)
    
    if args.user:
        check_user_files(args.user)
    else:
        success = sync_database_with_s3(dry_run=not args.apply)
        
        if not success:
            print("\n❌ Sync failed.")
            sys.exit(1)
        else:
            print("\n✅ Sync completed successfully.")


if __name__ == "__main__":
    main()
