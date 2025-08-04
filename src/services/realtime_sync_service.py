"""
Real-time Data Synchronization Service.
Handles real-time sync events and notifications.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from .data_sync_service import get_data_sync_service


class SyncEventType(Enum):
    """Types of sync events."""
    FILE_UPLOADED = "file_uploaded"
    FILE_DELETED = "file_deleted"
    FILE_UPDATED = "file_updated"
    EMBEDDING_CREATED = "embedding_created"
    EMBEDDING_DELETED = "embedding_deleted"
    SYNC_ISSUE_DETECTED = "sync_issue_detected"
    SYNC_ISSUE_RESOLVED = "sync_issue_resolved"


@dataclass
class SyncEvent:
    """Sync event data structure."""
    event_type: SyncEventType
    user_id: str
    file_id: Optional[str] = None
    file_key: Optional[str] = None
    file_name: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()


class RealtimeSyncService:
    """Service for real-time data synchronization."""
    
    def __init__(self):
        self.sync_service = get_data_sync_service()
        self.event_handlers: Dict[SyncEventType, List[Callable]] = {}
        self.active_connections: List[Any] = []  # WebSocket connections
        
    def register_event_handler(self, event_type: SyncEventType, handler: Callable):
        """Register an event handler for specific sync events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def add_websocket_connection(self, websocket):
        """Add a WebSocket connection for real-time updates."""
        self.active_connections.append(websocket)
    
    def remove_websocket_connection(self, websocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def emit_sync_event(self, event: SyncEvent):
        """Emit a sync event to all handlers and connections."""
        print(f"📡 Emitting sync event: {event.event_type.value} for user {event.user_id}")
        
        # Call registered handlers
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    print(f"❌ Error in sync event handler: {e}")
        
        # Send to WebSocket connections
        await self._broadcast_to_websockets(event)
    
    async def _broadcast_to_websockets(self, event: SyncEvent):
        """Broadcast event to all active WebSocket connections."""
        if not self.active_connections:
            return
        
        message = {
            "type": "sync_event",
            "event": asdict(event)
        }
        
        # Remove closed connections
        active_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
                active_connections.append(connection)
            except Exception:
                # Connection closed, remove it
                pass
        
        self.active_connections = active_connections
    
    async def handle_file_upload(self, user_id: str, file_id: str, file_key: str, 
                                file_name: str, metadata: Dict[str, Any] = None):
        """Handle file upload event."""
        event = SyncEvent(
            event_type=SyncEventType.FILE_UPLOADED,
            user_id=user_id,
            file_id=file_id,
            file_key=file_key,
            file_name=file_name,
            metadata=metadata
        )
        
        await self.emit_sync_event(event)
        
        # Check sync status after upload
        await self._check_sync_status_after_event(user_id, file_key)
    
    async def handle_file_deletion(self, user_id: str, file_key: str, file_name: str):
        """Handle file deletion event."""
        event = SyncEvent(
            event_type=SyncEventType.FILE_DELETED,
            user_id=user_id,
            file_key=file_key,
            file_name=file_name
        )
        
        await self.emit_sync_event(event)
    
    async def handle_embedding_created(self, user_id: str, file_key: str, 
                                     file_name: str, embedding_id: str):
        """Handle embedding creation event."""
        event = SyncEvent(
            event_type=SyncEventType.EMBEDDING_CREATED,
            user_id=user_id,
            file_key=file_key,
            file_name=file_name,
            metadata={"embedding_id": embedding_id}
        )
        
        await self.emit_sync_event(event)
    
    async def handle_embedding_deleted(self, user_id: str, file_key: str, file_name: str):
        """Handle embedding deletion event."""
        event = SyncEvent(
            event_type=SyncEventType.EMBEDDING_DELETED,
            user_id=user_id,
            file_key=file_key,
            file_name=file_name
        )
        
        await self.emit_sync_event(event)
    
    async def _check_sync_status_after_event(self, user_id: str, file_key: str):
        """Check sync status after an event and emit issues if found."""
        try:
            # Analyze sync for this specific user
            records = self.sync_service.analyze_file_sync(user_id)
            
            # Find the specific file record
            file_record = None
            for record in records:
                if record.file_key == file_key:
                    file_record = record
                    break
            
            if file_record and file_record.sync_issues:
                # Emit sync issue event
                issue_event = SyncEvent(
                    event_type=SyncEventType.SYNC_ISSUE_DETECTED,
                    user_id=user_id,
                    file_key=file_key,
                    file_name=file_record.file_name,
                    metadata={
                        "issues": file_record.sync_issues,
                        "sync_status": file_record.sync_status.value,
                        "locations": {
                            "mongodb": file_record.in_mongodb,
                            "s3": file_record.in_s3,
                            "qdrant": file_record.in_qdrant
                        }
                    }
                )
                
                await self.emit_sync_event(issue_event)
        
        except Exception as e:
            print(f"❌ Error checking sync status: {e}")
    
    async def periodic_sync_check(self, interval_minutes: int = 30):
        """Perform periodic sync checks for all users."""
        while True:
            try:
                print(f"🔄 Starting periodic sync check")
                
                # Get all users with files
                db_config = self.sync_service.db_config
                users = db_config.file_metadata.distinct("user_id", {"is_active": True})
                
                for user_id in users:
                    try:
                        # Quick sync check for each user
                        records = self.sync_service.analyze_file_sync(user_id)
                        issues_found = [r for r in records if r.sync_issues]
                        
                        if issues_found:
                            print(f"⚠️ Found {len(issues_found)} sync issues for user {user_id}")
                            
                            # Emit summary event
                            summary_event = SyncEvent(
                                event_type=SyncEventType.SYNC_ISSUE_DETECTED,
                                user_id=user_id,
                                metadata={
                                    "total_issues": len(issues_found),
                                    "files_with_issues": [r.file_name for r in issues_found],
                                    "periodic_check": True
                                }
                            )
                            
                            await self.emit_sync_event(summary_event)
                    
                    except Exception as e:
                        print(f"❌ Error checking sync for user {user_id}: {e}")
                
                print(f"✅ Periodic sync check completed")
                
                # Wait for next check
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                print(f"❌ Error in periodic sync check: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def get_sync_status_summary(self, user_id: str = None) -> Dict[str, Any]:
        """Get a quick sync status summary."""
        try:
            records = self.sync_service.analyze_file_sync(user_id)
            
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "total_files": len(records),
                "synced_files": len([r for r in records if not r.sync_issues]),
                "files_with_issues": len([r for r in records if r.sync_issues]),
                "storage_distribution": {
                    "mongodb_only": len([r for r in records if r.in_mongodb and not r.in_s3 and not r.in_qdrant]),
                    "s3_only": len([r for r in records if not r.in_mongodb and r.in_s3 and not r.in_qdrant]),
                    "qdrant_only": len([r for r in records if not r.in_mongodb and not r.in_s3 and r.in_qdrant]),
                    "all_three": len([r for r in records if r.in_mongodb and r.in_s3 and r.in_qdrant])
                }
            }
            
            return summary
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Global service instance
_realtime_sync_service: Optional[RealtimeSyncService] = None


def get_realtime_sync_service() -> RealtimeSyncService:
    """Get or create realtime sync service instance."""
    global _realtime_sync_service
    
    if _realtime_sync_service is None:
        _realtime_sync_service = RealtimeSyncService()
    
    return _realtime_sync_service


# Event handler examples
async def log_sync_event(event: SyncEvent):
    """Example event handler that logs sync events."""
    print(f"📝 Sync Event Log: {event.event_type.value} - {event.file_name} (User: {event.user_id})")


async def notify_admin_on_issues(event: SyncEvent):
    """Example event handler that notifies admin of sync issues."""
    if event.event_type == SyncEventType.SYNC_ISSUE_DETECTED:
        print(f"🚨 Admin Alert: Sync issues detected for {event.file_name} (User: {event.user_id})")
        # Here you could send email, Slack notification, etc.


# Auto-register default handlers
def setup_default_handlers():
    """Setup default event handlers."""
    sync_service = get_realtime_sync_service()
    sync_service.register_event_handler(SyncEventType.FILE_UPLOADED, log_sync_event)
    sync_service.register_event_handler(SyncEventType.FILE_DELETED, log_sync_event)
    sync_service.register_event_handler(SyncEventType.SYNC_ISSUE_DETECTED, notify_admin_on_issues)
