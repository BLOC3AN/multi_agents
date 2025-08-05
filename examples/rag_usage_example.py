"""
RAG System Usage Example

Demonstrates how to use the RAG (Retrieval-Augmented Generation) system:
- Vector search for relevant documents
- Context building from search results
- RAG agent for question answering with retrieved context
"""

import sys
import os

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.RAG import VectorSearchService, ContextBuilder, RAGAgent
from src.llms.llm_factory import LLMFactory
from src.config.settings import config
from src.core.types import AgentState


def test_vector_search():
    """Test vector search functionality."""
    print("🔍 Testing Vector Search")
    print("=" * 40)
    
    try:
        # Initialize search service
        search_service = VectorSearchService()
        
        # Test queries
        test_queries = [
            "machine learning algorithms",
            "python programming",
            "data science techniques"
        ]
        
        user_id = "test_user"
        
        for query in test_queries:
            print(f"\n📝 Query: {query}")
            
            # Test different search types
            for search_type in ["dense", "sparse", "hybrid"]:
                try:
                    results = search_service.search(
                        query=query,
                        user_id=user_id,
                        search_type=search_type,
                        limit=3
                    )
                    
                    print(f"  {search_type.capitalize()} search: {len(results)} results")
                    for i, result in enumerate(results[:2]):
                        print(f"    {i+1}. {result.title} (score: {result.score:.3f})")
                        
                except Exception as e:
                    print(f"  ❌ {search_type} search failed: {e}")
        
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")


def test_context_builder():
    """Test context building functionality."""
    print("\n📚 Testing Context Builder")
    print("=" * 40)
    
    try:
        # Initialize services
        search_service = VectorSearchService()
        context_builder = ContextBuilder(max_context_length=2000)
        
        query = "explain machine learning"
        user_id = "test_user"
        
        # Get search results
        results = search_service.search(query, user_id, limit=5)
        
        if results:
            # Build context
            context_data = context_builder.build_context(results, query)
            
            print(f"📊 Context Statistics:")
            print(f"  Documents: {context_data['total_documents']}")
            print(f"  Context length: {context_data['context_length']} chars")
            print(f"  Sources: {len(context_data['sources'])}")
            
            print(f"\n📄 Context Preview:")
            preview = context_data['context'][:500] + "..." if len(context_data['context']) > 500 else context_data['context']
            print(preview)
            
            # Test context summary
            summary = context_builder.get_context_summary(results)
            print(f"\n📋 Context Summary:")
            for key, value in summary.items():
                print(f"  {key}: {value}")
        else:
            print("⚠️ No search results found for context building test")
            
    except Exception as e:
        print(f"❌ Context builder test failed: {e}")


def test_rag_agent():
    """Test RAG agent functionality."""
    print("\n🤖 Testing RAG Agent")
    print("=" * 40)
    
    try:
        # Initialize RAG agent
        llm_factory = LLMFactory(config.llm)
        rag_agent = RAGAgent(
            llm_factory=llm_factory,
            search_type="hybrid",
            max_context_length=3000
        )
        
        # Test queries
        test_queries = [
            "What is machine learning?",
            "Explain Python programming concepts",
            "How does data science work?"
        ]
        
        user_id = "test_user"
        
        for query in test_queries:
            print(f"\n❓ Query: {query}")
            
            # Create agent state
            state = AgentState(
                input=query,
                user_id=user_id,
                conversation_context=[],
                detected_intents=None,
                primary_intent=None,
                agent_results=None,
                final_result=None,
                errors=None,
                processing_mode="single",
                execution_summary=None
            )
            
            # Process with RAG agent
            result_state = rag_agent.process(state)
            
            if result_state["errors"]:
                print(f"  ❌ Error: {result_state['errors']}")
            else:
                response = result_state["final_result"]
                print(f"  ✅ Response: {response[:200]}...")
                
                # Show RAG metadata if available
                if "rag_metadata" in result_state:
                    metadata = result_state["rag_metadata"]
                    print(f"  📊 RAG Metadata:")
                    print(f"    Search type: {metadata['search_type']}")
                    print(f"    Documents found: {metadata['documents_found']}")
                    print(f"    Context length: {metadata['context_length']}")
                    print(f"    Sources: {len(metadata['sources'])}")
        
    except Exception as e:
        print(f"❌ RAG agent test failed: {e}")


def interactive_rag_demo():
    """Interactive RAG demonstration."""
    print("\n🎯 Interactive RAG Demo")
    print("=" * 40)
    print("Type your questions (or 'quit' to exit)")
    
    try:
        # Initialize RAG agent
        llm_factory = LLMFactory(config.llm)
        rag_agent = RAGAgent(llm_factory=llm_factory)
        
        user_id = "demo_user"
        conversation_context = []
        
        while True:
            query = input("\n❓ Your question: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                break
            
            if not query:
                continue
            
            # Create state
            state = AgentState(
                input=query,
                user_id=user_id,
                conversation_context=conversation_context,
                detected_intents=None,
                primary_intent=None,
                agent_results=None,
                final_result=None,
                errors=None,
                processing_mode="single",
                execution_summary=None
            )
            
            # Process query
            result_state = rag_agent.process(state)
            
            if result_state["errors"]:
                print(f"❌ Error: {result_state['errors']}")
            else:
                response = result_state["final_result"]
                print(f"\n🤖 RAG Agent: {response}")
                
                # Show metadata
                if "rag_metadata" in result_state:
                    metadata = result_state["rag_metadata"]
                    print(f"\n📊 Found {metadata['documents_found']} relevant documents")
                
                # Update conversation context
                conversation_context.append({"role": "user", "content": query})
                conversation_context.append({"role": "assistant", "content": response})
                
                # Keep only last 6 messages
                if len(conversation_context) > 6:
                    conversation_context = conversation_context[-6:]
    
    except KeyboardInterrupt:
        print("\n👋 Demo ended by user")
    except Exception as e:
        print(f"❌ Interactive demo failed: {e}")


def main():
    """Run all RAG system tests."""
    print("🚀 RAG System Testing")
    print("=" * 50)
    
    # Run tests
    test_vector_search()
    test_context_builder()
    test_rag_agent()
    
    # Ask for interactive demo
    print("\n" + "=" * 50)
    demo_choice = input("Run interactive demo? (y/n): ").strip().lower()
    if demo_choice in ['y', 'yes']:
        interactive_rag_demo()
    
    print("\n✅ RAG system testing completed!")


if __name__ == "__main__":
    main()
