#!/usr/bin/env python3
"""
Cleanup script for orphaned files in S3 that don't have corresponding database entries.
"""

from src.database.models import get_db_config
from src.database.model_s3 import get_s3_manager

def cleanup_orphaned_files():
    """Find and optionally remove files that exist in S3 but not in database."""
    
    print("🔍 Starting orphaned files cleanup...")
    
    # Get services
    db_config = get_db_config()
    s3_manager = get_s3_manager()
    
    if not db_config or not s3_manager:
        print("❌ Failed to initialize services")
        return
    
    # Get all files from S3
    print("📥 Getting all files from S3...")
    s3_files = s3_manager.list_files()
    if not s3_files.get("success"):
        print(f"❌ Failed to list S3 files: {s3_files.get('error')}")
        return
    
    s3_file_keys = [f["key"] for f in s3_files.get("files", [])]
    print(f"📊 Found {len(s3_file_keys)} files in S3")
    
    # Get all files from database
    print("📥 Getting all files from database...")
    db_files = list(db_config.file_metadata.find({"is_active": True}))
    db_file_keys = [f["file_key"] for f in db_files]
    print(f"📊 Found {len(db_file_keys)} files in database")
    
    # Find orphaned files (in S3 but not in database)
    orphaned_files = []
    for s3_key in s3_file_keys:
        if s3_key not in db_file_keys:
            orphaned_files.append(s3_key)
    
    print(f"\n🔍 Analysis Results:")
    print(f"  S3 files: {len(s3_file_keys)}")
    print(f"  Database files: {len(db_file_keys)}")
    print(f"  Orphaned files: {len(orphaned_files)}")
    
    if orphaned_files:
        print(f"\n📋 Orphaned files found:")
        for i, file_key in enumerate(orphaned_files, 1):
            print(f"  {i}. {file_key}")
        
        # Ask for confirmation
        response = input(f"\n❓ Do you want to delete these {len(orphaned_files)} orphaned files from S3? (y/N): ")
        
        if response.lower() == 'y':
            print("\n🗑️ Deleting orphaned files...")
            deleted_count = 0
            failed_count = 0
            
            for file_key in orphaned_files:
                try:
                    result = s3_manager.delete_file(file_key)
                    if result.get("success"):
                        print(f"  ✅ Deleted: {file_key}")
                        deleted_count += 1
                    else:
                        print(f"  ❌ Failed to delete: {file_key} - {result.get('error')}")
                        failed_count += 1
                except Exception as e:
                    print(f"  ❌ Error deleting {file_key}: {e}")
                    failed_count += 1
            
            print(f"\n📊 Cleanup Summary:")
            print(f"  ✅ Successfully deleted: {deleted_count}")
            print(f"  ❌ Failed to delete: {failed_count}")
            print(f"  📊 Total processed: {len(orphaned_files)}")
        else:
            print("❌ Cleanup cancelled by user")
    else:
        print("\n✅ No orphaned files found. All S3 files have corresponding database entries.")

if __name__ == "__main__":
    cleanup_orphaned_files()
