"""
Context Builder for RAG system.

Builds context from search results for LLM prompts:
- Filters and ranks relevant documents
- Formats context for optimal LLM consumption
- Handles context length limits
- Provides source attribution
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .vector_search import SearchResult


@dataclass
class ContextDocument:
    """Represents a document in the context."""
    title: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]


class ContextBuilder:
    """Builds context from search results for RAG prompts."""
    
    def __init__(self, 
                 max_context_length: int = 4000,
                 min_relevance_score: float = 0.3,
                 max_documents: int = 5):
        """
        Initialize context builder.
        
        Args:
            max_context_length: Maximum context length in characters
            min_relevance_score: Minimum relevance score to include document
            max_documents: Maximum number of documents to include
        """
        self.max_context_length = max_context_length
        self.min_relevance_score = min_relevance_score
        self.max_documents = max_documents
    
    def filter_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Filter search results based on relevance and quality.
        
        Args:
            results: List of search results
            
        Returns:
            Filtered list of relevant results
        """
        # Filter by minimum score
        filtered = [r for r in results if r.score >= self.min_relevance_score]
        
        # Remove duplicates based on content similarity
        unique_results = []
        seen_content = set()
        
        for result in filtered:
            # Simple deduplication based on first 100 characters
            content_key = result.text[:100].strip().lower()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)
        
        # Limit number of documents
        return unique_results[:self.max_documents]
    
    def build_context(self, 
                     search_results: List[SearchResult],
                     query: str = None) -> Dict[str, Any]:
        """
        Build context from search results.
        
        Args:
            search_results: List of search results
            query: Original user query for context
            
        Returns:
            Dictionary containing formatted context and metadata
        """
        if not search_results:
            return {
                "context": "",
                "documents": [],
                "sources": [],
                "total_documents": 0,
                "context_length": 0
            }
        
        # Filter and rank results
        filtered_results = self.filter_results(search_results)
        
        if not filtered_results:
            return {
                "context": "Không tìm thấy tài liệu liên quan đến câu hỏi của bạn.",
                "documents": [],
                "sources": [],
                "total_documents": 0,
                "context_length": 0
            }
        
        # Build context documents
        context_docs = []
        total_length = 0
        
        for i, result in enumerate(filtered_results):
            # Check if adding this document would exceed length limit
            doc_length = len(result.text)
            if total_length + doc_length > self.max_context_length and context_docs:
                break
            
            context_doc = ContextDocument(
                title=result.title or f"Tài liệu {i+1}",
                content=result.text,
                source=result.source,
                score=result.score,
                metadata=result.metadata
            )
            
            context_docs.append(context_doc)
            total_length += doc_length
        
        # Format context for LLM
        context_text = self._format_context(context_docs, query)
        
        # Collect sources
        sources = [doc.source for doc in context_docs if doc.source]
        
        return {
            "context": context_text,
            "documents": [doc.__dict__ for doc in context_docs],
            "sources": list(set(sources)),  # Remove duplicates
            "total_documents": len(context_docs),
            "context_length": len(context_text)
        }
    
    def _format_context(self, 
                       documents: List[ContextDocument],
                       query: str = None) -> str:
        """
        Format context documents for LLM prompt.
        
        Args:
            documents: List of context documents
            query: Original user query
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        
        # Add header
        if query:
            context_parts.append(f"Dựa vào các tài liệu sau để trả lời câu hỏi: '{query}'\n")
        else:
            context_parts.append("Thông tin từ tài liệu liên quan:\n")
        
        # Add each document
        for i, doc in enumerate(documents, 1):
            doc_section = f"""
=== Tài liệu {i}: {doc.title} ===
Nguồn: {doc.source}
Độ liên quan: {doc.score:.2f}

{doc.content.strip()}
"""
            context_parts.append(doc_section)
        
        # Add footer
        context_parts.append(f"\n--- Kết thúc tài liệu tham khảo ({len(documents)} tài liệu) ---")
        
        return "\n".join(context_parts)
    
    def build_simple_context(self, search_results: List[SearchResult]) -> str:
        """
        Build simple context string without metadata.
        
        Args:
            search_results: List of search results
            
        Returns:
            Simple context string
        """
        context_data = self.build_context(search_results)
        return context_data["context"]
    
    def get_context_summary(self, search_results: List[SearchResult]) -> Dict[str, Any]:
        """
        Get summary of context without full text.
        
        Args:
            search_results: List of search results
            
        Returns:
            Context summary with metadata only
        """
        context_data = self.build_context(search_results)
        
        return {
            "total_documents": context_data["total_documents"],
            "sources": context_data["sources"],
            "context_length": context_data["context_length"],
            "document_titles": [doc["title"] for doc in context_data["documents"]],
            "avg_relevance": sum(doc["score"] for doc in context_data["documents"]) / len(context_data["documents"]) if context_data["documents"] else 0
        }
