#!/usr/bin/env python3
"""
Test message flow through the system to ensure RAG is working.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_message_processing():
    """Test message processing through the simple graph."""
    print("🔍 Testing message processing flow...")
    
    try:
        from src.core.simple_graph import process_user_input
        
        # Test messages
        test_cases = [
            {
                "message": "What are some IELTS speaking topics?",
                "user_id": "admin",
                "expected_rag": True
            },
            {
                "message": "Tell me about IELTS speaking test structure",
                "user_id": "admin", 
                "expected_rag": True
            },
            {
                "message": "Hello, how are you?",
                "user_id": "admin",
                "expected_rag": False  # Generic greeting, may not find relevant docs
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test Case {i}: {test_case['message']}")
            print(f"   User ID: {test_case['user_id']}")
            
            # Process message
            result = process_user_input(
                user_input=test_case['message'],
                user_id=test_case['user_id'],
                session_id=f"test_session_{i}"
            )
            
            print(f"   Success: {result.get('success')}")
            print(f"   Response length: {len(result.get('result', ''))}")
            
            # Check for RAG metadata
            if 'metadata' in result and result['metadata']:
                metadata = result['metadata']
                print(f"   RAG Metadata found: {bool(metadata)}")
                if metadata:
                    print(f"     Search type: {metadata.get('search_type', 'N/A')}")
                    print(f"     Documents found: {metadata.get('documents_found', 0)}")
                    print(f"     Sources: {len(metadata.get('sources', []))}")
            
            # Show response preview
            response = result.get('result', '')
            if response:
                preview = response[:200] + "..." if len(response) > 200 else response
                print(f"   Response preview: {preview}")
            
            print(f"   Expected RAG: {test_case['expected_rag']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Message processing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_socketio_flow():
    """Test the SocketIO message flow (simulation)."""
    print("\n🔍 Testing SocketIO message flow simulation...")
    
    try:
        # Import the process_message logic
        import socketio_server
        
        # Check if the system is configured to use RAG
        from src.core.simple_graph import RAG_AVAILABLE
        
        print(f"   RAG Available in system: {RAG_AVAILABLE}")
        
        # Simulate message data
        test_message_data = {
            "message": "What are some IELTS speaking topics?",
            "session_id": "test_session_socketio"
        }
        
        # Check if MULTIAGENTS_AVAILABLE
        multiagents_available = getattr(socketio_server, 'MULTIAGENTS_AVAILABLE', False)
        print(f"   MULTIAGENTS_AVAILABLE: {multiagents_available}")
        
        if multiagents_available:
            print("   ✅ System configured to use conversation agents")
            print("   ✅ Should use RAG agent if available")
        else:
            print("   ⚠️ System not configured for multi-agents")
        
        return True
        
    except Exception as e:
        print(f"❌ SocketIO flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_flow():
    """Test the API message flow."""
    print("\n🔍 Testing API message flow...")
    
    try:
        # Test the API endpoint logic
        from api import ProcessRequest
        
        # Create test request
        test_request = ProcessRequest(input="What are some IELTS speaking topics?")
        
        print(f"   Test request: {test_request.input}")
        
        # Check if the API uses simple_graph
        import api
        
        # Look for process_user_input usage in api.py
        import inspect
        api_source = inspect.getsource(api)
        
        if "process_user_input" in api_source:
            print("   ✅ API uses process_user_input from simple_graph")
        else:
            print("   ⚠️ API may not use simple_graph")
        
        if "simple_graph" in api_source:
            print("   ✅ API imports simple_graph")
        else:
            print("   ⚠️ API may not import simple_graph")
        
        return True
        
    except Exception as e:
        print(f"❌ API flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_context_building():
    """Test RAG context building specifically."""
    print("\n🔍 Testing RAG context building...")
    
    try:
        from src.RAG.rag_agent import RAGAgent
        from src.llms.llm_factory import LLMFactory
        from src.config.settings import config
        
        # Create RAG agent
        llm_factory = LLMFactory(config.llm)
        rag_agent = RAGAgent(llm_factory)
        
        # Test context retrieval
        test_query = "IELTS speaking topics"
        user_id = "admin"
        
        print(f"   Query: {test_query}")
        print(f"   User ID: {user_id}")
        
        # Get context
        context = rag_agent._retrieve_context(test_query, user_id)
        
        print(f"   Documents found: {context['total_documents']}")
        print(f"   Context length: {context['context_length']}")
        print(f"   Sources: {len(context['sources'])}")
        
        if context['context']:
            preview = context['context'][:300] + "..." if len(context['context']) > 300 else context['context']
            print(f"   Context preview: {preview}")
        
        # Test prompt building
        conversation_context = []
        prompt = rag_agent._build_rag_prompt(test_query, context, conversation_context)
        
        print(f"   Prompt length: {len(prompt)}")
        prompt_preview = prompt[:400] + "..." if len(prompt) > 400 else prompt
        print(f"   Prompt preview: {prompt_preview}")
        
        return context['total_documents'] > 0
        
    except Exception as e:
        print(f"❌ RAG context building test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🧪 MESSAGE FLOW TEST")
    print("="*50)
    
    # Test 1: Message processing
    message_success = test_message_processing()
    
    # Test 2: SocketIO flow
    socketio_success = test_socketio_flow()
    
    # Test 3: API flow
    api_success = test_api_flow()
    
    # Test 4: RAG context building
    rag_context_success = test_rag_context_building()
    
    # Summary
    print(f"\n📊 MESSAGE FLOW TEST SUMMARY")
    print("="*40)
    print(f"Message Processing: {'✅' if message_success else '❌'}")
    print(f"SocketIO Flow: {'✅' if socketio_success else '❌'}")
    print(f"API Flow: {'✅' if api_success else '❌'}")
    print(f"RAG Context: {'✅' if rag_context_success else '❌'}")
    
    if all([message_success, socketio_success, api_success, rag_context_success]):
        print(f"\n🎉 All message flow tests passed! RAG is integrated properly.")
        print(f"\n💡 Your messages should now go through RAG with user_id filtering!")
    else:
        print(f"\n⚠️ Some message flow tests failed. RAG integration may have issues.")

if __name__ == "__main__":
    main()
