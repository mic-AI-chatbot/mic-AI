from typing import List, Dict, Any, Optional
from mic.models import MODELS, load_model # Import MODELS and load_model

class ConversationManager:
    """
    Manages the state and flow of a conversation.
    """

    def __init__(self, history: List[Dict[str, str]] = None):
        """
        Initializes the ConversationManager.
        """
        self.history: List[Dict[str, str]] = history if history else []
        self.context: Dict[str, Any] = {}
        self.current_task: Optional[Task] = None
        self.user_sentiment: str = 'neutral'
        self.active_model: str = "google/flan-t5-small" # Add active_model

    def set_active_model(self, model_name: str):
        """
        Sets the active model for the conversation.
        """
        if model_name not in MODELS:
            raise ValueError(f"Model '{model_name}' is not supported. Supported models are: {', '.join(MODELS.keys())}")
        try:
            load_model(model_name) # Load the model if not already loaded
            self.active_model = model_name
        except Exception as e:
            raise RuntimeError(f"Error loading model '{model_name}': {e}")

    def get_active_model(self) -> str:
        """
        Returns the active model for the conversation.
        """
        return self.active_model

    def add_message(self, role: str, content: str):
        """
        Adds a message to the conversation history.
        """
        self.history.append({"role": role, "content": content})

    def get_last_user_message(self) -> Optional[str]:
        """
        Gets the last message from the user.
        """
        for message in reversed(self.history):
            if message['role'] == 'user':
                return message['content']
        return None

    def update_context(self, new_context: Dict[str, Any]):
        """
        Updates the conversation context with new entities or information.
        """
        self.context.update(new_context)

    def clear_context(self):
        """
        Clears the conversation context.
        """
        self.context = {}

    def start_task(self, task_name: str, required_slots: List[str], optional_slots: List[str] = []):
        """
        Starts a new multi-turn task.
        """
        self.current_task = Task(task_name, required_slots, optional_slots)

    def is_task_active(self) -> bool:
        """
        Checks if a task is currently active.
        """
        return self.current_task is not None

    def get_current_task(self) -> Optional['Task']:
        """
        Returns the current active task.
        """
        return self.current_task

    def end_task(self):
        """
        Ends the current task.
        """
        self.current_task = None


class Task:
    """
    Represents a multi-turn task that requires filling slots.
    """

    def __init__(self, name: str, required_slots: List[str], optional_slots: List[str] = []):
        """
        Initializes a Task.

        Args:
            name: The name of the task (e.g., 'book_meeting').
            required_slots: A list of slot names that need to be filled.
            optional_slots: A list of optional slot names.
        """
        self.name = name
        self.required_slots = required_slots
        self.optional_slots = optional_slots
        self.filled_slots: Dict[str, Any] = {}

    def fill_slot(self, slot_name: str, value: Any):
        """
        Fills a slot with a value.
        """
        if slot_name in self.required_slots or slot_name in self.optional_slots:
            self.filled_slots[slot_name] = value
        else:
            raise ValueError(f"Slot '{slot_name}' is not a valid slot for this task.")

    def get_next_missing_slot(self) -> Optional[str]:
        """
        Returns the name of the next required slot that needs to be filled.
        """
        for slot in self.required_slots:
            if slot not in self.filled_slots:
                return slot
        return None

    def is_complete(self) -> bool:
        """
        Checks if all required slots have been filled.
        """
        return all(slot in self.filled_slots for slot in self.required_slots)