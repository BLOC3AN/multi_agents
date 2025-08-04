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

# Import file embedding service
try:
    from src.services.file_embedding_service import get_file_embedding_service
    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ File embedding service not available: {e}")
    EMBEDDING_SERVICE_AVAILABLE = False

# Import realtime sync service
try:
    from src.services.realtime_sync_service import get_realtime_sync_service
    REALTIME_SYNC_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Realtime sync service not available: {e}")
    REALTIME_SYNC_AVAILABLE = False


class FileManager:
    """Service class for managing user files with limits and isolation."""
    
    MAX_FILES_PER_USER = 50
    
    def __init__(self):
        self.db_config = get_db_config()
        self.file_collection: Collection = self.db_config.file_metadata
        self.s3_manager = None
        self.embedding_service = None
        self.realtime_sync = None

        try:
            self.s3_manager = get_s3_manager()
        except Exception as e:
            print(f"⚠️ S3 manager not available: {e}")

        # Initialize embedding service
        if EMBEDDING_SERVICE_AVAILABLE:
            try:
                self.embedding_service = get_file_embedding_service()
                if self.embedding_service.is_available():
                    print("✅ File embedding service initialized")
                else:
                    print("⚠️ File embedding service not available (Qdrant issue)")
            except Exception as e:
                print(f"⚠️ Failed to initialize embedding service: {e}")

        # Initialize realtime sync service
        if REALTIME_SYNC_AVAILABLE:
            try:
                self.realtime_sync = get_realtime_sync_service()
                print("✅ Realtime sync service initialized")
            except Exception as e:
                print(f"⚠️ Failed to initialize realtime sync service: {e}")
    
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

            # Delete embedding if available
            if self.embedding_service and self.embedding_service.is_available():
                self.embedding_service.delete_file_embedding(user_id, file_doc["file_name"], file_key)

            # Emit sync event
            if self.realtime_sync:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.realtime_sync.handle_file_deletion(
                        user_id, file_key, file_doc["file_name"]
                    ))
                except Exception as e:
                    print(f"⚠️ Failed to emit file deletion sync event: {e}")

            return True
            
        except Exception as e:
            print(f"❌ Failed to delete file {file_key}: {e}")
            return False
    
    def handle_file_upload(self, user_id: str, file_key: str, file_name: str,
                          file_size: int, content_type: str, s3_bucket: str = None,
                          file_content: bytes = None) -> Dict[str, Any]:
        """Handle complete file upload process with limit checking and embedding."""
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

            # Try to embed file if content is provided and embedding service is available
            embedding_result = None
            if file_content and self.embedding_service and self.embedding_service.is_available():
                try:
                    embedding_result = self.embedding_service.embed_file(
                        user_id=user_id,
                        filename=file_name,
                        file_content=file_content,
                        content_type=content_type,
                        file_key=file_key,
                        metadata={"file_id": file_id, "file_size": file_size}
                    )
                except Exception as e:
                    print(f"⚠️ Failed to embed file {file_name}: {e}")

            result = {
                "success": True,
                "file_id": file_id,
                "message": "File uploaded successfully",
                "file_count": self.get_user_file_count(user_id)
            }

            if embedding_result:
                result["embedding_id"] = embedding_result
                result["message"] += " and embedded for search"

                # Emit embedding created event
                if self.realtime_sync:
                    import asyncio
                    try:
                        loop = asyncio.get_event_loop()
                        loop.create_task(self.realtime_sync.handle_embedding_created(
                            user_id, file_key, file_name, embedding_result
                        ))
                    except Exception as e:
                        print(f"⚠️ Failed to emit embedding created sync event: {e}")

            # Emit file upload event
            if self.realtime_sync:
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(self.realtime_sync.handle_file_upload(
                        user_id, file_id, file_key, file_name,
                        {"file_size": file_size, "content_type": content_type}
                    ))
                except Exception as e:
                    print(f"⚠️ Failed to emit file upload sync event: {e}")

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to handle file upload"
            }

    def embed_existing_file(self, user_id: str, file_key: str) -> Dict[str, Any]:
        """
        Embed an existing file that wasn't embedded during upload.

        Args:
            user_id: User ID
            file_key: File key to embed

        Returns:
            Result dictionary
        """
        try:
            if not self.embedding_service or not self.embedding_service.is_available():
                return {
                    "success": False,
                    "error": "Embedding service not available"
                }

            # Get file metadata
            file_doc = self.get_file_metadata(file_key, user_id)
            if not file_doc:
                return {
                    "success": False,
                    "error": "File not found or access denied"
                }

            # Check if already embedded
            if self.embedding_service.check_file_embedded(user_id, file_doc["file_name"], file_key):
                return {
                    "success": True,
                    "message": "File already embedded",
                    "already_embedded": True
                }

            # Download file content from S3
            if not self.s3_manager:
                return {
                    "success": False,
                    "error": "S3 manager not available"
                }

            download_result = self.s3_manager.download_file(file_key)
            if not download_result["success"]:
                return {
                    "success": False,
                    "error": f"Failed to download file: {download_result['error']}"
                }

            # Embed the file
            embedding_result = self.embedding_service.embed_file(
                user_id=user_id,
                filename=file_doc["file_name"],
                file_content=download_result["file_data"],
                content_type=file_doc["content_type"],
                file_key=file_key,
                metadata={
                    "file_id": file_doc["file_id"],
                    "file_size": file_doc["file_size"]
                }
            )

            if embedding_result:
                return {
                    "success": True,
                    "message": "File embedded successfully",
                    "embedding_id": embedding_result
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to embed file"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get or create file manager instance."""
    global _file_manager
    
    if _file_manager is None:
        _file_manager = FileManager()
    
    return _file_manager
