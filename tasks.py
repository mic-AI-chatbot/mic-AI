from typing import List, Dict, Any

class TaskDefinition:
    """
    Defines a task with its required and optional slots.
    """
    def __init__(self, name: str, required_slots: List[str], optional_slots: List[str] = []):
        self.name = name
        self.required_slots = required_slots
        self.optional_slots = optional_slots

# A registry of all available tasks
TASK_REGISTRY: Dict[str, TaskDefinition] = {
    "send_email": TaskDefinition(
        name="send_email",
        required_slots=["recipient", "subject", "body"],
        optional_slots=["attachment_path"]
    ),
    # ... (other tasks can be defined here) ...
}