import logging
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from mic.hf_llm import HfLLM # Import the HfLLM
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CONVERSATION_HISTORY_FILE = "conversation_history.json"

class ConversationManager:
    """Manages conversation history for different users/sessions, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: str = CONVERSATION_HISTORY_FILE):
        if cls._instance is None:
            cls._instance = super(ConversationManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.history: Dict[str, List[Dict[str, str]]] = cls._instance._load_history()
        return cls._instance

    def _load_history(self) -> Dict[str, List[Dict[str, str]]]:
        """Loads conversation history from a JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty history.")
                return {}
            except Exception as e:
                logger.error(f"Error loading history from {self.file_path}: {e}")
                return {}
        return {}

    def _save_history(self) -> None:
        """Saves conversation history to a JSON file."""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving history to {self.file_path}: {e}")

    def add_message(self, user_id: str, role: str, content: str):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({"role": role, "content": content, "timestamp": datetime.now().isoformat() + "Z"})
        self._save_history()

    def get_history(self, user_id: str) -> List[Dict[str, str]]:
        return self.history.get(user_id, [])

    def clear_history(self, user_id: str) -> bool:
        if user_id in self.history:
            del self.history[user_id]
            self._save_history()
            return True
        return False

conversation_manager = ConversationManager()

class ConversationalAITool(BaseTool):
    """Generates conversational AI responses using a local LLM."""
    def __init__(self, tool_name="conversational_ai"):
        super().__init__(tool_name=tool_name)
        self.llm = HfLLM()

    @property
    def description(self) -> str:
        return "Generates a conversational AI response based on a given chat history using a local LLM."

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

    def execute(self, user_id: str, user_message: str, **kwargs: Any) -> str:
        if self.llm.llm is None: # Check if LLM is initialized
            return json.dumps({"error": "Local LLM not available. Please ensure it is configured correctly."})

        conversation_manager.add_message(user_id, "user", user_message)
        history = conversation_manager.get_history(user_id)
        
        input_text = ""
        for message in history:
            input_text += f"{message['role']}: {message['content']}\n"
        input_text += "assistant: "

        try:
            response = self.llm.generate_response(input_text)
            conversation_manager.add_message(user_id, "assistant", response)
            
            return json.dumps({"user_id": user_id, "user_message": user_message, "assistant_response": response}, indent=2)
        except Exception as e:
            logger.error(f"An error occurred with the local LLM: {e}", exc_info=True)
            return json.dumps({"error": f"Sorry, an error occurred while processing your request with the AI model: {e}"})

class GetConversationHistoryTool(BaseTool):
    """Retrieves the conversation history for a user."""
    def __init__(self, tool_name="get_conversation_history"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the conversation history for a specific user or session."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "The ID of the user to retrieve history for."}},
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        history = conversation_manager.get_history(user_id)
        if not history:
            return json.dumps({"message": f"No conversation history found for user '{user_id}'."})
        
        return json.dumps({"user_id": user_id, "history": history}, indent=2)

class ClearConversationHistoryTool(BaseTool):
    """Clears the conversation history for a user."""
    def __init__(self, tool_name="clear_conversation_history"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Clears the conversation history for a specific user or session."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "The ID of the user to clear history for."}},
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        success = conversation_manager.clear_history(user_id)
        if success:
            return json.dumps({"message": f"Conversation history for user '{user_id}' cleared successfully."})
        else:
            return json.dumps({"error": f"No conversation history found for user '{user_id}' to clear."})
