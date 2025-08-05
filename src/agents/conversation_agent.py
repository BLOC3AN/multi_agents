"""
Single conversation agent that handles all types of user requests.
This agent replaces the multi-agent system with a unified approach.
"""
from src.core.base_agent import BaseAgent
from src.core.types import AgentState
from src.llms.llm_factory import LLMFactory


class ConversationAgent(BaseAgent):
    """Unified agent that handles all types of conversations and requests."""

    def get_agent_name(self) -> str:
        """Return the name of this agent."""
        return "ConversationAgent"

    def get_prompt(self, user_input: str, context: list = None) -> str:
        """Generate an intelligent prompt that can handle all types of requests."""
        
        # Base system prompt that combines all capabilities
        prompt = """Bạn là một AI assistant thông minh và hữu ích. Bạn có thể:

🧮 **Giải toán**: Giải các bài toán, phương trình, tính toán số học một cách chi tiết
📚 **Giải thích khái niệm**: Trả lời câu hỏi, giải thích khái niệm, cung cấp thông tin hữu ích
🎭 **Sáng tác văn học**: Viết thơ, truyện, sáng tác văn học sáng tạo

Hãy phân tích yêu cầu của người dùng và đưa ra câu trả lời phù hợp nhất. 
Nếu là bài toán, hãy giải chi tiết từng bước.
Nếu cần giải thích, hãy trình bày rõ ràng và dễ hiểu.
Nếu là yêu cầu sáng tác, hãy tạo ra nội dung hay và ý nghĩa.

"""

        # Add conversation context if available
        if context and len(context) > 0:
            prompt += "\n**Ngữ cảnh cuộc trò chuyện trước đó:**\n"
            for msg in context[-3:]:  # Use last 3 messages for context
                if msg.get("user_input"):
                    prompt += f"👤 Người dùng: {msg['user_input']}\n"
                if msg.get("agent_response"):
                    # Truncate long responses for context
                    response = msg['agent_response']
                    if len(response) > 200:
                        response = response[:200] + "..."
                    prompt += f"🤖 Trợ lý: {response}\n"
            prompt += "\n"

        # Add current user input
        prompt += f"**Yêu cầu hiện tại:**\n👤 Người dùng: {user_input}\n\n"
        prompt += "🤖 Trợ lý: "

        return prompt

    def _detect_request_type(self, user_input: str) -> str:
        """
        Simple heuristic to detect request type for internal use.
        This is just for logging/debugging purposes.
        """
        text_lower = user_input.lower()
        
        # Math keywords
        math_keywords = ["solve", "equation", "calculate", "math", "=", "+", "-", "*", "/", 
                        "x +", "x -", "2x", "phương trình", "giải", "tính", "toán"]
        if any(keyword in text_lower for keyword in math_keywords):
            return "math"
        
        # Poem keywords  
        poem_keywords = ["poem", "poetry", "verse", "thơ", "bài thơ", "viết thơ", 
                        "write a poem", "compose", "sáng tác"]
        if any(keyword in text_lower for keyword in poem_keywords):
            return "poem"
        
        # Default to general conversation
        return "general"

    def process(self, state: AgentState) -> AgentState:
        """
        Process the input and update the state.
        Enhanced version that includes request type detection for metadata.
        """
        try:
            user_input = state["input"]
            context = state.get("conversation_context", [])
            
            # Detect request type for metadata (optional)
            request_type = self._detect_request_type(user_input)
            
            # Generate prompt and get LLM response
            prompt = self.get_prompt(user_input, context)
            from langchain.schema import HumanMessage
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Update state with results
            state["final_result"] = response.content
            state["errors"] = None
            
            # Add metadata about the request type
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["detected_request_type"] = request_type
            state["metadata"]["agent_used"] = self.get_agent_name()

        except Exception as e:
            state["final_result"] = None
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Error in {self.get_agent_name()}: {str(e)}")
            
            # Add error metadata
            if "metadata" not in state:
                state["metadata"] = {}
            state["metadata"]["error_occurred"] = True

        return state
