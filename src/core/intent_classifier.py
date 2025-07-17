"""
Intent classification logic for routing user input to appropriate agents.
Enhanced to support multi-intent detection with confidence scores.
"""
import json
import re
from typing import Dict, List, Callable
from langchain.schema import HumanMessage

from src.core.types import AgentState, IntentType, IntentScore
from src.llms.llm_factory import LLMFactory


class IntentClassifier:
    """LLM-powered intent classifier."""

    def __init__(self, llm_factory: LLMFactory):
        """Initialize the classifier with LLM factory."""
        self.llm_factory = llm_factory
        self._llm = None
        self.default_intent: IntentType = "english"
    
    @property
    def llm(self):
        """Lazy-load the LLM instance."""
        if self._llm is None:
            self._llm = self.llm_factory.create_llm()
        return self._llm

    def get_single_classification_prompt(self, text: str) -> str:
        """Generate prompt for single intent classification (backward compatibility)."""
        return f"""Bạn là một AI classifier chuyên phân loại ý định của người dùng.

Hãy phân tích input sau và xác định ý định chính:

Input: "{text}"

Các loại ý định có thể:
1. "math" - Các câu hỏi về toán học, giải phương trình, tính toán số học
2. "poem" - Yêu cầu viết thơ, sáng tác văn học, tạo ra các tác phẩm nghệ thuật bằng lời
3. "english" - Giải thích khái niệm, trả lời câu hỏi thông thường, dịch thuật, mô tả

Hãy trả về CHÍNH XÁC một trong ba từ: "math", "poem", hoặc "english"

Trả lời:"""

    def get_multi_classification_prompt(self, text: str) -> str:
        """Generate prompt for multi-intent classification with confidence scores."""
        return f"""Phân tích input sau và xác định TẤT CẢ các ý định có thể có:

Input: "{text}"

Các loại ý định:
- "math": toán học, phương trình, tính toán
- "poem": viết thơ, sáng tác văn học
- "english": giải thích, mô tả khái niệm

QUAN TRỌNG: Trả về CHÍNH XÁC theo format JSON này:
{{"intents":[{{"intent":"math","confidence":0.8,"reasoning":"có phương trình"}},{{"intent":"english","confidence":0.6,"reasoning":"cần giải thích"}}],"primary_intent":"math"}}

Ví dụ:
- "Giải 2x+3=7" → {{"intents":[{{"intent":"math","confidence":0.9,"reasoning":"phương trình toán"}}],"primary_intent":"math"}}
- "Explain AI and solve 2x+5=11" → {{"intents":[{{"intent":"english","confidence":0.8,"reasoning":"explain AI"}},{{"intent":"math","confidence":0.8,"reasoning":"solve equation"}}],"primary_intent":"english"}}

JSON:"""

    def classify(self, text: str) -> IntentType:
        """
        Classify single intent using LLM (backward compatibility).

        Args:
            text: Input text to classify

        Returns:
            The classified intent type
        """
        try:
            prompt = self.get_single_classification_prompt(text)
            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Extract intent from response
            result = response.content.strip().lower()

            # Validate the response
            if result in ["math", "poem", "english"]:
                return result
            else:
                # If response is not valid, try to extract from the text
                if "math" in result:
                    return "math"
                elif "poem" in result:
                    return "poem"
                elif "english" in result:
                    return "english"
                else:
                    return self.default_intent

        except Exception as e:
            # Fallback to default intent if LLM fails
            print(f"Intent classification error: {e}")
            return self.default_intent

    def classify_multi_intent(self, text: str, confidence_threshold: float = 0.2) -> List[IntentScore]:
        """
        Classify multiple intents with confidence scores.

        Args:
            text: Input text to classify
            confidence_threshold: Minimum confidence to include intent

        Returns:
            List of intents with confidence scores
        """
        try:
            prompt = self.get_multi_classification_prompt(text)
            response = self.llm.invoke([HumanMessage(content=prompt)])

            # Try to parse JSON response
            response_text = response.content.strip()

            # Clean up response - sometimes LLM adds extra text
            if "```json" in response_text:
                # Extract JSON from code block
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end]
            elif response_text.startswith("JSON:"):
                response_text = response_text[5:].strip()

            try:
                result = json.loads(response_text)

                intents = []
                for intent_data in result.get("intents", []):
                    if intent_data.get("confidence", 0) >= confidence_threshold:
                        intents.append(IntentScore(
                            intent=intent_data["intent"],
                            confidence=intent_data["confidence"],
                            reasoning=intent_data.get("reasoning")
                        ))

                # Sort by confidence descending
                intents.sort(key=lambda x: x.confidence, reverse=True)
                return intents

            except (json.JSONDecodeError, KeyError) as e:
                # Try to extract intents manually from response
                print(f"JSON parsing failed: {e}, trying manual extraction")
                return self._extract_intents_manually(text, response_text, confidence_threshold)

        except Exception as e:
            # Fallback to default intent
            print(f"Multi-intent classification error: {e}")
            return [IntentScore(intent=self.default_intent, confidence=0.5, reasoning="Error fallback")]

    def _extract_intents_manually(self, text: str, response_text: str, confidence_threshold: float) -> List[IntentScore]:
        """Manually extract intents when JSON parsing fails."""
        intents = []
        text_lower = text.lower()

        # Check for math keywords
        math_keywords = ["solve", "equation", "calculate", "math", "=", "+", "-", "*", "/", "x +", "x -", "2x", "phương trình", "giải", "tính"]
        math_score = sum(1 for keyword in math_keywords if keyword in text_lower) * 0.3
        if math_score >= confidence_threshold:
            intents.append(IntentScore(intent="math", confidence=min(math_score, 0.9), reasoning="Math keywords detected"))

        # Check for poem keywords
        poem_keywords = ["poem", "poetry", "verse", "thơ", "bài thơ", "viết thơ", "write a poem", "compose"]
        poem_score = sum(1 for keyword in poem_keywords if keyword in text_lower) * 0.4
        if poem_score >= confidence_threshold:
            intents.append(IntentScore(intent="poem", confidence=min(poem_score, 0.9), reasoning="Poem keywords detected"))

        # Check for english/explanation keywords
        english_keywords = ["explain", "what is", "describe", "how does", "machine learning", "AI", "artificial intelligence", "giải thích"]
        english_score = sum(1 for keyword in english_keywords if keyword in text_lower) * 0.3
        if english_score >= confidence_threshold:
            intents.append(IntentScore(intent="english", confidence=min(english_score, 0.9), reasoning="Explanation keywords detected"))

        # If no intents found, fallback to single classification
        if not intents:
            single_intent = self.classify(text)
            intents.append(IntentScore(intent=single_intent, confidence=0.6, reasoning="Manual fallback"))

        # Sort by confidence
        intents.sort(key=lambda x: x.confidence, reverse=True)
        return intents
    
    def classify_state(self, state: AgentState) -> AgentState:
        """
        Enhanced state classification supporting multi-intent detection.
        """
        try:
            # Perform multi-intent classification
            intents = self.classify_multi_intent(state["input"])

            # Update state with multi-intent results
            state["detected_intents"] = intents
            state["primary_intent"] = intents[0].intent if intents else self.default_intent
            state["processing_mode"] = "parallel" if len(intents) > 1 else "single"

            # Initialize other fields
            if "errors" not in state:
                state["errors"] = []
            if "agent_results" not in state:
                state["agent_results"] = {}

        except Exception as e:
            # Fallback to single intent
            state["detected_intents"] = [IntentScore(intent=self.default_intent, confidence=0.5)]
            state["primary_intent"] = self.default_intent
            state["processing_mode"] = "single"
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Error in intent classification: {str(e)}")

        return state

    def classify_state_legacy(self, state: AgentState) -> AgentState:
        """
        Legacy single-intent classification for backward compatibility.
        """
        try:
            intent = self.classify(state["input"])
            state["primary_intent"] = intent
            state["detected_intents"] = [IntentScore(intent=intent, confidence=0.8)]
            state["processing_mode"] = "single"
        except Exception as e:
            state["primary_intent"] = self.default_intent
            state["detected_intents"] = [IntentScore(intent=self.default_intent, confidence=0.5)]
            state["processing_mode"] = "single"
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"Error in intent classification: {str(e)}")

        return state
