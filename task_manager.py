from typing import Dict, Any, List, Optional

class Task:
    def __init__(self, name: str, required_slots: List[str], optional_slots: List[str] = None):
        self.name = name
        self.required_slots = required_slots if required_slots is not None else []
        self.optional_slots = optional_slots if optional_slots is not None else []
        self.filled_slots: Dict[str, Any] = {}
        self.is_active: bool = False

    def start(self):
        self.is_active = True

    def end(self):
        self.is_active = False
        self.filled_slots = {}

    def fill_slot(self, slot_name: str, value: Any):
        if slot_name in self.required_slots or slot_name in self.optional_slots:
            self.filled_slots[slot_name] = value
        else:
            raise ValueError(f"Slot '{slot_name}' is not defined for task '{self.name}'")

    def get_next_missing_slot(self) -> Optional[str]:
        for slot in self.required_slots:
            if slot not in self.filled_slots:
                return slot
        return None

    def is_complete(self) -> bool:
        return all(slot in self.filled_slots for slot in self.required_slots)

class TaskManager:
    def __init__(self):
        self.active_task: Optional[Task] = None
        self.task_definitions: Dict[str, Task] = {}

    def register_task(self, task: Task):
        self.task_definitions[task.name] = task

    def start_task(self, task_name: str, required_slots: List[str], optional_slots: List[str] = None):
        if task_name not in self.task_definitions:
            task = Task(task_name, required_slots, optional_slots)
            self.register_task(task)
        else:
            task = self.task_definitions[task_name]
            task.filled_slots = {} # Reset slots for a new start
        task.start()
        self.active_task = task

    def end_active_task(self):
        if self.active_task:
            self.active_task.end()
            self.active_task = None

    def get_active_task(self) -> Optional[Task]:
        return self.active_task

    def is_task_active(self) -> bool:
        return self.active_task is not None and self.active_task.is_active
