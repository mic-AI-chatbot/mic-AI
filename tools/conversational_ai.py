import logging
import json
from typing import Dict, Any, List, Optional
from mic.hf_llm import HfLLM # Import the HfLLM
from tools.base_tool import BaseTool

# Import ConversationManager and ConversationalAITool from conversational_ai_tool.py
try:
    from .conversational_ai_tool import conversation_manager, ConversationalAITool as SpecificConversationalAITool
    CONVERSATIONAL_AI_TOOL_AVAILABLE = True
except ImportError:
    CONVERSATIONAL_AI_TOOL_AVAILABLE = False
    logging.warning("SpecificConversationalAITool from conversational_ai_tool.py not found. General conversational AI will use a simpler, local LLM.")

logger = logging.getLogger(__name__)

class GeneralConversationalAITool(BaseTool):
    """
    A general-purpose AI for conversational queries using a local LLM, leveraging the existing conversational AI tool.
    """

    def __init__(self, tool_name: str = "general_conversational_ai_tool"):
        super().__init__(tool_name)
        if CONVERSATIONAL_AI_TOOL_AVAILABLE:
            self.specific_conversational_ai_tool = SpecificConversationalAITool()
        else:
            self.llm = HfLLM() # Fallback to direct LLM if specific tool not available

    @property
    def description(self) -> str:
        return "A general-purpose conversational AI that can respond to a wide range of queries based on the provided conversation history."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user for whom to generate a response."},
                "user_message": {"type": "string", "description": "The user's message or query."}
            },
            "required": ["user_id", "user_message"]
        }

    def execute(self, user_id: str, user_message: str) -> str:
        if CONVERSATIONAL_AI_TOOL_AVAILABLE:
            # Leverage the existing, more robust conversational AI tool
            return self.specific_conversational_ai_tool.execute(user_id=user_id, user_message=user_message)
        else:
            # Fallback to a simpler LLM interaction if the specific tool is not available
            if self.llm.llm is None:
                return json.dumps({"error": "Local LLM not available. Please ensure it is configured correctly."})

            # Simple history management for fallback (only current message for simplicity)
            input_text = f"user: {user_message}\nassistant: "

            try:
                response = self.llm.generate_response(input_text)
                return json.dumps({"user_id": user_id, "user_message": user_message, "assistant_response": response}, indent=2)
            except Exception as e:
                logger.error(f"An error occurred with the local LLM: {e}", exc_info=True)
                return json.dumps({"error": f"Sorry, an error occurred while processing your request with the AI model: {e}"})
