"""
File management service for Multi-Agent System.
Handles file upload limits, metadata storage, and user file isolation.
"""
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo.collection import Collection

from src.database.models import FileMetadata, get_db_config
from src.database.model_s3 import get_s3_manager


class FileManager:
    """Service class for managing user files with limits and isolation."""
    
    MAX_FILES_PER_USER = 50
    
    def __init__(self):
        self.db_config = get_db_config()
        self.file_collection: Collection = self.db_config.file_metadata
        self.s3_manager = None
        try:
            self.s3_manager = get_s3_manager()
        except Exception as e:
            print(f"⚠️ S3 manager not available: {e}")
    
    def get_user_file_count(self, user_id: str) -> int:
        """Get the number of active files for a user."""
        return self.file_collection.count_documents({
            "user_id": user_id,
            "is_active": True
        })
    
    def get_user_files(self, user_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Get all active files for a user in legacy format."""
        query = {"user_id": user_id, "is_active": True}
        cursor = self.file_collection.find(query).sort("upload_date", -1)

        if limit:
            cursor = cursor.limit(limit)

        files = []
        for file_doc in cursor:
            # Return in legacy format for backward compatibility
            files.append({
                "key": file_doc["file_key"],
                "name": file_doc["file_name"],
                "size": file_doc["file_size"],
                "last_modified": file_doc["upload_date"],
                "folder": file_doc.get("s3_bucket", ""),
                # Keep new fields for advanced usage
                "file_id": file_doc["file_id"],
                "content_type": file_doc["content_type"],
                "metadata": file_doc.get("metadata", {})
            })

        return files
    
    def check_file_limit(self, user_id: str) -> Dict[str, Any]:
        """Check if user has reached file limit."""
        current_count = self.get_user_file_count(user_id)
        
        return {
            "current_count": current_count,
            "max_allowed": self.MAX_FILES_PER_USER,
            "can_upload": current_count < self.MAX_FILES_PER_USER,
            "remaining": max(0, self.MAX_FILES_PER_USER - current_count)
        }
    
    def cleanup_old_files(self, user_id: str, keep_count: int = None) -> List[str]:
        """Remove oldest files to make room for new uploads."""
        if keep_count is None:
            keep_count = self.MAX_FILES_PER_USER - 1
        
        # Get all user files sorted by upload date (oldest first)
        old_files = list(self.file_collection.find({
            "user_id": user_id,
            "is_active": True
        }).sort("upload_date", 1))
        
        files_to_remove = old_files[:-keep_count] if len(old_files) > keep_count else []
        removed_files = []
        
        for file_doc in files_to_remove:
            try:
                # Delete from S3 if available
                if self.s3_manager:
                    self.s3_manager.delete_file(file_doc["file_key"])
                
                # Mark as inactive in database
                self.file_collection.update_one(
                    {"file_id": file_doc["file_id"]},
                    {"$set": {"is_active": False, "deleted_at": datetime.utcnow().isoformat()}}
                )
                
                removed_files.append(file_doc["file_key"])
                print(f"✅ Removed old file: {file_doc['file_name']}")
                
            except Exception as e:
                print(f"⚠️ Failed to remove file {file_doc['file_name']}: {e}")
        
        return removed_files
    
    def save_file_metadata(self, user_id: str, file_key: str, file_name: str, 
                          file_size: int, content_type: str, s3_bucket: str = None,
                          metadata: Dict[str, Any] = None) -> str:
        """Save file metadata to database."""
        file_id = str(uuid.uuid4())
        
        file_metadata = FileMetadata(
            file_id=file_id,
            user_id=user_id,
            file_key=file_key,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            upload_date=datetime.utcnow(),
            s3_bucket=s3_bucket,
            is_active=True,
            metadata=metadata or {}
        )
        
        self.file_collection.insert_one(file_metadata.to_dict())
        return file_id
    
    def get_file_metadata(self, file_key: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get file metadata by file key."""
        query = {"file_key": file_key, "is_active": True}
        if user_id:
            query["user_id"] = user_id
        
        file_doc = self.file_collection.find_one(query)
        return file_doc
    
    def delete_file(self, file_key: str, user_id: str) -> bool:
        """Delete a file (only if owned by user)."""
        try:
            # Check if file belongs to user
            file_doc = self.get_file_metadata(file_key, user_id)
            if not file_doc:
                return False
            
            # Delete from S3 if available
            if self.s3_manager:
                self.s3_manager.delete_file(file_key)
            
            # Mark as inactive in database
            self.file_collection.update_one(
                {"file_key": file_key, "user_id": user_id},
                {"$set": {"is_active": False, "deleted_at": datetime.utcnow().isoformat()}}
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete file {file_key}: {e}")
            return False
    
    def handle_file_upload(self, user_id: str, file_key: str, file_name: str,
                          file_size: int, content_type: str, s3_bucket: str = None) -> Dict[str, Any]:
        """Handle complete file upload process with limit checking."""
        try:
            # Check file limit
            limit_check = self.check_file_limit(user_id)
            
            if not limit_check["can_upload"]:
                # Remove oldest file to make room
                removed_files = self.cleanup_old_files(user_id)
                print(f"📁 Removed {len(removed_files)} old files to make room for new upload")
            
            # Save metadata
            file_id = self.save_file_metadata(
                user_id=user_id,
                file_key=file_key,
                file_name=file_name,
                file_size=file_size,
                content_type=content_type,
                s3_bucket=s3_bucket
            )
            
            return {
                "success": True,
                "file_id": file_id,
                "message": "File uploaded successfully",
                "file_count": self.get_user_file_count(user_id)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to handle file upload"
            }


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get or create file manager instance."""
    global _file_manager
    
    if _file_manager is None:
        _file_manager = FileManager()
    
    return _file_manager
