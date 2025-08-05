"""
RAG Agent for Retrieval-Augmented Generation.

Main agent that combines vector search with LLM generation:
- Inherits from BaseAgent for consistency
- Performs vector/hybrid search for relevant documents
- Builds context from search results
- Generates responses using LLM with retrieved context
- Maintains user isolation and error handling
"""

from typing import List, Dict, Any, Optional
from src.core.base_agent import BaseAgent
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory
from .vector_search import VectorSearchService
from .context_builder import ContextBuilder


class RAGAgent(BaseAgent):
    """RAG Agent that combines retrieval and generation."""
    
    def __init__(self, 
                 llm_factory: LLMFactory,
                 search_type: str = "hybrid",
                 max_context_length: int = 4000,
                 max_search_results: int = 10):
        """
        Initialize RAG agent.
        
        Args:
            llm_factory: LLM factory for creating LLM instances
            search_type: Type of search ("dense", "sparse", "hybrid")
            max_context_length: Maximum context length for LLM
            max_search_results: Maximum number of search results
        """
        super().__init__(llm_factory)
        
        self.search_type = search_type
        self.max_search_results = max_search_results
        
        # Initialize RAG components
        try:
            # Get embedding provider from file embedding service
            from src.services.file_embedding_service import get_file_embedding_service
            embedding_service = get_file_embedding_service()

            # Initialize search service with proper embedding provider
            self.search_service = VectorSearchService(embedding_service.embedding_provider)
            self.context_builder = ContextBuilder(max_context_length=max_context_length)
            self.rag_available = True
            print("✅ RAG Agent initialized successfully")
        except Exception as e:
            print(f"⚠️ RAG components not available: {e}")
            self.search_service = None
            self.context_builder = None
            self.rag_available = False
    
    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        return "RAGAgent"
    
    def get_prompt(self, user_input: str, context: list = None) -> str:
        """
        Generate prompt with RAG context.
        This method is called by BaseAgent.process()
        
        Args:
            user_input: User query
            context: Conversation context (not used for RAG context)
            
        Returns:
            Prompt with retrieved context
        """
        # If RAG not available, use simple prompt
        if not self.rag_available:
            return self._get_fallback_prompt(user_input, context)
        
        # Get user_id from state (will be set by process method)
        user_id = getattr(self, '_current_user_id', 'default_user')
        
        # Perform RAG retrieval
        rag_context = self._retrieve_context(user_input, user_id)
        
        # Build prompt with context
        return self._build_rag_prompt(user_input, rag_context, context)
    
    def _retrieve_context(self, query: str, user_id: str) -> Dict[str, Any]:
        """
        Retrieve relevant context for the query.
        
        Args:
            query: User query
            user_id: User ID for isolation
            
        Returns:
            Context data with documents and metadata
        """
        try:
            # Perform vector search
            search_results = self.search_service.search(
                query=query,
                user_id=user_id,
                search_type=self.search_type,
                limit=self.max_search_results
            )
            
            # Build context from results
            context_data = self.context_builder.build_context(search_results, query)
            
            print(f"📚 Retrieved {context_data['total_documents']} documents for query")
            return context_data
            
        except Exception as e:
            print(f"❌ Context retrieval failed: {e}")
            return {
                "context": "",
                "documents": [],
                "sources": [],
                "total_documents": 0,
                "context_length": 0
            }
    
    def _build_rag_prompt(self, 
                         user_input: str, 
                         rag_context: Dict[str, Any],
                         conversation_context: list = None) -> str:
        """
        Build prompt with RAG context.
        
        Args:
            user_input: User query
            rag_context: Retrieved context data
            conversation_context: Previous conversation
            
        Returns:
            Complete prompt with context
        """
        prompt_parts = []
        
        # System instruction
        prompt_parts.append("""Bạn là một AI assistant thông minh và hữu ích. Bạn có khả năng:

1. **Trả lời dựa trên tài liệu**: Sử dụng thông tin từ tài liệu được cung cấp để đưa ra câu trả lời chính xác và chi tiết
2. **Trích dẫn nguồn**: Luôn đề cập đến nguồn thông tin khi trả lời
3. **Phân tích và tổng hợp**: Kết hợp thông tin từ nhiều tài liệu để đưa ra câu trả lời toàn diện
4. **Thừa nhận giới hạn**: Nếu không tìm thấy thông tin liên quan, hãy thành thật nói rằng bạn không có đủ thông tin

**Nguyên tắc quan trọng:**
- Ưu tiên thông tin từ tài liệu được cung cấp
- Trả lời bằng tiếng Việt trừ khi được yêu cầu khác
- Cung cấp câu trả lời có cấu trúc và dễ hiểu
- Đề cập nguồn tài liệu khi có thể""")
        
        # Add RAG context if available
        if rag_context["context"]:
            prompt_parts.append(f"\n{rag_context['context']}")
        else:
            prompt_parts.append("\nKhông tìm thấy tài liệu liên quan trong cơ sở dữ liệu.")
        
        # Add conversation context if available
        if conversation_context:
            prompt_parts.append("\n--- Lịch sử hội thoại ---")
            for msg in conversation_context[-3:]:  # Last 3 messages
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
        
        # Add current query
        prompt_parts.append(f"\n--- Câu hỏi hiện tại ---")
        prompt_parts.append(f"Người dùng: {user_input}")
        
        # Add instruction for response
        if rag_context["total_documents"] > 0:
            prompt_parts.append(f"\nHãy trả lời câu hỏi dựa trên {rag_context['total_documents']} tài liệu được cung cấp ở trên. Nếu thông tin không đủ để trả lời, hãy nói rõ và đưa ra gợi ý nếu có thể.")
        else:
            prompt_parts.append(f"\nKhông tìm thấy tài liệu liên quan. Hãy trả lời dựa trên kiến thức chung của bạn và thông báo rằng câu trả lời không dựa trên tài liệu cụ thể nào.")
        
        return "\n".join(prompt_parts)
    
    def _get_fallback_prompt(self, user_input: str, context: list = None) -> str:
        """
        Generate fallback prompt when RAG is not available.
        
        Args:
            user_input: User query
            context: Conversation context
            
        Returns:
            Simple prompt without RAG context
        """
        prompt_parts = []
        
        prompt_parts.append("""Bạn là một AI assistant thông minh và hữu ích. 
        
⚠️ Lưu ý: Hệ thống tìm kiếm tài liệu hiện không khả dụng, vì vậy tôi sẽ trả lời dựa trên kiến thức chung.
        
Hãy trả lời câu hỏi một cách hữu ích và chính xác nhất có thể.""")
        
        # Add conversation context if available
        if context:
            prompt_parts.append("\n--- Lịch sử hội thoại ---")
            for msg in context[-3:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt_parts.append(f"{role}: {content}")
        
        prompt_parts.append(f"\nCâu hỏi: {user_input}")
        
        return "\n".join(prompt_parts)
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process the input with RAG capabilities.
        Enhanced version of BaseAgent.process() with RAG context.
        
        Args:
            state: Agent state containing input and metadata
            
        Returns:
            Updated state with RAG response
        """
        try:
            user_input = state["input"]
            user_id = state.get("user_id", "default_user")
            
            # Store user_id for use in get_prompt
            self._current_user_id = user_id
            
            # Get conversation context
            conversation_context = state.get("conversation_context", [])
            
            # Generate prompt (this will trigger RAG retrieval)
            prompt = self.get_prompt(user_input, conversation_context)
            
            # Get LLM response
            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Update state with results
            state["final_result"] = response.content
            state["errors"] = None
            
            # Add RAG metadata if available
            if self.rag_available:
                rag_context = self._retrieve_context(user_input, user_id)
                state["rag_metadata"] = {
                    "search_type": self.search_type,
                    "documents_found": rag_context["total_documents"],
                    "sources": rag_context["sources"],
                    "context_length": rag_context["context_length"]
                }
            
            print(f"✅ RAG Agent processed query successfully")
            
        except Exception as e:
            error_msg = f"Error in {self.get_agent_name()}: {str(e)}"
            state["final_result"] = None
            state["errors"] = [error_msg]
            print(f"❌ {error_msg}")
        
        return state
