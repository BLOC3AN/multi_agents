#!/usr/bin/env python3
"""
Script to analyze and fix data synchronization issues.
Identifies files that exist in S3 but are missing from MongoDB and/or Qdrant.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.data_sync_service import get_data_sync_service
from src.services.file_manager import get_file_manager
from src.services.file_embedding_service import get_file_embedding_service
from src.database.model_s3 import get_s3_manager


def analyze_sync_issues(user_id: str = None):
    """Analyze synchronization issues across all storage systems."""
    print("🔍 Starting data synchronization analysis...")
    
    # Get sync service
    sync_service = get_data_sync_service()
    
    # Generate comprehensive report
    report = sync_service.get_sync_report(user_id)
    
    print(f"\n📊 SYNC ANALYSIS REPORT")
    print(f"{'='*50}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"User ID: {report['user_id'] or 'All users'}")
    
    # Summary
    summary = report['summary']
    print(f"\n📈 SUMMARY:")
    print(f"  Total files: {summary['total_files']}")
    print(f"  ✅ Synced: {summary['synced']}")
    print(f"  ⚠️  Out of sync: {summary['out_of_sync']}")
    print(f"  ❌ Missing: {summary['missing']}")
    print(f"  🚫 Errors: {summary['errors']}")
    
    # Storage counts
    storage = report['storage_counts']
    print(f"\n💾 STORAGE DISTRIBUTION:")
    print(f"  MongoDB: {storage['mongodb']} files")
    print(f"  S3: {storage['s3']} files")
    print(f"  Qdrant: {storage['qdrant']} files")
    
    # Issues
    if report['issues']:
        print(f"\n🚨 SYNC ISSUES FOUND:")
        print(f"{'='*50}")
        
        for i, issue in enumerate(report['issues'], 1):
            print(f"\n{i}. File: {issue['file_name']}")
            print(f"   Key: {issue['file_key']}")
            print(f"   User: {issue['user_id']}")
            print(f"   Status: {issue['status']}")
            print(f"   Issues: {', '.join(issue['issues'])}")
            print(f"   Locations:")
            print(f"     MongoDB: {'✅' if issue['locations']['mongodb'] else '❌'}")
            print(f"     S3: {'✅' if issue['locations']['s3'] else '❌'}")
            print(f"     Qdrant: {'✅' if issue['locations']['qdrant'] else '❌'}")
    else:
        print(f"\n✅ No sync issues found!")
    
    # Recommendations
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    return report


def fix_s3_orphan_files(user_id: str = None, dry_run: bool = True):
    """Fix S3 files that are missing MongoDB records and Qdrant embeddings."""
    print(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing S3 orphan files...")

    from src.database.models import get_db_config

    file_manager = get_file_manager()
    embedding_service = get_file_embedding_service()
    s3_manager = get_s3_manager()
    db_config = get_db_config()

    # Get S3 files directly
    s3_result = s3_manager.list_files()
    if not s3_result.get("success"):
        print(f"❌ Failed to get S3 files: {s3_result.get('error')}")
        return

    s3_files = s3_result.get("files", [])
    print(f"📁 Found {len(s3_files)} files in S3")

    fixed_count = 0
    failed_count = 0

    for s3_file in s3_files:
        file_key = s3_file.get("key")
        file_name = s3_file.get("name", file_key)
        file_size = s3_file.get("size", 0)

        print(f"\n📁 Processing S3 file: {file_name}")
        print(f"   Key: {file_key}")
        print(f"   Size: {file_size} bytes")

        # Check if MongoDB record exists
        mongo_record = db_config.file_metadata.find_one({"file_key": file_key, "is_active": True})

        if mongo_record:
            print(f"   ✅ MongoDB record exists for user: {mongo_record['user_id']}")
            target_user_id = mongo_record['user_id']
        else:
            print(f"   ❌ No MongoDB record found")

            if dry_run:
                print("   🔍 DRY RUN: Would create MongoDB record")
                continue

            # Need to determine user_id for orphan file
            if user_id:
                target_user_id = user_id
                print(f"   💡 Using provided user_id: {target_user_id}")
            else:
                # Default to admin user for orphan files
                target_user_id = "admin"
                print(f"   💡 Using default user_id: {target_user_id}")

            try:
                # Download file content
                download_result = s3_manager.download_file(file_key)
                if not download_result.get("success"):
                    print(f"   ❌ Failed to download from S3: {download_result.get('error')}")
                    failed_count += 1
                    continue

                file_content = download_result["file_data"]

                # Determine content type
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_name)
                if not content_type:
                    content_type = "application/octet-stream"

                # Create MongoDB record
                file_id = file_manager.save_file_metadata(
                    user_id=target_user_id,
                    file_key=file_key,
                    file_name=file_name,
                    file_size=file_size,
                    content_type=content_type
                )

                print(f"   ✅ Created MongoDB record: {file_id}")
                mongo_record = {"user_id": target_user_id, "content_type": content_type}

            except Exception as e:
                print(f"   ❌ Error creating MongoDB record: {str(e)}")
                failed_count += 1
                continue

        # Check Qdrant embedding
        if embedding_service and embedding_service.is_available():
            user_files = embedding_service.qdrant.get_user_files(mongo_record['user_id'])
            has_embedding = any(
                doc.source == file_key or doc.title == file_name or doc.file_name == file_name
                for doc in user_files
            )

            if has_embedding:
                print(f"   ✅ Qdrant embedding exists")
            else:
                print(f"   ❌ No Qdrant embedding found")

                if dry_run:
                    print("   🔍 DRY RUN: Would create Qdrant embedding")
                    continue

                # Create embedding
                if embedding_service.should_embed_file(mongo_record.get('content_type', ''), file_name):
                    try:
                        # Download file if not already downloaded
                        download_result = s3_manager.download_file(file_key)
                        if not download_result.get("success"):
                            print(f"   ❌ Failed to download for embedding: {download_result.get('error')}")
                            failed_count += 1
                            continue

                        file_content = download_result["file_data"]

                        # Create embedding
                        doc_ids = embedding_service.embed_file_chunked(
                            user_id=mongo_record['user_id'],
                            filename=file_name,
                            file_content=file_content,
                            content_type=mongo_record.get('content_type', 'application/octet-stream'),
                            file_key=file_key
                        )

                        if doc_ids:
                            print(f"   ✅ Created Qdrant embeddings: {len(doc_ids)} chunks")
                        else:
                            print(f"   ⚠️ Failed to create Qdrant embeddings")

                    except Exception as e:
                        print(f"   ❌ Error creating embedding: {str(e)}")
                        failed_count += 1
                        continue
                else:
                    print(f"   ⏭️ Skipping embedding (unsupported file type)")

        fixed_count += 1

    print(f"\n📊 RESULTS:")
    print(f"  ✅ Processed: {fixed_count}")
    print(f"  ❌ Failed: {failed_count}")


def fix_missing_embeddings(user_id: str = None, dry_run: bool = True):
    """Fix MongoDB files that are missing Qdrant embeddings."""
    print(f"\n🔧 {'DRY RUN: ' if dry_run else ''}Fixing missing embeddings...")

    from src.database.models import get_db_config

    embedding_service = get_file_embedding_service()
    s3_manager = get_s3_manager()
    db_config = get_db_config()

    if not embedding_service or not embedding_service.is_available():
        print("❌ Embedding service not available")
        return

    # Get MongoDB files
    query = {"is_active": True}
    if user_id:
        query["user_id"] = user_id

    mongo_files = list(db_config.file_metadata.find(query))
    print(f"📁 Found {len(mongo_files)} files in MongoDB")

    fixed_count = 0
    failed_count = 0

    for mongo_file in mongo_files:
        file_name = mongo_file["file_name"]
        file_key = mongo_file["file_key"]
        user_id_file = mongo_file["user_id"]
        content_type = mongo_file.get("content_type", "")

        print(f"\n📁 Checking: {file_name} (User: {user_id_file})")

        # Check if embedding exists
        user_files = embedding_service.qdrant.get_user_files(user_id_file)
        has_embedding = any(
            doc.source == file_key or doc.title == file_name or doc.file_name == file_name
            for doc in user_files
        )

        if has_embedding:
            print(f"   ✅ Embedding exists")
            continue

        print(f"   ❌ Missing embedding")

        if dry_run:
            print("   🔍 DRY RUN: Would create embedding")
            continue

        # Check if file type should be embedded
        if not embedding_service.should_embed_file(content_type, file_name):
            print(f"   ⏭️ Skipping (unsupported file type: {content_type})")
            continue

        try:
            # Download file from S3
            download_result = s3_manager.download_file(file_key)
            if not download_result.get("success"):
                print(f"   ❌ Failed to download from S3: {download_result.get('error')}")
                failed_count += 1
                continue

            file_content = download_result["file_data"]

            # Create embedding
            doc_ids = embedding_service.embed_file_chunked(
                user_id=user_id_file,
                filename=file_name,
                file_content=file_content,
                content_type=content_type,
                file_key=file_key
            )

            if doc_ids:
                print(f"   ✅ Created embeddings: {len(doc_ids)} chunks")
                fixed_count += 1
            else:
                print(f"   ⚠️ Failed to create embeddings")
                failed_count += 1

        except Exception as e:
            print(f"   ❌ Error creating embedding: {str(e)}")
            failed_count += 1

    print(f"\n📊 EMBEDDING RESULTS:")
    print(f"  ✅ Fixed: {fixed_count}")
    print(f"  ❌ Failed: {failed_count}")


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze and fix data synchronization issues")
    parser.add_argument("--user-id", help="Analyze specific user (default: all users)")
    parser.add_argument("--fix-orphans", action="store_true", help="Fix S3 orphan files")
    parser.add_argument("--fix-embeddings", action="store_true", help="Fix missing embeddings")
    parser.add_argument("--fix-all", action="store_true", help="Fix all sync issues")
    parser.add_argument("--no-dry-run", action="store_true", help="Actually perform fixes (default is dry run)")

    args = parser.parse_args()

    # Analyze sync issues first
    print("🔍 ANALYZING CURRENT STATE...")
    report = analyze_sync_issues(args.user_id)

    dry_run = not args.no_dry_run

    # Fix issues if requested
    if args.fix_orphans or args.fix_all:
        fix_s3_orphan_files(args.user_id, dry_run=dry_run)

    if args.fix_embeddings or args.fix_all:
        fix_missing_embeddings(args.user_id, dry_run=dry_run)

    if not any([args.fix_orphans, args.fix_embeddings, args.fix_all]):
        print(f"\n💡 To fix issues, use:")
        print(f"  --fix-orphans: Fix S3 files without MongoDB records")
        print(f"  --fix-embeddings: Fix missing Qdrant embeddings")
        print(f"  --fix-all: Fix all issues")
        print(f"  --no-dry-run: Actually perform fixes (default is dry run)")

    return report


if __name__ == "__main__":
    main()
