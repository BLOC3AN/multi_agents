#!/usr/bin/env python3
"""
File Health Check Script for Multi-Agent System.
Monitors file system health and provides diagnostics.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.models import get_db_config


def check_file_health():
    """Check overall file system health."""
    try:
        db = get_db_config()
        
        # Get file statistics
        total_files = db.file_metadata.count_documents({})
        active_files = db.file_metadata.count_documents({"is_active": True})
        inactive_files = db.file_metadata.count_documents({"is_active": False})
        
        # Get recent activity
        last_24h = datetime.utcnow() - timedelta(hours=24)
        last_24h_str = last_24h.isoformat()
        
        recent_uploads = db.file_metadata.count_documents({
            "upload_date": {"$gte": last_24h_str}
        })
        
        recent_deletions = db.file_metadata.count_documents({
            "deleted_at": {"$exists": True, "$gte": last_24h_str}
        })
        
        # Get user statistics
        user_pipeline = [
            {"$match": {"is_active": True}},
            {"$group": {"_id": "$user_id", "file_count": {"$sum": 1}}},
            {"$sort": {"file_count": -1}}
        ]
        user_stats = list(db.file_metadata.aggregate(user_pipeline))
        
        # Print report
        print("File System Health Report")
        print("=" * 50)
        print(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print()
        
        print("📊 Overall Statistics:")
        print(f"  Total files in database: {total_files}")
        print(f"  Active files: {active_files}")
        print(f"  Inactive files: {inactive_files}")
        print(f"  Active percentage: {(active_files/total_files*100):.1f}%" if total_files > 0 else "  No files found")
        print()
        
        print("📈 Recent Activity (Last 24 hours):")
        print(f"  New uploads: {recent_uploads}")
        print(f"  Deletions: {recent_deletions}")
        print()
        
        print("👥 Top Users by File Count:")
        for i, user_stat in enumerate(user_stats[:10], 1):
            print(f"  {i:2d}. {user_stat['_id']}: {user_stat['file_count']} files")
        print()
        
        # Health warnings
        warnings = []
        
        if total_files > 0 and (active_files / total_files) < 0.5:
            warnings.append("⚠️  More than 50% of files are inactive")
        
        if recent_deletions > recent_uploads * 2:
            warnings.append("⚠️  High deletion rate compared to uploads")
        
        if active_files == 0 and total_files > 0:
            warnings.append("🚨 No active files found - possible system issue")
        
        if warnings:
            print("⚠️  Health Warnings:")
            for warning in warnings:
                print(f"  {warning}")
            print()
        else:
            print("✅ No health issues detected")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking file health: {e}")
        return False


def check_s3_sync():
    """Check S3 synchronization status."""
    try:
        from src.database.model_s3 import get_s3_manager
        
        print("🔄 S3 Sync Status:")
        
        try:
            s3_manager = get_s3_manager()
            s3_files = s3_manager.list_files()
            print(f"  S3 files found: {len(s3_files)}")
            
            # Get active files from database
            db = get_db_config()
            db_files = list(db.file_metadata.find({"is_active": True}))
            
            print(f"  Database active files: {len(db_files)}")
            
            # Check for mismatches
            db_file_keys = {f["file_key"] for f in db_files}
            s3_file_keys = {f["Key"] for f in s3_files}
            
            missing_in_s3 = db_file_keys - s3_file_keys
            missing_in_db = s3_file_keys - db_file_keys
            
            if missing_in_s3:
                print(f"  ⚠️  Files in DB but missing in S3: {len(missing_in_s3)}")
                for key in list(missing_in_s3)[:5]:
                    print(f"    - {key}")
                if len(missing_in_s3) > 5:
                    print(f"    ... and {len(missing_in_s3) - 5} more")
            
            if missing_in_db:
                print(f"  ⚠️  Files in S3 but missing in DB: {len(missing_in_db)}")
                for key in list(missing_in_db)[:5]:
                    print(f"    - {key}")
                if len(missing_in_db) > 5:
                    print(f"    ... and {len(missing_in_db) - 5} more")
            
            if not missing_in_s3 and not missing_in_db:
                print("  ✅ S3 and database are in sync")
            
        except Exception as e:
            print(f"  ❌ S3 check failed: {e}")
        
        print()
        
    except ImportError:
        print("🔄 S3 Sync Status: S3 manager not available")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Check file system health")
    parser.add_argument("--s3", action="store_true", help="Include S3 sync check")
    
    args = parser.parse_args()
    
    success = check_file_health()
    
    if args.s3:
        check_s3_sync()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
