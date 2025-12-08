import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered context-aware responses will not be available.")

logger = logging.getLogger(__name__)

USER_CONTEXT_FILE = Path("user_context.json")
USER_INTERACTION_HISTORY_FILE = Path("user_interaction_history.json")

class ContextManager:
    """Manages user context and preferences, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = USER_CONTEXT_FILE):
        if cls._instance is None:
            cls._instance = super(ContextManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.contexts: Dict[str, Any] = cls._instance._load_contexts()
        return cls._instance

    def _load_contexts(self) -> Dict[str, Any]:
        """Loads user contexts from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty contexts.")
                return {}
            except Exception as e:
                logger.error(f"Error loading contexts from {self.file_path}: {e}")
                return {}
        return {}

    def _save_contexts(self) -> None:
        """Saves user contexts to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.contexts, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving contexts to {self.file_path}: {e}")

    def get_context(self, user_id: str) -> Dict[str, Any]:
        # Simulate dynamic context like time of day
        context = self.contexts.get(user_id, {"location": "unknown", "preferences": {}})
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12: context["time_of_day"] = "morning"
        elif 12 <= current_hour < 18: context["time_of_day"] = "afternoon"
        else: context["time_of_day"] = "evening"
        return context

    def set_context(self, user_id: str, location: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None) -> bool:
        if user_id not in self.contexts:
            self.contexts[user_id] = {"location": "unknown", "preferences": {}}
        
        if location is not None: self.contexts[user_id]["location"] = location
        if preferences is not None: self.contexts[user_id]["preferences"].update(preferences)
        
        self._save_contexts()
        return True

context_manager = ContextManager()

class UserInteractionHistoryManager:
    """Manages user interaction history, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = USER_INTERACTION_HISTORY_FILE):
        if cls._instance is None:
            cls._instance = super(UserInteractionHistoryManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.history: Dict[str, List[Dict[str, Any]]] = cls._instance._load_history()
        return cls._instance

    def _load_history(self) -> Dict[str, List[Dict[str, Any]]]:
        """Loads history from a JSON file."""
        if self.file_path.exists():
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
        """Saves history to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving history to {self.file_path}: {e}")

    def record_interaction(self, user_id: str, action: str, query: str, response: str, context: Dict[str, Any]):
        if user_id not in self.history:
            self.history[user_id] = []
        self.history[user_id].append({
            "action": action,
            "query": query,
            "response": response,
            "context": context,
            "timestamp": datetime.now().isoformat() + "Z"
        })
        self._save_history()

user_interaction_history_manager = UserInteractionHistoryManager()

class LLMContextAssistant:
    """Manages the text generation model for context-aware responses, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMContextAssistant, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for context-aware responses are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for context-aware responses...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if self._generator is None:
            return json.dumps({"error": "Text generation model not available. Check logs for loading errors."})
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return json.dumps({"error": f"Text generation failed: {e}"})

llm_context_assistant_instance = LLMContextAssistant()

class GetContextTool(BaseTool):
    """Retrieves the current context for a user."""
    def __init__(self, tool_name="get_context"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current context for a user, including simulated location, time of day, and preferences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "The ID of the user to retrieve context for."}},
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        context = context_manager.get_context(user_id)
        return json.dumps({"user_id": user_id, "context": context}, indent=2)

class SetContextTool(BaseTool):
    """Sets the context for a user."""
    def __init__(self, tool_name="set_context"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Sets the context for a user, including location and preferences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user to set context for."},
                "location": {"type": "string", "description": "Optional: The user's current location (e.g., 'New York', 'home').", "default": None},
                "preferences": {"type": "object", "description": "Optional: A dictionary of user preferences (e.g., {'interests': ['music', 'tech']}).", "default": None}
            },
            "required": ["user_id"]
        }

    def execute(self, user_id: str, location: Optional[str] = None, preferences: Optional[Dict[str, Any]] = None, **kwargs: Any) -> str:
        success = context_manager.set_context(user_id, location, preferences)
        if success:
            report = {"message": f"Context for user '{user_id}' updated successfully."}
        else:
            report = {"error": f"Failed to update context for user '{user_id}'. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class ContextAwareResponseTool(BaseTool):
    """Generates a context-aware response to a user query using an AI model."""
    def __init__(self, tool_name="context_aware_response"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a response to a user query that is tailored based on the current context (e.g., location, time, user preferences) using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user."},
                "user_query": {"type": "string", "description": "The user's query or message."}
            },
            "required": ["user_id", "user_query"]
        }

    def execute(self, user_id: str, user_query: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library for AI-powered responses."})

        current_context = context_manager.get_context(user_id)
        
        prompt = f"Generate a context-aware response to the user's query. Consider the following context:\n\nUser ID: {user_id}\nContext: {json.dumps(current_context)}\n\nUser Query: {user_query}\n\nContext-Aware Response:"
        
        generated_response = llm_context_assistant_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)

        user_interaction_history_manager.record_interaction(user_id, "response_generated", user_query, generated_response, current_context)

        return json.dumps({"user_id": user_id, "query": user_query, "response": generated_response, "context_used": current_context}, indent=2)