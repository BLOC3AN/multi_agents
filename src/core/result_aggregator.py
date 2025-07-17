"""
Result aggregator for combining outputs from multiple agents.
"""
from typing import Dict, List, Optional
from langchain.schema import HumanMessage

from src.core.types import AgentState, AgentResult, IntentScore
from src.llms.llm_factory import LLMFactory


class ResultAggregator:
    """Aggregates and formats results from multiple agents."""
    
    def __init__(self, llm_factory: LLMFactory):
        """Initialize the aggregator."""
        self.llm_factory = llm_factory
        self._llm = None
    
    @property
    def llm(self):
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = self.llm_factory.create_llm()
        return self._llm
    
    def _format_single_result(self, result: AgentResult) -> str:
        """Format a single agent result."""
        if not result.success:
            return f"❌ **{result.agent_name}** ({result.intent}): {result.error}"
        
        return f"✅ **{result.agent_name}** ({result.intent}):\n{result.result}"
    
    def _create_simple_aggregation(self, results: Dict[str, AgentResult]) -> str:
        """Create a simple concatenation of results."""
        if not results:
            return "Không có kết quả nào được tạo ra."
        
        if len(results) == 1:
            # Single result
            result = list(results.values())[0]
            return result.result if result.success else f"Lỗi: {result.error}"
        
        # Multiple results
        formatted_results = []
        for intent, result in results.items():
            formatted_results.append(self._format_single_result(result))
        
        return "\n\n---\n\n".join(formatted_results)
    
    def _create_intelligent_aggregation(self, state: AgentState) -> str:
        """Use LLM to intelligently combine multiple results."""
        results = state.get("agent_results", {})
        user_input = state.get("input", "")
        
        if not results:
            return "Không có kết quả nào để tổng hợp."
        
        if len(results) == 1:
            # Single result, no need for aggregation
            result = list(results.values())[0]
            return result.result if result.success else f"Lỗi: {result.error}"
        
        # Prepare context for LLM
        results_context = []
        for intent, result in results.items():
            if result.success:
                results_context.append(f"**{intent.upper()} Agent Result:**\n{result.result}")
            else:
                results_context.append(f"**{intent.upper()} Agent Error:**\n{result.error}")
        
        context = "\n\n".join(results_context)
        
        prompt = f"""Bạn là một AI assistant chuyên tổng hợp kết quả từ nhiều agents khác nhau.

Câu hỏi gốc của người dùng: "{user_input}"

Kết quả từ các agents:
{context}

Hãy tổng hợp các kết quả trên thành một câu trả lời hoàn chỉnh, mạch lạc và hữu ích cho người dùng. 

Yêu cầu:
1. Ưu tiên kết quả từ agent phù hợp nhất với câu hỏi
2. Kết hợp thông tin từ các agents khác nếu có liên quan
3. Loại bỏ thông tin trùng lặp hoặc không cần thiết
4. Trình bày theo cách dễ hiểu và logic
5. Nếu có lỗi từ một số agents, chỉ sử dụng kết quả thành công

Câu trả lời tổng hợp:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content.strip()
        except Exception as e:
            # Fallback to simple aggregation if LLM fails
            print(f"Intelligent aggregation failed: {e}, falling back to simple aggregation")
            return self._create_simple_aggregation(results)
    
    def _create_execution_summary(self, state: AgentState) -> str:
        """Create a summary of the execution process."""
        summary = state.get("execution_summary", {})
        processing_mode = state.get("processing_mode", "single")
        
        if not summary:
            return ""
        
        total_agents = summary.get("total_agents", 0)
        successful_agents = summary.get("successful_agents", 0)
        failed_agents = summary.get("failed_agents", 0)
        execution_time = summary.get("total_execution_time", 0)
        intents = summary.get("intents_processed", [])
        
        summary_parts = []
        
        if processing_mode == "parallel":
            summary_parts.append(f"🔄 **Xử lý song song**: {total_agents} agents")
        else:
            summary_parts.append(f"🔄 **Xử lý tuần tự**: {total_agents} agent")
        
        summary_parts.append(f"✅ Thành công: {successful_agents}")
        if failed_agents > 0:
            summary_parts.append(f"❌ Thất bại: {failed_agents}")
        
        summary_parts.append(f"⏱️ Thời gian: {execution_time:.2f}s")
        summary_parts.append(f"🎯 Intents: {', '.join(intents)}")
        
        return " | ".join(summary_parts)
    
    def aggregate_results(self, state: AgentState, use_intelligent_aggregation: bool = True) -> AgentState:
        """
        Aggregate results from multiple agents into final result.
        
        Args:
            state: Current agent state with results
            use_intelligent_aggregation: Whether to use LLM for intelligent aggregation
            
        Returns:
            Updated state with final aggregated result
        """
        results = state.get("agent_results", {})
        
        if not results:
            state["final_result"] = "Không có kết quả nào được tạo ra."
            return state
        
        try:
            if use_intelligent_aggregation and len(results) > 1:
                # Use LLM for intelligent aggregation
                final_result = self._create_intelligent_aggregation(state)
            else:
                # Use simple aggregation
                final_result = self._create_simple_aggregation(results)
            
            # Add execution summary if in debug mode or multiple agents
            processing_mode = state.get("processing_mode", "single")
            if processing_mode == "parallel" or len(results) > 1:
                execution_summary = self._create_execution_summary(state)
                if execution_summary:
                    final_result = f"{final_result}\n\n---\n\n📊 **Thông tin xử lý**: {execution_summary}"
            
            state["final_result"] = final_result
            
        except Exception as e:
            # Fallback to simple aggregation
            state["final_result"] = self._create_simple_aggregation(results)
            errors = state.get("errors", [])
            errors.append(f"Result aggregation error: {str(e)}")
            state["errors"] = errors
        
        return state
    
    def get_best_result(self, results: Dict[str, AgentResult]) -> Optional[AgentResult]:
        """
        Get the best result based on success and confidence.
        
        Args:
            results: Dictionary of agent results
            
        Returns:
            The best result or None if no successful results
        """
        if not results:
            return None
        
        # Filter successful results
        successful_results = [r for r in results.values() if r.success]
        
        if not successful_results:
            return None
        
        # If only one successful result, return it
        if len(successful_results) == 1:
            return successful_results[0]
        
        # For multiple successful results, prefer based on intent priority
        # Math > Poem > English (can be customized)
        intent_priority = {"math": 3, "poem": 2, "english": 1}
        
        best_result = max(
            successful_results,
            key=lambda r: intent_priority.get(r.intent, 0)
        )
        
        return best_result
