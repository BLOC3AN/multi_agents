"""
RAG (Retrieval-Augmented Generation) Package

This package provides RAG functionality for the multi-agent system:
- Vector search in Qdrant database
- Hybrid search (dense + sparse vectors)
- Context building from search results
- RAG agent integration with existing LLM providers

Components:
- VectorSearchService: Handle vector/hybrid search operations
- ContextBuilder: Build context from search results
- RAGAgent: Main RAG agent inheriting from BaseAgent
"""

from .vector_search import VectorSearchService
from .context_builder import ContextBuilder
from .rag_agent import RAGAgent

__all__ = [
    "VectorSearchService",
    "ContextBuilder", 
    "RAGAgent"
]

__version__ = "1.0.0"
