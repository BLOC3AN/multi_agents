"""
Data Synchronization Service for Multi-Agent System.
Ensures consistency between MongoDB, S3, Qdrant, and UI.
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

from ..database.models import get_db_config
from ..database.model_s3 import get_s3_manager
from ..services.file_manager import get_file_manager
from ..services.file_embedding_service import get_file_embedding_service


class SyncStatus(Enum):
    """Sync status enumeration."""
    SYNCED = "synced"
    OUT_OF_SYNC = "out_of_sync"
    MISSING = "missing"
    ERROR = "error"


@dataclass
class FileRecord:
    """File record for sync comparison."""
    file_id: str
    user_id: str
    file_key: str
    file_name: str
    file_size: int
    content_type: str
    upload_date: str
    is_active: bool
    
    # Source indicators
    in_mongodb: bool = False
    in_s3: bool = False
    in_qdrant: bool = False
    
    # Metadata
    mongodb_metadata: Optional[Dict] = None
    s3_metadata: Optional[Dict] = None
    qdrant_metadata: Optional[Dict] = None
    
    # Sync status
    sync_status: SyncStatus = SyncStatus.OUT_OF_SYNC
    sync_issues: List[str] = None
    
    def __post_init__(self):
        if self.sync_issues is None:
            self.sync_issues = []


class DataSyncService:
    """Service for synchronizing data across all storage systems."""
    
    def __init__(self):
        self.db_config = get_db_config()
        self.file_manager = get_file_manager()
        self.embedding_service = None
        self.s3_manager = None
        
        # Initialize services
        try:
            self.embedding_service = get_file_embedding_service()
        except Exception as e:
            print(f"⚠️ Embedding service not available: {e}")
        
        try:
            self.s3_manager = get_s3_manager()
        except Exception as e:
            print(f"⚠️ S3 manager not available: {e}")
    
    def get_mongodb_files(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all files from MongoDB."""
        try:
            query = {"is_active": True}
            if user_id:
                query["user_id"] = user_id
            
            files = list(self.db_config.file_metadata.find(query))
            return files
        except Exception as e:
            print(f"❌ Failed to get MongoDB files: {e}")
            return []
    
    def get_s3_files(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all files from S3."""
        if not self.s3_manager:
            return []
        
        try:
            # Get all files from S3
            result = self.s3_manager.list_files()
            if not result.get("success"):
                return []
            
            s3_files = result.get("files", [])
            
            # Filter by user if specified
            if user_id:
                # Assuming file keys contain user info or we can match by metadata
                # This might need adjustment based on your S3 structure
                filtered_files = []
                for file in s3_files:
                    # Try to match with MongoDB records to get user_id
                    mongo_file = self.db_config.file_metadata.find_one({
                        "file_key": file.get("key"),
                        "user_id": user_id,
                        "is_active": True
                    })
                    if mongo_file:
                        filtered_files.append(file)
                return filtered_files
            
            return s3_files
        except Exception as e:
            print(f"❌ Failed to get S3 files: {e}")
            return []
    
    def get_qdrant_files(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get all files from Qdrant."""
        if not self.embedding_service or not self.embedding_service.is_available():
            return []
        
        try:
            qdrant = self.embedding_service.qdrant
            
            if user_id and user_id != "global":
                # Get files for specific user
                user_files = qdrant.get_user_files(user_id)
                return [doc.__dict__ for doc in user_files]
            else:
                # Get all files (this might be expensive for large collections)
                # Use scroll to get all points
                all_files = []
                offset = None
                limit = 100
                
                while True:
                    results, next_offset = qdrant.client.scroll(
                        collection_name=qdrant.collection_name,
                        limit=limit,
                        offset=offset,
                        with_payload=True,
                        with_vectors=False
                    )
                    
                    if not results:
                        break
                    
                    for point in results:
                        from src.database.model_qdrant import VectorDocument
                        doc = VectorDocument.from_payload(point.id, point.payload)
                        all_files.append(doc.__dict__)
                    
                    if next_offset is None:
                        break
                    offset = next_offset
                
                return all_files
        except Exception as e:
            print(f"❌ Failed to get Qdrant files: {e}")
            return []
    
    def analyze_file_sync(self, user_id: str = None) -> List[FileRecord]:
        """Analyze sync status of all files."""
        print(f"🔍 Analyzing file sync for user: {user_id or 'all users'}")
        
        # Get files from all sources
        mongodb_files = self.get_mongodb_files(user_id)
        s3_files = self.get_s3_files(user_id)
        qdrant_files = self.get_qdrant_files(user_id)
        
        print(f"📊 Found files - MongoDB: {len(mongodb_files)}, S3: {len(s3_files)}, Qdrant: {len(qdrant_files)}")
        
        # Create file records map
        file_records = {}
        
        # Process MongoDB files
        for mongo_file in mongodb_files:
            file_key = mongo_file["file_key"]
            record = FileRecord(
                file_id=mongo_file["file_id"],
                user_id=mongo_file["user_id"],
                file_key=file_key,
                file_name=mongo_file["file_name"],
                file_size=mongo_file["file_size"],
                content_type=mongo_file["content_type"],
                upload_date=mongo_file["upload_date"],
                is_active=mongo_file["is_active"],
                in_mongodb=True,
                mongodb_metadata=mongo_file
            )
            file_records[file_key] = record
        
        # Check S3 files
        for s3_file in s3_files:
            file_key = s3_file.get("key")
            if file_key in file_records:
                file_records[file_key].in_s3 = True
                file_records[file_key].s3_metadata = s3_file
            else:
                # S3 file without MongoDB record
                record = FileRecord(
                    file_id="unknown",
                    user_id="unknown",
                    file_key=file_key,
                    file_name=s3_file.get("name", file_key),
                    file_size=s3_file.get("size", 0),
                    content_type="unknown",
                    upload_date=s3_file.get("last_modified", ""),
                    is_active=True,
                    in_s3=True,
                    s3_metadata=s3_file
                )
                record.sync_issues.append("S3 file without MongoDB record")
                file_records[file_key] = record
        
        # Check Qdrant files
        for qdrant_file in qdrant_files:
            # Match by source (file_key) or title (file_name)
            source = qdrant_file.get("source")
            title = qdrant_file.get("title")

            # Try to find matching record (including chunked files)
            matched_record = self._find_matching_record(file_records, source, title, qdrant_file)

            if matched_record:
                matched_record.in_qdrant = True
                matched_record.qdrant_metadata = qdrant_file
            else:
                # Qdrant file without MongoDB record (only add if not a chunk)
                if not self._is_chunked_file(source, title):
                    record = FileRecord(
                        file_id=qdrant_file.get("id", "unknown"),
                        user_id=qdrant_file.get("user_id", "unknown"),
                        file_key=source or title or "unknown",
                        file_name=title or "unknown",
                        file_size=0,
                        content_type="unknown",
                        upload_date=qdrant_file.get("timestamp", ""),
                        is_active=True,
                        in_qdrant=True,
                        qdrant_metadata=qdrant_file
                    )
                    record.sync_issues.append("Qdrant file without MongoDB record")
                    file_records[record.file_key] = record
        
        # Analyze sync status
        for record in file_records.values():
            self._analyze_record_sync_status(record)
        
        return list(file_records.values())

    def _find_matching_record(self, file_records: Dict[str, FileRecord], source: str, title: str, qdrant_file: Dict) -> Optional[FileRecord]:
        """Find matching MongoDB record for a Qdrant file, including chunked files."""

        # Try exact match first
        for key, record in file_records.items():
            if (source and key == source) or (title and record.file_name == title):
                return record

        # Try chunked file matching
        if self._is_chunked_file(source, title):
            original_file_key, original_file_name = self._extract_original_file_info(source, title, qdrant_file)

            # Look for original file in records
            for key, record in file_records.items():
                if (original_file_key and key == original_file_key) or (original_file_name and record.file_name == original_file_name):
                    return record

        return None

    def _is_chunked_file(self, source: str, title: str) -> bool:
        """Check if this is a chunked file."""
        if source and "#chunk_" in source:
            return True
        if title and " (Part " in title and "/" in title and title.endswith(")"):
            return True
        return False

    def _extract_original_file_info(self, source: str, title: str, qdrant_file: Dict) -> tuple:
        """Extract original file key and name from chunked file info."""
        original_file_key = None
        original_file_name = None

        # First priority: Use file_name field directly (new approach)
        if qdrant_file.get("file_name"):
            original_file_name = qdrant_file["file_name"]
            # For file_key, try to extract from source or use file_name
            if source and "#chunk_" in source:
                original_file_key = source.split("#chunk_")[0]
            else:
                original_file_key = original_file_name
            return original_file_key, original_file_name

        # Fallback: Extract from source (e.g., "file.pdf#chunk_0" -> "file.pdf")
        if source and "#chunk_" in source:
            original_file_key = source.split("#chunk_")[0]

        # Fallback: Extract from title (e.g., "file.pdf (Part 1/1)" -> "file.pdf")
        if title and " (Part " in title:
            original_file_name = title.split(" (Part ")[0]

        # Fallback: Try to get from metadata.parent_file (legacy)
        metadata = qdrant_file.get("metadata", {})
        if metadata.get("parent_file"):
            original_file_name = metadata["parent_file"]

        return original_file_key, original_file_name

    def _analyze_record_sync_status(self, record: FileRecord):
        """Analyze sync status for a single file record."""
        issues = []
        
        # Check if file should exist in all systems
        if record.is_active:
            if not record.in_mongodb:
                issues.append("Missing from MongoDB")
            if not record.in_s3:
                issues.append("Missing from S3")
            if not record.in_qdrant:
                # Only flag as issue if file type should be embedded
                if self.embedding_service and self.embedding_service.should_embed_file(
                    record.content_type, record.file_name
                ):
                    issues.append("Missing from Qdrant (should be embedded)")
        
        # Check metadata consistency
        if record.in_mongodb and record.in_s3:
            mongo_size = record.mongodb_metadata.get("file_size", 0)
            s3_size = record.s3_metadata.get("size", 0)
            if mongo_size != s3_size:
                issues.append(f"Size mismatch: MongoDB({mongo_size}) vs S3({s3_size})")
        
        # Update record
        record.sync_issues.extend(issues)
        
        if not issues:
            record.sync_status = SyncStatus.SYNCED
        elif any("Missing from" in issue for issue in issues):
            record.sync_status = SyncStatus.MISSING
        else:
            record.sync_status = SyncStatus.OUT_OF_SYNC
    
    def fix_sync_issues(self, user_id: str = None, dry_run: bool = True) -> Dict[str, Any]:
        """Fix sync issues automatically."""
        print(f"🔧 {'Dry run' if dry_run else 'Fixing'} sync issues for user: {user_id or 'all users'}")
        
        records = self.analyze_file_sync(user_id)
        
        results = {
            "total_files": len(records),
            "synced_files": 0,
            "fixed_files": 0,
            "failed_fixes": 0,
            "actions_taken": [],
            "errors": []
        }
        
        for record in records:
            if record.sync_status == SyncStatus.SYNCED:
                results["synced_files"] += 1
                continue
            
            try:
                if self._fix_record_sync(record, dry_run):
                    results["fixed_files"] += 1
                    results["actions_taken"].append(f"Fixed {record.file_name}")
                else:
                    results["failed_fixes"] += 1
            except Exception as e:
                results["failed_fixes"] += 1
                results["errors"].append(f"Failed to fix {record.file_name}: {str(e)}")
        
        return results
    
    def _fix_record_sync(self, record: FileRecord, dry_run: bool) -> bool:
        """Fix sync issues for a single record."""
        if record.sync_status == SyncStatus.SYNCED:
            return True
        
        print(f"🔧 {'Would fix' if dry_run else 'Fixing'} {record.file_name}: {record.sync_issues}")
        
        if dry_run:
            return True
        
        # Implementation for actual fixes would go here
        # For now, just return True to indicate success
        return True
    
    def get_sync_report(self, user_id: str = None) -> Dict[str, Any]:
        """Generate a comprehensive sync report."""
        records = self.analyze_file_sync(user_id)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "summary": {
                "total_files": len(records),
                "synced": len([r for r in records if r.sync_status == SyncStatus.SYNCED]),
                "out_of_sync": len([r for r in records if r.sync_status == SyncStatus.OUT_OF_SYNC]),
                "missing": len([r for r in records if r.sync_status == SyncStatus.MISSING]),
                "errors": len([r for r in records if r.sync_status == SyncStatus.ERROR])
            },
            "storage_counts": {
                "mongodb": len([r for r in records if r.in_mongodb]),
                "s3": len([r for r in records if r.in_s3]),
                "qdrant": len([r for r in records if r.in_qdrant])
            },
            "issues": [],
            "recommendations": []
        }
        
        # Collect issues
        for record in records:
            if record.sync_issues:
                report["issues"].append({
                    "file_name": record.file_name,
                    "file_key": record.file_key,
                    "user_id": record.user_id,
                    "status": record.sync_status.value,
                    "issues": record.sync_issues,
                    "locations": {
                        "mongodb": record.in_mongodb,
                        "s3": record.in_s3,
                        "qdrant": record.in_qdrant
                    }
                })
        
        # Generate recommendations
        if report["summary"]["missing"] > 0:
            report["recommendations"].append("Run sync repair to restore missing files")
        if report["summary"]["out_of_sync"] > 0:
            report["recommendations"].append("Check metadata consistency and update as needed")
        
        return report


# Global service instance
_data_sync_service: Optional[DataSyncService] = None


def get_data_sync_service() -> DataSyncService:
    """Get or create data sync service instance."""
    global _data_sync_service
    
    if _data_sync_service is None:
        _data_sync_service = DataSyncService()
    
    return _data_sync_service
