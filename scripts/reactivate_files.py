#!/usr/bin/env python3
"""
Script to reactivate deleted files in the database.
This script helps recover files that were marked as inactive.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config


def reactivate_recent_files(days_back=7, dry_run=True):
    """
    Reactivate files that were deleted within the last N days.
    
    Args:
        days_back (int): Number of days to look back for deleted files
        dry_run (bool): If True, only show what would be reactivated without making changes
    """
    try:
        db = get_db_config()
        
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        cutoff_str = cutoff_date.isoformat()
        
        # Find deleted files within the time range
        query = {
            "is_active": False,
            "deleted_at": {"$exists": True, "$gte": cutoff_str}
        }
        
        deleted_files = list(db.file_metadata.find(query).sort("upload_date", -1))
        
        print(f"Found {len(deleted_files)} deleted files from the last {days_back} days:")
        print("-" * 80)
        
        for i, file_doc in enumerate(deleted_files, 1):
            print(f"{i:2d}. {file_doc.get('file_name', 'unknown')}")
            print(f"    User: {file_doc.get('user_id', 'unknown')}")
            print(f"    Upload: {file_doc.get('upload_date', 'unknown')}")
            print(f"    Deleted: {file_doc.get('deleted_at', 'unknown')}")
            print(f"    Size: {file_doc.get('file_size', 0)} bytes")
            print()
        
        if not deleted_files:
            print("No deleted files found in the specified time range.")
            return
        
        if dry_run:
            print("DRY RUN MODE - No changes made.")
            print("Run with --apply to actually reactivate these files.")
            return
        
        # Reactivate files
        print("Reactivating files...")
        reactivated_count = 0
        
        for file_doc in deleted_files:
            result = db.file_metadata.update_one(
                {"_id": file_doc["_id"]},
                {
                    "$set": {"is_active": True},
                    "$unset": {"deleted_at": ""}
                }
            )
            
            if result.modified_count > 0:
                reactivated_count += 1
                print(f"✅ Reactivated: {file_doc.get('file_name', 'unknown')}")
            else:
                print(f"❌ Failed to reactivate: {file_doc.get('file_name', 'unknown')}")
        
        print(f"\nReactivated {reactivated_count} out of {len(deleted_files)} files.")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Reactivate deleted files")
    parser.add_argument("--days", type=int, default=7, help="Number of days to look back (default: 7)")
    parser.add_argument("--apply", action="store_true", help="Actually apply changes (default: dry run)")
    
    args = parser.parse_args()
    
    print("File Reactivation Script")
    print("=" * 50)
    
    success = reactivate_recent_files(
        days_back=args.days,
        dry_run=not args.apply
    )
    
    if success:
        print("\nScript completed successfully.")
    else:
        print("\nScript failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
