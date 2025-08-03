#!/usr/bin/env python3
"""
Migration script for existing files to file_metadata collection.
This script will scan S3 bucket and create metadata entries for existing files.
"""
import sys
from pathlib import Path
import uuid
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.database.models import get_db_config, FileMetadata
from src.services.file_manager import get_file_manager


def migrate_existing_files(default_user_id: str = "system_migration"):
    """
    Migrate existing files in S3 to file_metadata collection.
    
    Args:
        default_user_id: Default user_id for files without owner information
    """
    print("🔄 Starting file migration...")
    
    try:
        # Get services
        db_config = get_db_config()
        file_manager = get_file_manager()
        
        # Check if S3 manager is available
        if not file_manager.s3_manager:
            print("⚠️ S3 manager not available. Migration will be skipped.")
            return
        
        # Get existing files from S3
        print("📁 Scanning S3 bucket for existing files...")
        s3_result = file_manager.s3_manager.list_files()
        
        if not s3_result.get('success', False):
            print(f"❌ Failed to list S3 files: {s3_result.get('error', 'Unknown error')}")
            return
        
        s3_files = s3_result.get('files', [])
        print(f"📊 Found {len(s3_files)} files in S3 bucket")
        
        if not s3_files:
            print("ℹ️ No files found in S3 bucket. Migration complete.")
            return
        
        # Check existing metadata entries
        existing_metadata = list(db_config.file_metadata.find({}))
        existing_keys = {meta['file_key'] for meta in existing_metadata}
        print(f"📋 Found {len(existing_metadata)} existing metadata entries")
        
        # Migrate files that don't have metadata
        migrated_count = 0
        skipped_count = 0
        
        for s3_file in s3_files:
            file_key = s3_file.get('key', s3_file.get('name', ''))
            
            if file_key in existing_keys:
                print(f"⏭️ Skipping {file_key} (metadata already exists)")
                skipped_count += 1
                continue
            
            try:
                # Create metadata for the file
                file_metadata = FileMetadata(
                    file_id=str(uuid.uuid4()),
                    user_id=default_user_id,
                    file_key=file_key,
                    file_name=s3_file.get('name', file_key.split('/')[-1]),
                    file_size=s3_file.get('size', 0),
                    content_type=s3_file.get('content_type', 'application/octet-stream'),
                    upload_date=datetime.fromisoformat(s3_file.get('last_modified', datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                    s3_bucket=getattr(file_manager.s3_manager, 'bucket_name', None),
                    is_active=True,
                    metadata={
                        'migrated': True,
                        'migration_date': datetime.utcnow().isoformat(),
                        'original_s3_data': s3_file
                    }
                )
                
                # Insert metadata
                db_config.file_metadata.insert_one(file_metadata.to_dict())
                print(f"✅ Migrated: {file_key}")
                migrated_count += 1
                
            except Exception as e:
                print(f"❌ Failed to migrate {file_key}: {e}")
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Migrated: {migrated_count} files")
        print(f"   ⏭️ Skipped: {skipped_count} files")
        print(f"   📁 Total processed: {len(s3_files)} files")
        
        if migrated_count > 0:
            print(f"\n⚠️ Note: All migrated files are assigned to user '{default_user_id}'")
            print("   You may need to reassign ownership manually if needed.")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")


def cleanup_orphaned_metadata():
    """
    Clean up metadata entries for files that no longer exist in S3.
    """
    print("\n🧹 Checking for orphaned metadata entries...")
    
    try:
        db_config = get_db_config()
        file_manager = get_file_manager()
        
        if not file_manager.s3_manager:
            print("⚠️ S3 manager not available. Cleanup skipped.")
            return
        
        # Get S3 files
        s3_result = file_manager.s3_manager.list_files()
        if not s3_result.get('success', False):
            print(f"❌ Failed to list S3 files: {s3_result.get('error', 'Unknown error')}")
            return
        
        s3_keys = {f.get('key', f.get('name', '')) for f in s3_result.get('files', [])}
        
        # Get metadata entries
        metadata_entries = list(db_config.file_metadata.find({'is_active': True}))
        
        orphaned_count = 0
        for metadata in metadata_entries:
            file_key = metadata['file_key']
            
            if file_key not in s3_keys:
                # Mark as inactive
                db_config.file_metadata.update_one(
                    {'file_id': metadata['file_id']},
                    {
                        '$set': {
                            'is_active': False,
                            'deleted_at': datetime.utcnow().isoformat(),
                            'deletion_reason': 'orphaned_cleanup'
                        }
                    }
                )
                print(f"🗑️ Marked orphaned metadata as inactive: {file_key}")
                orphaned_count += 1
        
        print(f"📊 Cleanup Summary: {orphaned_count} orphaned entries cleaned up")
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")


def show_migration_stats():
    """Show current migration statistics."""
    print("\n📊 Current File Management Statistics:")
    
    try:
        db_config = get_db_config()
        
        # Total metadata entries
        total_metadata = db_config.file_metadata.count_documents({})
        active_metadata = db_config.file_metadata.count_documents({'is_active': True})
        migrated_files = db_config.file_metadata.count_documents({'metadata.migrated': True})
        
        print(f"   📁 Total metadata entries: {total_metadata}")
        print(f"   ✅ Active files: {active_metadata}")
        print(f"   🔄 Migrated files: {migrated_files}")
        
        # User statistics
        user_stats = list(db_config.file_metadata.aggregate([
            {'$match': {'is_active': True}},
            {'$group': {'_id': '$user_id', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]))
        
        print(f"\n👥 Files per user:")
        for stat in user_stats:
            print(f"   {stat['_id']}: {stat['count']} files")
        
    except Exception as e:
        print(f"❌ Failed to get statistics: {e}")


def main():
    """Main migration function."""
    print("🚀 File Migration Tool")
    print("=" * 50)
    
    # Show current stats
    show_migration_stats()
    
    # Ask for confirmation
    print("\n" + "=" * 50)
    response = input("Do you want to proceed with migration? (y/N): ").strip().lower()
    
    if response != 'y':
        print("❌ Migration cancelled.")
        return
    
    # Get default user ID
    default_user = input("Enter default user_id for migrated files (default: 'system_migration'): ").strip()
    if not default_user:
        default_user = "system_migration"
    
    # Run migration
    migrate_existing_files(default_user)
    
    # Run cleanup
    cleanup_response = input("\nDo you want to clean up orphaned metadata? (y/N): ").strip().lower()
    if cleanup_response == 'y':
        cleanup_orphaned_metadata()
    
    # Show final stats
    show_migration_stats()
    
    print("\n✅ Migration process completed!")


if __name__ == "__main__":
    main()
