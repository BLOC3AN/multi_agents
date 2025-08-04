"""
Qdrant Vector Database Model for Multi-Agent System.
Handles vector embeddings storage and retrieval for semantic search.
"""
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, SparseVectorParams, Modifier

# Load environment variables
load_dotenv()


@dataclass
class VectorDocument:
    """Vector document model for Qdrant storage."""
    id: Union[str, int]
    text: str
    user_id: str  # Required user_id for file isolation
    title: Optional[str] = None
    source: Optional[str] = None
    page: Optional[int] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Post-initialization to set default values."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

        if self.metadata is None:
            self.metadata = {
                "category": "document",
                "language": "vi"
            }
        
        if self.extra is None:
            self.extra = {
                "summary": None,
                "url": None
            }
    
    def to_payload(self) -> Dict[str, Any]:
        """Convert to Qdrant payload format."""
        return {
            "text": self.text,
            "user_id": self.user_id,
            "title": self.title,
            "source": self.source,
            "page": self.page,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "extra": self.extra
        }
    
    @classmethod
    def from_payload(cls, doc_id: Union[str, int], payload: Dict[str, Any]) -> 'VectorDocument':
        """Create VectorDocument from Qdrant payload."""
        return cls(
            id=doc_id,
            text=payload.get("text", ""),
            user_id=payload.get("user_id", ""),
            title=payload.get("title"),
            source=payload.get("source"),
            page=payload.get("page"),
            timestamp=payload.get("timestamp"),
            metadata=payload.get("metadata", {}),
            extra=payload.get("extra", {})
        )


class QdrantConfig:
    """Qdrant database configuration and connection management."""
    
    def __init__(self, 
                 api_key: str = None, 
                 url: str = None, 
                 collection_name: str = None):
        """
        Initialize Qdrant configuration.
        
        Args:
            api_key: Qdrant Cloud API key
            url: Qdrant Cloud endpoint URL
            collection_name: Collection name for storing vectors
        """
        self.api_key = api_key or os.getenv("QDRANT_CLOUD_API_KEY")
        self.url = url or os.getenv("QDRANT_URL")
        self.collection_name = collection_name or os.getenv("QDRANT_COLLECTION", "agent_data")
        
        if not self.api_key or not self.url:
            raise ValueError("QDRANT_CLOUD_API_KEY and QDRANT_URL must be provided")
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=self.url,
            api_key=self.api_key,
        )
        
        # Test connection and create collection if needed
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize collection with proper configuration."""
        try:
            # Test connection
            collections = self.client.get_collections()
            print(f"✅ Connected to Qdrant Cloud: {self.url}")
            
            # Check if collection exists
            if not self.client.collection_exists(collection_name=self.collection_name):
                print(f"📦 Creating collection: {self.collection_name}")
                
                # Create collection with dense and sparse vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense_vector": VectorParams(
                            size=1024,  # Vector size 1024 dimensions
                            distance=Distance.COSINE
                        )
                    },
                    sparse_vectors_config={
                        "bm25_sparse_vector": SparseVectorParams(
                            modifier=Modifier.IDF  # Enable Inverse Document Frequency
                        )
                    }
                )
                print(f"✅ Collection created successfully: {self.collection_name}")

                # Create payload indexes for filtering
                self._create_payload_indexes()
            else:
                print(f"✅ Collection already exists: {self.collection_name}")

                # Ensure payload indexes exist
                self._create_payload_indexes()
                
        except Exception as e:
            print(f"❌ Failed to initialize Qdrant collection: {e}")
            raise

    def _create_payload_indexes(self):
        """Create payload indexes for efficient filtering."""
        try:
            # Create index for user_id field
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print("✅ Created index for user_id")

            # Create index for title field
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="title",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print("✅ Created index for title")

            # Create index for source field
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="source",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print("✅ Created index for source")

            # Create index for metadata.category
            self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name="metadata.category",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            print("✅ Created index for metadata.category")

        except Exception as e:
            # Indexes might already exist, which is fine
            if "already exists" in str(e).lower():
                print("✅ Payload indexes already exist")
            else:
                print(f"⚠️ Warning: Failed to create some payload indexes: {e}")
    
    def upsert_document(self, 
                       document: VectorDocument, 
                       dense_vector: List[float],
                       sparse_vector: Optional[Dict[str, Any]] = None) -> bool:
        """
        Insert or update a document in Qdrant.
        
        Args:
            document: VectorDocument to store
            dense_vector: Dense embedding vector (1024 dimensions)
            sparse_vector: Optional sparse vector for BM25
            
        Returns:
            bool: Success status
        """
        try:
            # Prepare vectors
            vectors = {
                "dense_vector": dense_vector
            }
            
            if sparse_vector:
                vectors["bm25_sparse_vector"] = sparse_vector
            
            # Upsert point
            self.client.upsert(
                collection_name=self.collection_name,
                points=[
                    models.PointStruct(
                        id=document.id,
                        vector=vectors,
                        payload=document.to_payload()
                    )
                ]
            )
            
            print(f"✅ Document upserted: {document.id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to upsert document: {e}")
            return False
    
    def search_similar(self, 
                      query_vector: List[float],
                      limit: int = 10,
                      score_threshold: float = 0.7,
                      filter_conditions: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar documents using dense vector.
        
        Args:
            query_vector: Query embedding vector
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            filter_conditions: Optional filter conditions
            
        Returns:
            List of similar documents with scores
        """
        try:
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=("dense_vector", query_vector),
                limit=limit,
                score_threshold=score_threshold,
                query_filter=models.Filter(**filter_conditions) if filter_conditions else None,
                with_payload=True,
                with_vectors=False
            )
            
            results = []
            for point in search_result:
                doc = VectorDocument.from_payload(point.id, point.payload)
                results.append({
                    "document": doc,
                    "score": point.score,
                    "id": point.id
                })
            
            return results
            
        except Exception as e:
            print(f"❌ Failed to search documents: {e}")
            return []
    
    def get_document(self, doc_id: Union[str, int]) -> Optional[VectorDocument]:
        """
        Get a specific document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            VectorDocument or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[doc_id],
                with_payload=True,
                with_vectors=False
            )
            
            if result:
                point = result[0]
                return VectorDocument.from_payload(point.id, point.payload)
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to get document: {e}")
            return None
    
    def delete_document(self, doc_id: Union[str, int]) -> bool:
        """
        Delete a document by ID.
        
        Args:
            doc_id: Document ID to delete
            
        Returns:
            bool: Success status
        """
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.PointIdsList(
                    points=[doc_id]
                )
            )
            
            print(f"✅ Document deleted: {doc_id}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to delete document: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """Get collection information and statistics."""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "config": {
                    "vector_size": info.config.params.vectors.get("dense_vector", {}).size if info.config.params.vectors else None,
                    "distance": info.config.params.vectors.get("dense_vector", {}).distance if info.config.params.vectors else None
                }
            }
        except Exception as e:
            print(f"❌ Failed to get collection info: {e}")
            return None

    def check_file_exists(self, user_id: str, file_name: str, source: str = None) -> Optional[VectorDocument]:
        """
        Check if a file has already been embedded for a user.

        Args:
            user_id: User ID
            file_name: File name (title)
            source: Optional source/file_key for more specific matching

        Returns:
            VectorDocument if exists, None otherwise
        """
        try:
            # Build filter conditions
            must_conditions = [
                {
                    "key": "user_id",
                    "match": {"value": user_id}
                },
                {
                    "key": "title",
                    "match": {"value": file_name}
                }
            ]

            if source:
                must_conditions.append({
                    "key": "source",
                    "match": {"value": source}
                })

            filter_conditions = {
                "must": must_conditions
            }

            # Use scroll to find points with filter (more efficient than search for existence check)
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(**filter_conditions),
                limit=1,
                with_payload=True,
                with_vectors=False
            )

            if results:
                point = results[0]
                return VectorDocument.from_payload(point.id, point.payload)

            return None

        except Exception as e:
            print(f"❌ Failed to check file existence: {e}")
            return None

    def delete_user_file_vectors(self, user_id: str, file_name: str, source: str = None) -> bool:
        """
        Delete all vectors for a specific user file.

        Args:
            user_id: User ID
            file_name: File name to delete
            source: Optional source for more specific matching

        Returns:
            bool: Success status
        """
        try:
            # Build filter conditions
            must_conditions = [
                {
                    "key": "user_id",
                    "match": {"value": user_id}
                },
                {
                    "key": "title",
                    "match": {"value": file_name}
                }
            ]

            if source:
                must_conditions.append({
                    "key": "source",
                    "match": {"value": source}
                })

            filter_conditions = {
                "must": must_conditions
            }

            # Delete points with filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(**filter_conditions)
                )
            )

            print(f"✅ Deleted vectors for user {user_id}, file: {file_name}")
            return True

        except Exception as e:
            print(f"❌ Failed to delete file vectors: {e}")
            return False

    def get_user_files(self, user_id: str, limit: int = 100) -> List[VectorDocument]:
        """
        Get all files for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of files to return

        Returns:
            List of VectorDocument for the user
        """
        try:
            filter_conditions = {
                "must": [
                    {
                        "key": "user_id",
                        "match": {"value": user_id}
                    }
                ]
            }

            # Use scroll to get all user files
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(**filter_conditions),
                limit=limit,
                with_payload=True,
                with_vectors=False
            )

            user_files = []
            for point in results:
                doc = VectorDocument.from_payload(point.id, point.payload)
                user_files.append(doc)

            return user_files

        except Exception as e:
            print(f"❌ Failed to get user files: {e}")
            return []


# Global Qdrant configuration instance
_qdrant_config: Optional[QdrantConfig] = None


def get_qdrant_config() -> QdrantConfig:
    """Get or create Qdrant configuration instance."""
    global _qdrant_config
    
    if _qdrant_config is None:
        _qdrant_config = QdrantConfig()
    
    return _qdrant_config


def close_qdrant_connection():
    """Close Qdrant connection."""
    global _qdrant_config
    
    if _qdrant_config:
        # Qdrant client doesn't need explicit closing
        _qdrant_config = None


# Utility functions
def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


def create_vector_document(text: str,
                          user_id: str,
                          title: str = None,
                          source: str = None,
                          page: int = None,
                          category: str = "document",
                          language: str = "vi",
                          summary: str = None,
                          url: str = None,
                          **kwargs) -> VectorDocument:
    """
    Create a VectorDocument with proper structure.

    Args:
        text: Main text content
        user_id: User ID for file isolation
        title: Document title
        source: Source file or origin
        page: Page number if applicable
        category: Document category
        language: Document language
        summary: Document summary
        url: Source URL
        **kwargs: Additional metadata

    Returns:
        VectorDocument instance
    """
    doc_id = generate_document_id()

    metadata = {
        "category": category,
        "language": language,
        **kwargs
    }

    extra = {
        "summary": summary,
        "url": url
    }

    return VectorDocument(
        id=doc_id,
        text=text,
        user_id=user_id,
        title=title,
        source=source,
        page=page,
        metadata=metadata,
        extra=extra
    )
