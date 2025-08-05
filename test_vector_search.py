#!/usr/bin/env python3
"""
Test vector search functionality step by step.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_embedding_provider():
    """Test embedding provider directly."""
    print("🔍 Testing embedding provider...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        embedding_provider = embedding_service.embedding_provider
        
        print(f"   Embedding provider type: {type(embedding_provider)}")
        print(f"   Has encode method: {hasattr(embedding_provider, 'encode')}")
        
        if hasattr(embedding_provider, 'encode'):
            test_text = "IELTS speaking topics"
            embedding = embedding_provider.encode(test_text)
            print(f"   Test encoding successful: {len(embedding)} dimensions")
            print(f"   Embedding type: {type(embedding)}")
            return True
        else:
            print(f"   Available methods: {[m for m in dir(embedding_provider) if not m.startswith('_')]}")
            return False
        
    except Exception as e:
        print(f"❌ Embedding provider test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_qdrant_direct_search():
    """Test direct Qdrant search with manual embedding."""
    print("\n🔍 Testing direct Qdrant search...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        from qdrant_client import models
        
        embedding_service = get_file_embedding_service()
        qdrant = embedding_service.qdrant
        embedding_provider = embedding_service.embedding_provider
        
        # Generate embedding
        test_query = "IELTS speaking topics"
        query_embedding = embedding_provider.encode(test_query)
        
        print(f"   Query: {test_query}")
        print(f"   Embedding length: {len(query_embedding)}")
        print(f"   Embedding type: {type(query_embedding)}")

        # Convert to list if needed
        if hasattr(query_embedding, 'tolist'):
            query_vector = query_embedding.tolist()
        else:
            query_vector = list(query_embedding) if not isinstance(query_embedding, list) else query_embedding

        print(f"   Vector length: {len(query_vector)}")
        print(f"   First 5 values: {query_vector[:5]}")
        
        # Perform search with named vector
        search_result = qdrant.client.search(
            collection_name=qdrant.collection_name,
            query_vector=models.NamedVector(
                name="dense_vector",
                vector=query_vector
            ),
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value="admin")
                    )
                ]
            ),
            limit=5,
            with_payload=True
        )
        
        print(f"   Search results: {len(search_result)}")
        
        for i, result in enumerate(search_result[:3], 1):
            print(f"   {i}. Score: {result.score:.4f}")
            print(f"      Title: {result.payload.get('title', '')[:50]}...")
            print(f"      Text: {result.payload.get('text', '')[:100]}...")
        
        return len(search_result) > 0
        
    except Exception as e:
        print(f"❌ Direct Qdrant search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_search_service_fixed():
    """Test vector search service with proper initialization."""
    print("\n🔍 Testing vector search service (fixed)...")
    
    try:
        from src.RAG.vector_search import VectorSearchService
        from src.services.file_embedding_service import get_file_embedding_service
        
        # Get embedding service
        embedding_service = get_file_embedding_service()
        
        # Initialize search service with proper embedding provider
        search_service = VectorSearchService(embedding_service.embedding_provider)
        
        print(f"   Search service initialized")
        print(f"   Embedding provider: {type(search_service.embedding_provider)}")
        print(f"   Has encode method: {hasattr(search_service.embedding_provider, 'encode')}")
        
        # Test search
        test_query = "IELTS speaking topics"
        user_id = "admin"
        
        print(f"   Testing query: {test_query}")
        
        # Test dense search
        dense_results = search_service.search_dense(test_query, user_id, limit=5)
        print(f"   Dense search: {len(dense_results)} results")
        
        if dense_results:
            print(f"   Best match: {dense_results[0].title[:50]}...")
            print(f"   Score: {dense_results[0].score:.4f}")
        
        # Test hybrid search
        hybrid_results = search_service.search_hybrid(test_query, user_id, limit=5)
        print(f"   Hybrid search: {len(hybrid_results)} results")
        
        return len(dense_results) > 0 or len(hybrid_results) > 0
        
    except Exception as e:
        print(f"❌ Vector search service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_collection_info():
    """Test collection information and vector configuration."""
    print("\n🔍 Testing collection information...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        qdrant = embedding_service.qdrant
        
        # Get collection info
        collection_info = qdrant.client.get_collection(qdrant.collection_name)
        
        print(f"   Collection: {qdrant.collection_name}")
        print(f"   Points count: {collection_info.points_count}")
        print(f"   Vectors count: {collection_info.vectors_count}")
        print(f"   Config: {collection_info.config}")
        
        # Check vector configuration
        if hasattr(collection_info.config, 'params'):
            params = collection_info.config.params
            print(f"   Vector params: {params}")
            
            if hasattr(params, 'vectors'):
                vectors_config = params.vectors
                print(f"   Vectors config: {vectors_config}")
        
        return True
        
    except Exception as e:
        print(f"❌ Collection info test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sample_point():
    """Test retrieving and examining a sample point."""
    print("\n🔍 Testing sample point...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        from qdrant_client import models
        
        embedding_service = get_file_embedding_service()
        qdrant = embedding_service.qdrant
        
        # Get a sample point
        search_result = qdrant.client.scroll(
            collection_name=qdrant.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value="admin")
                    )
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=True
        )
        
        points, _ = search_result
        
        if points:
            point = points[0]
            print(f"   Point ID: {point.id}")
            print(f"   Payload keys: {list(point.payload.keys())}")
            print(f"   User ID: {point.payload.get('user_id')}")
            print(f"   Title: {point.payload.get('title', '')[:50]}...")
            
            if point.vector:
                if isinstance(point.vector, dict):
                    print(f"   Vector keys: {list(point.vector.keys())}")
                    for name, vector in point.vector.items():
                        print(f"   Vector '{name}': {len(vector) if vector else 0} dimensions")
                else:
                    print(f"   Vector: {len(point.vector)} dimensions")
            
            return True
        else:
            print(f"   No points found")
            return False
        
    except Exception as e:
        print(f"❌ Sample point test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 VECTOR SEARCH DETAILED TEST")
    print("="*50)
    
    # Test 1: Embedding provider
    embedding_success = test_embedding_provider()
    
    # Test 2: Collection info
    collection_success = test_collection_info()
    
    # Test 3: Sample point
    sample_success = test_sample_point()
    
    # Test 4: Direct Qdrant search
    direct_success = test_qdrant_direct_search()
    
    # Test 5: Vector search service (fixed)
    service_success = test_vector_search_service_fixed()
    
    # Summary
    print(f"\n📊 DETAILED TEST SUMMARY")
    print("="*40)
    print(f"Embedding Provider: {'✅' if embedding_success else '❌'}")
    print(f"Collection Info: {'✅' if collection_success else '❌'}")
    print(f"Sample Point: {'✅' if sample_success else '❌'}")
    print(f"Direct Search: {'✅' if direct_success else '❌'}")
    print(f"Service Search: {'✅' if service_success else '❌'}")
    
    if all([embedding_success, collection_success, sample_success, direct_success, service_success]):
        print(f"\n🎉 All detailed tests passed! Vector search is working.")
    else:
        print(f"\n⚠️ Some detailed tests failed. Vector search needs fixing.")

if __name__ == "__main__":
    main()
