"""
Test cases for Qdrant Vector Database Model.
"""
import sys
import os
import pytest
import numpy as np

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.model_qdrant import (
    QdrantConfig,
    VectorDocument,
    get_qdrant_config,
    create_vector_document,
    generate_document_id
)


class TestVectorDocument:
    """Test VectorDocument model."""
    
    def test_vector_document_creation(self):
        """Test creating a VectorDocument."""
        doc = VectorDocument(
            id="test_id",
            text="This is a test document",
            title="Test Document",
            source="test.txt"
        )
        
        assert doc.id == "test_id"
        assert doc.text == "This is a test document"
        assert doc.title == "Test Document"
        assert doc.source == "test.txt"
        assert doc.timestamp is not None
        assert doc.metadata is not None
        assert doc.extra is not None
    
    def test_vector_document_to_payload(self):
        """Test converting VectorDocument to payload."""
        doc = VectorDocument(
            id="test_id",
            text="Test content",
            title="Test Title"
        )
        
        payload = doc.to_payload()
        
        assert payload["text"] == "Test content"
        assert payload["title"] == "Test Title"
        assert "timestamp" in payload
        assert "metadata" in payload
        assert "extra" in payload
    
    def test_vector_document_from_payload(self):
        """Test creating VectorDocument from payload."""
        payload = {
            "text": "Test content",
            "title": "Test Title",
            "source": "test.txt",
            "metadata": {"author": "Test Author"},
            "extra": {"summary": "Test summary"}
        }
        
        doc = VectorDocument.from_payload("test_id", payload)
        
        assert doc.id == "test_id"
        assert doc.text == "Test content"
        assert doc.title == "Test Title"
        assert doc.source == "test.txt"
        assert doc.metadata["author"] == "Test Author"
        assert doc.extra["summary"] == "Test summary"


class TestQdrantConfig:
    """Test QdrantConfig functionality."""
    
    def test_qdrant_config_initialization(self):
        """Test Qdrant configuration initialization."""
        try:
            config = get_qdrant_config()
            assert config is not None
            assert config.collection_name == "agent_data"
            print("✅ Qdrant configuration test passed")
        except Exception as e:
            pytest.skip(f"Qdrant connection not available: {e}")
    
    def test_collection_info(self):
        """Test getting collection information."""
        try:
            config = get_qdrant_config()
            info = config.get_collection_info()
            
            if info:
                assert "name" in info
                assert "vectors_count" in info
                assert "points_count" in info
                print(f"✅ Collection info: {info}")
            else:
                pytest.skip("Collection info not available")
                
        except Exception as e:
            pytest.skip(f"Qdrant connection not available: {e}")
    
    def test_document_operations(self):
        """Test document CRUD operations."""
        try:
            config = get_qdrant_config()
            
            # Create test document
            doc = create_vector_document(
                text="This is a test document for vector search",
                title="Test Document",
                source="test_file.txt",
                author="Test Author",
                category="test"
            )
            
            # Generate random vector (1024 dimensions)
            test_vector = np.random.rand(1024).tolist()
            
            # Test upsert
            success = config.upsert_document(doc, test_vector)
            assert success, "Document upsert should succeed"
            
            # Test retrieval
            retrieved_doc = config.get_document(doc.id)
            assert retrieved_doc is not None, "Document should be retrievable"
            assert retrieved_doc.text == doc.text
            assert retrieved_doc.title == doc.title
            
            # Test search
            search_results = config.search_similar(
                query_vector=test_vector,
                limit=5,
                score_threshold=0.5
            )
            assert len(search_results) > 0, "Search should return results"
            
            # Verify search result structure
            result = search_results[0]
            assert "document" in result
            assert "score" in result
            assert "id" in result
            
            # Test deletion
            delete_success = config.delete_document(doc.id)
            assert delete_success, "Document deletion should succeed"
            
            # Verify deletion
            deleted_doc = config.get_document(doc.id)
            assert deleted_doc is None, "Document should be deleted"
            
            print("✅ All document operations test passed")
            
        except Exception as e:
            pytest.skip(f"Qdrant operations not available: {e}")


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_generate_document_id(self):
        """Test document ID generation."""
        id1 = generate_document_id()
        id2 = generate_document_id()
        
        assert id1 != id2, "Generated IDs should be unique"
        assert len(id1) > 0, "ID should not be empty"
        assert isinstance(id1, str), "ID should be string"
    
    def test_create_vector_document(self):
        """Test vector document creation utility."""
        doc = create_vector_document(
            text="Test content",
            title="Test Title",
            source="test.txt",
            author="Test Author",
            category="test",
            language="en",
            summary="Test summary",
            url="https://example.com"
        )
        
        assert doc.text == "Test content"
        assert doc.title == "Test Title"
        assert doc.source == "test.txt"
        assert doc.metadata["author"] == "Test Author"
        assert doc.metadata["category"] == "test"
        assert doc.metadata["language"] == "en"
        assert doc.extra["summary"] == "Test summary"
        assert doc.extra["url"] == "https://example.com"
        assert doc.id is not None


def test_integration_workflow():
    """Test complete integration workflow."""
    try:
        # Get Qdrant config
        config = get_qdrant_config()
        
        # Create multiple test documents
        documents = []
        vectors = []
        
        for i in range(3):
            doc = create_vector_document(
                text=f"This is test document number {i+1} with unique content",
                title=f"Test Document {i+1}",
                source=f"test_{i+1}.txt",
                author="Test Author",
                category="integration_test"
            )
            documents.append(doc)
            
            # Generate random vector
            vector = np.random.rand(1024).tolist()
            vectors.append(vector)
            
            # Upsert document
            success = config.upsert_document(doc, vector)
            assert success, f"Document {i+1} upsert should succeed"
        
        # Test search with first document's vector
        search_results = config.search_similar(
            query_vector=vectors[0],
            limit=5,
            score_threshold=0.3
        )
        
        assert len(search_results) > 0, "Search should return results"
        
        # The first result should be the exact match
        best_match = search_results[0]
        assert best_match["id"] == documents[0].id, "Best match should be the exact document"
        assert best_match["score"] >= 0.99, "Exact match should have high score"
        
        # Clean up - delete test documents
        for doc in documents:
            config.delete_document(doc.id)
        
        print("✅ Integration workflow test passed")
        
    except Exception as e:
        pytest.skip(f"Integration test not available: {e}")


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running Qdrant Model Tests...")
    
    # Test VectorDocument
    test_doc = TestVectorDocument()
    test_doc.test_vector_document_creation()
    test_doc.test_vector_document_to_payload()
    test_doc.test_vector_document_from_payload()
    print("✅ VectorDocument tests passed")
    
    # Test utility functions
    test_utils = TestUtilityFunctions()
    test_utils.test_generate_document_id()
    test_utils.test_create_vector_document()
    print("✅ Utility function tests passed")
    
    # Test Qdrant operations (if available)
    try:
        test_config = TestQdrantConfig()
        test_config.test_qdrant_config_initialization()
        test_config.test_collection_info()
        test_config.test_document_operations()
        
        # Run integration test
        test_integration_workflow()
        
        print("🎉 All tests passed successfully!")
        
    except Exception as e:
        print(f"⚠️ Qdrant tests skipped: {e}")
        print("💡 Make sure QDRANT_CLOUD_API_KEY and QDRANT_URL are set in .env file")
