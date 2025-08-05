#!/usr/bin/env python3
"""
Debug script to test RAG search functionality in detail.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_direct_qdrant_search():
    """Test direct Qdrant search."""
    print("🔍 Testing direct Qdrant search...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        qdrant = embedding_service.qdrant
        
        # Test 1: Get all points for user admin
        print("\n📊 Getting all points for user 'admin'...")
        
        from qdrant_client import models
        
        # Search with user filter
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
            limit=5,
            with_payload=True,
            with_vectors=False
        )
        
        points, next_page_offset = search_result
        print(f"   Found {len(points)} points for user 'admin'")
        
        if points:
            for i, point in enumerate(points[:3], 1):
                print(f"   {i}. ID: {point.id}")
                print(f"      User: {point.payload.get('user_id')}")
                print(f"      Title: {point.payload.get('title', '')[:50]}...")
                print(f"      Text: {point.payload.get('text', '')[:100]}...")
        
        return len(points) > 0
        
    except Exception as e:
        print(f"❌ Direct Qdrant search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_search_service():
    """Test the vector search service."""
    print("\n🔍 Testing vector search service...")
    
    try:
        from src.RAG.vector_search import VectorSearchService
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        search_service = VectorSearchService(embedding_service.qdrant)
        
        # Test different search types
        test_queries = [
            "IELTS speaking topics",
            "speaking test",
            "topics",
            "IELTS"
        ]
        
        user_id = "admin"
        
        for query in test_queries:
            print(f"\n   Testing query: '{query}'")
            
            # Test dense search
            dense_results = search_service.search_dense(query, user_id, limit=3)
            print(f"     Dense: {len(dense_results)} results")
            
            # Test sparse search  
            sparse_results = search_service.search_sparse(query, user_id, limit=3)
            print(f"     Sparse: {len(sparse_results)} results")
            
            # Test hybrid search
            hybrid_results = search_service.search_hybrid(query, user_id, limit=3)
            print(f"     Hybrid: {len(hybrid_results)} results")
            
            if hybrid_results:
                print(f"     Best match: {hybrid_results[0].title[:50]}...")
                print(f"     Score: {hybrid_results[0].score:.4f}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Vector search service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embedding_generation():
    """Test if embeddings are being generated correctly."""
    print("\n🔍 Testing embedding generation...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        
        # Test embedding generation
        test_text = "IELTS speaking topics"
        embedding = embedding_service.embedding_model.encode(test_text)
        
        print(f"   Text: {test_text}")
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   Embedding type: {type(embedding)}")
        print(f"   First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_search():
    """Test manual search with direct Qdrant client."""
    print("\n🔍 Testing manual search with Qdrant client...")
    
    try:
        from src.services.file_embedding_service import get_file_embedding_service
        from qdrant_client import models
        
        embedding_service = get_file_embedding_service()
        qdrant = embedding_service.qdrant
        
        # Generate embedding for test query
        test_query = "IELTS speaking topics"
        query_embedding = embedding_service.embedding_model.encode(test_query)
        
        print(f"   Query: {test_query}")
        print(f"   Query embedding shape: {query_embedding.shape}")
        
        # Perform manual search
        search_result = qdrant.client.search(
            collection_name=qdrant.collection_name,
            query_vector=query_embedding.tolist(),
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
        
        print(f"   Found {len(search_result)} results")
        
        for i, result in enumerate(search_result[:3], 1):
            print(f"   {i}. Score: {result.score:.4f}")
            print(f"      Title: {result.payload.get('title', '')[:50]}...")
            print(f"      Text: {result.payload.get('text', '')[:100]}...")
        
        return len(search_result) > 0
        
    except Exception as e:
        print(f"❌ Manual search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_with_different_users():
    """Test search with different user IDs."""
    print("\n🔍 Testing search with different user IDs...")
    
    try:
        from src.RAG.vector_search import VectorSearchService
        from src.services.file_embedding_service import get_file_embedding_service
        
        embedding_service = get_file_embedding_service()
        search_service = VectorSearchService(embedding_service.qdrant)
        
        test_query = "IELTS"
        test_users = ["admin", "hailt", "test_user", "default_user"]
        
        for user_id in test_users:
            print(f"   Testing user: {user_id}")
            results = search_service.search_hybrid(test_query, user_id, limit=3)
            print(f"     Results: {len(results)}")
            
            if results:
                print(f"     Best match: {results[0].title[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ User search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function."""
    print("🐛 RAG SEARCH DEBUG")
    print("="*50)
    
    # Test 1: Direct Qdrant search
    direct_success = test_direct_qdrant_search()
    
    # Test 2: Vector search service
    vector_success = test_vector_search_service()
    
    # Test 3: Embedding generation
    embedding_success = test_embedding_generation()
    
    # Test 4: Manual search
    manual_success = test_manual_search()
    
    # Test 5: Different users
    user_success = test_search_with_different_users()
    
    # Summary
    print(f"\n📊 DEBUG SUMMARY")
    print("="*30)
    print(f"Direct Qdrant: {'✅' if direct_success else '❌'}")
    print(f"Vector Service: {'✅' if vector_success else '❌'}")
    print(f"Embedding Gen: {'✅' if embedding_success else '❌'}")
    print(f"Manual Search: {'✅' if manual_success else '❌'}")
    print(f"User Search: {'✅' if user_success else '❌'}")
    
    if all([direct_success, vector_success, embedding_success, manual_success, user_success]):
        print(f"\n🎉 All debug tests passed! Search should be working.")
    else:
        print(f"\n⚠️ Some debug tests failed. There may be search issues.")

if __name__ == "__main__":
    main()
