import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DialogueStateTrackerTool(BaseTool):
    """
    A tool for simulating dialogue state tracking, maintaining context and
    understanding user intent across multi-turn conversations.
    """

    def __init__(self, tool_name: str = "dialogue_state_tracker"):
        super().__init__(tool_name)
        self.states_file = "dialogue_states.json"
        self.conversations: Dict[str, Dict[str, Any]] = self._load_states()

    @property
    def description(self) -> str:
        return "Simulates dialogue state tracking: starts conversations, processes utterances, and manages conversation context."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The dialogue state tracking operation to perform.",
                    "enum": ["start_conversation", "process_utterance", "get_conversation_state", "list_conversations"]
                },
                "conversation_id": {"type": "string"},
                "initial_utterance": {"type": "string"},
                "utterance": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_states(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.states_file):
            with open(self.states_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted states file '{self.states_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_states(self) -> None:
        with open(self.states_file, 'w') as f:
            json.dump(self.conversations, f, indent=4)

    def _start_conversation(self, conversation_id: str, initial_utterance: str) -> Dict[str, Any]:
        if not all([conversation_id, initial_utterance]):
            raise ValueError("Conversation ID and initial utterance cannot be empty.")
        if conversation_id in self.conversations:
            raise ValueError(f"Conversation '{conversation_id}' already exists.")

        initial_state = {
            "conversation_id": conversation_id, "status": "active",
            "started_at": datetime.now().isoformat(), "last_updated_at": datetime.now().isoformat(),
            "history": [{"speaker": "user", "utterance": initial_utterance, "timestamp": datetime.now().isoformat()}],
            "current_intent": "greet", "extracted_entities": {}, "context": {}
        }
        self.conversations[conversation_id] = initial_state
        self._save_states()
        return initial_state

    def _process_utterance(self, conversation_id: str, utterance: str) -> Dict[str, Any]:
        conversation = self.conversations.get(conversation_id)
        if not conversation: raise ValueError(f"Conversation '{conversation_id}' not found.")
        if not utterance: raise ValueError("Utterance cannot be empty.")

        conversation["history"].append({"speaker": "user", "utterance": utterance, "timestamp": datetime.now().isoformat()})
        conversation["last_updated_at"] = datetime.now().isoformat()

        simulated_intent = "unknown"
        simulated_entities = {}

        if "hello" in utterance.lower() or "hi" in utterance.lower(): simulated_intent = "greet"
        elif "order" in utterance.lower():
            simulated_intent = "place_order"
            if "pizza" in utterance.lower(): simulated_entities["item"] = "pizza"
            if "large" in utterance.lower(): simulated_entities["size"] = "large"
        elif "status" in utterance.lower():
            simulated_intent = "check_status"
            if "order" in utterance.lower(): simulated_entities["item_type"] = "order"
        
        conversation["current_intent"] = simulated_intent
        conversation["extracted_entities"].update(simulated_entities)
        conversation["context"]["last_intent"] = simulated_intent

        self._save_states()
        return conversation

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "start_conversation":
            return self._start_conversation(kwargs.get("conversation_id"), kwargs.get("initial_utterance"))
        elif operation == "process_utterance":
            return self._process_utterance(kwargs.get("conversation_id"), kwargs.get("utterance"))
        elif operation == "get_conversation_state":
            return self.conversations.get(kwargs.get("conversation_id"))
        elif operation == "list_conversations":
            summaries = []
            for conv_id, conv_data in self.conversations.items():
                summary = {
                    "conversation_id": conv_id, "status": conv_data["status"],
                    "started_at": conv_data["started_at"], "last_updated_at": conv_data["last_updated_at"],
                    "current_intent": conv_data["current_intent"], "history_length": len(conv_data["history"])
                }
                summaries.append(summary)
            return summaries
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DialogueStateTrackerTool functionality...")
    tool = DialogueStateTrackerTool()
    
    try:
        print("\n--- Starting Conversation ---")
        tool.execute(operation="start_conversation", conversation_id="conv_001", initial_utterance="Hello, I'd like to order a large pizza.")
        
        print("\n--- Processing Utterance ---")
        tool.execute(operation="process_utterance", conversation_id="conv_001", utterance="What's the status of my order?")

        print("\n--- Getting Conversation State ---")
        state = tool.execute(operation="get_conversation_state", conversation_id="conv_001")
        print(json.dumps(state, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.states_file): os.remove(tool.states_file)
        print("\nCleanup complete.")
