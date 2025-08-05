#!/usr/bin/env python3
"""
Test script to check RAG availability and functionality.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rag_import():
    """Test if RAG agent can be imported."""
    print("🔍 Testing RAG agent import...")
    
    try:
        from src.RAG.rag_agent import RAGAgent
        print("✅ RAG agent imported successfully")
        return True
    except ImportError as e:
        print(f"❌ RAG agent import failed: {e}")
        return False

def test_rag_initialization():
    """Test if RAG agent can be initialized."""
    print("\n🔍 Testing RAG agent initialization...")
    
    try:
        from src.RAG.rag_agent import RAGAgent
        from src.llms.llm_factory import LLMFactory
        from src.config.settings import config
        
        llm_factory = LLMFactory(config.llm)
        rag_agent = RAGAgent(llm_factory)
        
        print(f"✅ RAG agent initialized successfully")
        print(f"   RAG Available: {rag_agent.rag_available}")
        print(f"   Search Type: {rag_agent.search_type}")
        print(f"   Max Results: {rag_agent.max_search_results}")
        
        return rag_agent
        
    except Exception as e:
        print(f"❌ RAG agent initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_rag_search(rag_agent):
    """Test RAG search functionality."""
    print("\n🔍 Testing RAG search functionality...")
    
    if not rag_agent:
        print("❌ No RAG agent to test")
        return False
    
    try:
        # Test search
        test_query = "IELTS speaking topics"
        user_id = "admin"
        
        print(f"   Query: {test_query}")
        print(f"   User ID: {user_id}")
        
        # Test context retrieval
        context = rag_agent._retrieve_context(test_query, user_id)
        
        print(f"✅ RAG search completed")
        print(f"   Documents found: {context['total_documents']}")
        print(f"   Context length: {context['context_length']}")
        print(f"   Sources: {len(context['sources'])}")
        
        if context['total_documents'] > 0:
            print(f"   First source: {context['sources'][0] if context['sources'] else 'None'}")
            print(f"   Context preview: {context['context'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_graph():
    """Test the simple graph configuration."""
    print("\n🔍 Testing simple graph configuration...")
    
    try:
        from src.core.simple_graph import RAG_AVAILABLE, create_simple_agent_graph
        
        print(f"   RAG_AVAILABLE: {RAG_AVAILABLE}")
        
        # Create graph
        graph = create_simple_agent_graph()
        print(f"✅ Simple graph created successfully")
        
        # Test with sample input
        from src.core.simple_graph import create_initial_state
        
        test_input = "What are some IELTS speaking topics?"
        user_id = "admin"
        
        initial_state = create_initial_state(
            user_input=test_input,
            user_id=user_id
        )
        
        print(f"   Testing with input: {test_input}")
        print(f"   User ID: {user_id}")
        
        # Process through graph
        result = graph.invoke(initial_state)
        
        print(f"✅ Graph processing completed")
        print(f"   Success: {result.get('errors') is None}")
        print(f"   Response length: {len(result.get('final_result', ''))}")
        
        if result.get('rag_metadata'):
            metadata = result['rag_metadata']
            print(f"   RAG Metadata:")
            print(f"     Search type: {metadata.get('search_type')}")
            print(f"     Documents found: {metadata.get('documents_found')}")
            print(f"     Sources: {len(metadata.get('sources', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple graph test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 RAG AVAILABILITY TEST")
    print("="*50)
    
    # Test 1: Import
    import_success = test_rag_import()
    
    # Test 2: Initialization
    rag_agent = test_rag_initialization() if import_success else None
    
    # Test 3: Search functionality
    search_success = test_rag_search(rag_agent) if rag_agent else False
    
    # Test 4: Simple graph
    graph_success = test_simple_graph()
    
    # Summary
    print(f"\n📊 TEST SUMMARY")
    print("="*30)
    print(f"Import: {'✅' if import_success else '❌'}")
    print(f"Initialization: {'✅' if rag_agent else '❌'}")
    print(f"Search: {'✅' if search_success else '❌'}")
    print(f"Graph: {'✅' if graph_success else '❌'}")
    
    if all([import_success, rag_agent, search_success, graph_success]):
        print(f"\n🎉 All tests passed! RAG is fully functional.")
    else:
        print(f"\n⚠️ Some tests failed. RAG may not be working properly.")

if __name__ == "__main__":
    main()
