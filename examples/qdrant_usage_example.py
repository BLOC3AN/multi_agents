"""
Example usage of Qdrant Vector Database Model.
Demonstrates how to use the Qdrant model for vector storage and retrieval.
"""
import sys
import os
import numpy as np

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.model_qdrant import (
    get_qdrant_config,
    create_vector_document,
    VectorDocument
)


def generate_mock_embedding(text: str, dimension: int = 1024) -> list:
    """
    Generate a mock embedding vector for demonstration.
    In real usage, you would use a proper embedding model like:
    - OpenAI embeddings
    - Sentence Transformers
    - Google Universal Sentence Encoder
    - etc.
    """
    # Simple hash-based mock embedding (for demo only)
    np.random.seed(hash(text) % (2**32))
    return np.random.rand(dimension).tolist()


def example_basic_operations():
    """Demonstrate basic Qdrant operations."""
    print("🚀 Starting Qdrant Basic Operations Example")
    
    try:
        # Get Qdrant configuration
        qdrant = get_qdrant_config()
        print(f"✅ Connected to Qdrant collection: {qdrant.collection_name}")
        
        # Get collection info
        info = qdrant.get_collection_info()
        if info:
            print(f"📊 Collection info: {info['points_count']} points, {info['vectors_count']} vectors")
        
        # Create sample documents
        documents = [
            {
                "text": "Python là một ngôn ngữ lập trình mạnh mẽ và dễ học",
                "title": "Giới thiệu Python",
                "source": "python_tutorial.md",
                "category": "programming"
            },
            {
                "text": "Machine Learning là một nhánh của trí tuệ nhân tạo",
                "title": "Machine Learning cơ bản",
                "source": "ml_basics.md",
                "category": "ai"
            },
            {
                "text": "Vector database giúp tìm kiếm semantic hiệu quả",
                "title": "Vector Database",
                "source": "vector_db.md",
                "category": "database"
            }
        ]
        
        # Store documents
        stored_docs = []
        for doc_data in documents:
            # Create vector document
            doc = create_vector_document(user_id="demo_user", **doc_data)
            
            # Generate embedding (mock)
            embedding = generate_mock_embedding(doc.text)
            
            # Store in Qdrant
            success = qdrant.upsert_document(doc, embedding)
            if success:
                stored_docs.append((doc, embedding))
                print(f"✅ Stored: {doc.title}")
            else:
                print(f"❌ Failed to store: {doc.title}")
        
        print(f"\n📚 Stored {len(stored_docs)} documents")
        
        return stored_docs
        
    except Exception as e:
        print(f"❌ Error in basic operations: {e}")
        return []


def example_search_operations(stored_docs):
    """Demonstrate search operations."""
    print("\n🔍 Starting Search Operations Example")
    
    if not stored_docs:
        print("❌ No documents to search")
        return
    
    try:
        qdrant = get_qdrant_config()
        
        # Example 1: Search with exact document vector
        print("\n1️⃣ Exact Match Search:")
        doc, vector = stored_docs[0]
        results = qdrant.search_similar(
            query_vector=vector,
            limit=3,
            score_threshold=0.5
        )
        
        for i, result in enumerate(results):
            print(f"   {i+1}. {result['document'].title} (score: {result['score']:.3f})")
        
        # Example 2: Search with query text
        print("\n2️⃣ Query Text Search:")
        query_text = "lập trình Python machine learning"
        query_vector = generate_mock_embedding(query_text)
        
        results = qdrant.search_similar(
            query_vector=query_vector,
            limit=5,
            score_threshold=0.3
        )
        
        print(f"   Query: '{query_text}'")
        for i, result in enumerate(results):
            doc = result['document']
            print(f"   {i+1}. {doc.title} (score: {result['score']:.3f})")
            print(f"      Text: {doc.text[:50]}...")
        
        # Example 3: Search with filters
        print("\n3️⃣ Filtered Search:")
        filter_conditions = {
            "must": [
                {
                    "key": "metadata.category",
                    "match": {"value": "programming"}
                }
            ]
        }
        
        results = qdrant.search_similar(
            query_vector=query_vector,
            limit=3,
            score_threshold=0.1,
            filter_conditions=filter_conditions
        )
        
        print(f"   Filter: category = 'programming'")
        for i, result in enumerate(results):
            doc = result['document']
            print(f"   {i+1}. {doc.title} (category: {doc.metadata['category']})")
        
    except Exception as e:
        print(f"❌ Error in search operations: {e}")


def example_document_management(stored_docs):
    """Demonstrate document management operations."""
    print("\n📝 Starting Document Management Example")
    
    if not stored_docs:
        print("❌ No documents to manage")
        return
    
    try:
        qdrant = get_qdrant_config()
        
        # Get a specific document
        doc, _ = stored_docs[0]
        print(f"\n1️⃣ Retrieving document: {doc.id}")
        
        retrieved_doc = qdrant.get_document(doc.id)
        if retrieved_doc:
            print(f"   ✅ Found: {retrieved_doc.title}")
            print(f"   Text: {retrieved_doc.text[:50]}...")
            print(f"   Author: {retrieved_doc.metadata.get('author', 'Unknown')}")
        else:
            print(f"   ❌ Document not found")
        
        # Update a document
        print(f"\n2️⃣ Updating document: {doc.id}")
        
        # Create updated version
        updated_doc = VectorDocument(
            id=doc.id,
            text=doc.text + " (Updated version)",
            user_id=doc.user_id,
            title=doc.title + " - Updated",
            source=doc.source,
            metadata={**doc.metadata, "version": "2.0"},
            extra={**doc.extra, "last_updated": "2025-08-04"}
        )
        
        # Generate new embedding
        new_embedding = generate_mock_embedding(updated_doc.text)
        
        # Update in Qdrant
        success = qdrant.upsert_document(updated_doc, new_embedding)
        if success:
            print(f"   ✅ Document updated successfully")
        else:
            print(f"   ❌ Failed to update document")
        
        # Verify update
        updated_retrieved = qdrant.get_document(doc.id)
        if updated_retrieved and "Updated" in updated_retrieved.title:
            print(f"   ✅ Update verified: {updated_retrieved.title}")
        
    except Exception as e:
        print(f"❌ Error in document management: {e}")


def example_cleanup(stored_docs):
    """Clean up example documents."""
    print("\n🧹 Cleaning up example documents")
    
    try:
        qdrant = get_qdrant_config()
        
        for doc, _ in stored_docs:
            success = qdrant.delete_document(doc.id)
            if success:
                print(f"   ✅ Deleted: {doc.title}")
            else:
                print(f"   ❌ Failed to delete: {doc.title}")
        
        print("✅ Cleanup completed")
        
    except Exception as e:
        print(f"❌ Error in cleanup: {e}")


def main():
    """Run all examples."""
    print("🎯 Qdrant Vector Database Usage Examples")
    print("=" * 50)
    
    # Check environment
    if not os.getenv("QDRANT_CLOUD_API_KEY") or not os.getenv("QDRANT_URL"):
        print("❌ Missing Qdrant configuration in .env file")
        print("💡 Please set QDRANT_CLOUD_API_KEY and QDRANT_URL")
        return
    
    try:
        # Run examples
        stored_docs = example_basic_operations()
        
        if stored_docs:
            example_search_operations(stored_docs)
            example_document_management(stored_docs)
            example_cleanup(stored_docs)
        
        print("\n🎉 All examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Example execution failed: {e}")
        print("💡 Make sure Qdrant Cloud is accessible and credentials are correct")


if __name__ == "__main__":
    main()
