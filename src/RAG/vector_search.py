"""
Vector Search Service for RAG system.

Provides vector search capabilities using Qdrant database with:
- Dense vector search (cosine similarity)
- Sparse vector search (BM25)
- Hybrid search combining both approaches
- User isolation and filtering
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from qdrant_client import models

# Import existing Qdrant infrastructure
try:
    from src.database.model_qdrant import get_qdrant_config, QdrantConfig
    from src.services.file_embedding_service import EmbeddingProvider
    QDRANT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Qdrant infrastructure not available: {e}")
    QDRANT_AVAILABLE = False


@dataclass
class SearchResult:
    """Represents a search result from vector database."""
    id: str
    score: float
    text: str
    title: str
    source: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "score": self.score,
            "text": self.text,
            "title": self.title,
            "source": self.source,
            "metadata": self.metadata
        }


class VectorSearchService:
    """Service for performing vector searches in Qdrant database."""
    
    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        """
        Initialize vector search service.
        
        Args:
            embedding_provider: Optional embedding provider for query encoding
        """
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant infrastructure not available")
            
        self.qdrant = get_qdrant_config()
        self.embedding_provider = embedding_provider or EmbeddingProvider()
        
    def search_dense(self,
                    query: str,
                    user_id: str,
                    limit: int = 10,
                    score_threshold: float = 0.0) -> List[SearchResult]:
        """
        Perform dense vector search using cosine similarity.
        
        Args:
            query: Search query text
            user_id: User ID for isolation
            limit: Maximum number of results
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results sorted by relevance
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_provider.encode(query)

            # Convert to list if needed (embedding provider returns list)
            if hasattr(query_embedding, 'tolist'):
                query_vector = query_embedding.tolist()
            else:
                query_vector = list(query_embedding) if not isinstance(query_embedding, list) else query_embedding

            # Perform search with user isolation
            search_result = self.qdrant.client.search(
                collection_name=self.qdrant.collection_name,
                query_vector=models.NamedVector(
                    name="dense_vector",
                    vector=query_vector
                ),
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to SearchResult objects
            results = []
            for point in search_result:
                result = SearchResult(
                    id=str(point.id),
                    score=point.score,
                    text=point.payload.get("text", ""),
                    title=point.payload.get("title", ""),
                    source=point.payload.get("source", ""),
                    metadata=point.payload
                )
                results.append(result)
            
            print(f"🔍 Dense search found {len(results)} results for user {user_id}")
            return results
            
        except Exception as e:
            print(f"❌ Dense search failed: {e}")
            return []
    
    def search_sparse(self,
                     query: str,
                     user_id: str, 
                     limit: int = 10) -> List[SearchResult]:
        """
        Perform sparse vector search using BM25.
        
        Args:
            query: Search query text
            user_id: User ID for isolation
            limit: Maximum number of results
            
        Returns:
            List of search results sorted by BM25 score
        """
        try:
            # Create sparse vector from query (simple word-based approach)
            words = query.lower().split()
            sparse_vector = models.SparseVector(
                indices=[hash(word) % 10000 for word in words],
                values=[1.0] * len(words)
            )
            
            # Perform sparse search
            search_result = self.qdrant.client.search(
                collection_name=self.qdrant.collection_name,
                query_vector=models.NamedSparseVector(
                    name="bm25_sparse_vector",
                    vector=sparse_vector
                ),
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id)
                        )
                    ]
                ),
                limit=limit
            )
            
            # Convert to SearchResult objects
            results = []
            for point in search_result:
                result = SearchResult(
                    id=str(point.id),
                    score=point.score,
                    text=point.payload.get("text", ""),
                    title=point.payload.get("title", ""),
                    source=point.payload.get("source", ""),
                    metadata=point.payload
                )
                results.append(result)
            
            print(f"🔍 Sparse search found {len(results)} results for user {user_id}")
            return results
            
        except Exception as e:
            print(f"❌ Sparse search failed: {e}")
            return []
    
    def search_hybrid(self,
                     query: str,
                     user_id: str,
                     limit: int = 10,
                     dense_weight: float = 0.7,
                     sparse_weight: float = 0.3) -> List[SearchResult]:
        """
        Perform hybrid search combining dense and sparse results.
        
        Args:
            query: Search query text
            user_id: User ID for isolation
            limit: Maximum number of results
            dense_weight: Weight for dense search results
            sparse_weight: Weight for sparse search results
            
        Returns:
            List of search results with combined scores
        """
        try:
            # Get results from both search methods
            dense_results = self.search_dense(query, user_id, limit * 2)
            sparse_results = self.search_sparse(query, user_id, limit * 2)
            
            # Combine and re-rank results
            combined_results = {}
            
            # Add dense results with weight
            for result in dense_results:
                combined_results[result.id] = result
                combined_results[result.id].score = result.score * dense_weight
            
            # Add sparse results with weight (combine if already exists)
            for result in sparse_results:
                if result.id in combined_results:
                    # Combine scores
                    combined_results[result.id].score += result.score * sparse_weight
                else:
                    # New result from sparse search
                    combined_results[result.id] = result
                    combined_results[result.id].score = result.score * sparse_weight
            
            # Sort by combined score and limit results
            final_results = sorted(
                combined_results.values(),
                key=lambda x: x.score,
                reverse=True
            )[:limit]
            
            print(f"🔍 Hybrid search found {len(final_results)} results for user {user_id}")
            return final_results
            
        except Exception as e:
            print(f"❌ Hybrid search failed: {e}")
            # Fallback to dense search only
            return self.search_dense(query, user_id, limit)
    
    def search(self,
              query: str,
              user_id: str,
              search_type: str = "hybrid",
              limit: int = 10,
              **kwargs) -> List[SearchResult]:
        """
        Unified search interface.
        
        Args:
            query: Search query text
            user_id: User ID for isolation
            search_type: Type of search ("dense", "sparse", "hybrid")
            limit: Maximum number of results
            **kwargs: Additional search parameters
            
        Returns:
            List of search results
        """
        if search_type == "dense":
            return self.search_dense(query, user_id, limit, **kwargs)
        elif search_type == "sparse":
            return self.search_sparse(query, user_id, limit, **kwargs)
        elif search_type == "hybrid":
            return self.search_hybrid(query, user_id, limit, **kwargs)
        else:
            raise ValueError(f"Unsupported search type: {search_type}")
