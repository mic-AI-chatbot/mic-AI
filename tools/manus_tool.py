
import logging
import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import re

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ManusTaskManagementTool(BaseTool):
    """
    An intelligent task management tool that suggests assignees, prioritizes tasks,
    and manages a hierarchy of tasks and subtasks.
    """

    def __init__(self, tool_name: str = "ManusTaskTool", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.tasks_file = os.path.join(self.data_dir, "manus_tasks.json")
        self.tasks: Dict[str, Dict[str, Any]] = self._load_data(self.tasks_file, default={})
        self.team = {
            "Alice": {"skills": ["report", "sales", "analysis"]},
            "Bob": {"skills": ["server", "deploy", "database", "backend"]},
            "Charlie": {"skills": ["frontend", "ui", "design"]}
        }

    @property
    def description(self) -> str:
        return "An AI-driven task manager for creating, delegating, and prioritizing tasks."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_task", "add_subtask", "update_status", "suggest_assignee", "prioritize_tasks", "list_tasks"]},
                "task_id": {"type": "string"}, "description": {"type": "string"}, "assignee": {"type": "string"},
                "due_date": {"type": "string", "description": "YYYY-MM-DD"}, "parent_task_id": {"type": "string"},
                "new_status": {"type": "string", "enum": ["open", "in_progress", "completed", "cancelled"]},
                "task_ids_to_prioritize": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_tasks(self):
        with open(self.tasks_file, 'w') as f: json.dump(self.tasks, f, indent=4)

    def create_task(self, task_id: str, description: str, due_date: str, assignee: Optional[str] = None, parent_task_id: Optional[str] = None) -> Dict[str, Any]:
        """Creates a new task, optionally as a subtask of another."""
        if task_id in self.tasks: raise ValueError(f"Task with ID '{task_id}' already exists.")
        if parent_task_id and parent_task_id not in self.tasks: raise ValueError(f"Parent task '{parent_task_id}' not found.")

        new_task = {
            "task_id": task_id, "description": description, "assignee": assignee, "due_date": due_date,
            "status": "open", "subtasks": [], "parent_task_id": parent_task_id,
            "created_at": datetime.now().isoformat()
        }
        self.tasks[task_id] = new_task
        if parent_task_id:
            self.tasks[parent_task_id]["subtasks"].append(task_id)
        
        self._save_tasks()
        return new_task

    def add_subtask(self, parent_task_id: str, task_id: str, description: str, due_date: str, assignee: Optional[str] = None) -> Dict[str, Any]:
        """Adds a subtask to a parent task."""
        return self.create_task(task_id, description, due_date, assignee, parent_task_id)

    def update_status(self, task_id: str, new_status: str) -> Dict[str, Any]:
        """Updates the status of a task."""
        task = self.tasks.get(task_id)
        if not task: raise ValueError(f"Task '{task_id}' not found.")
        task["status"] = new_status
        self._save_tasks()
        return task

    def suggest_assignee(self, description: str) -> List[Dict[str, Any]]:
        """Suggests an assignee based on keywords in the task description."""
        suggestions = []
        for name, details in self.team.items():
            score = sum(1 for skill in details['skills'] if re.search(r'\b' + skill + r'\b', description, re.IGNORECASE))
            if score > 0:
                suggestions.append({"assignee": name, "relevance_score": score})
        return sorted(suggestions, key=lambda x: x['relevance_score'], reverse=True)

    def prioritize_tasks(self, task_ids_to_prioritize: List[str]) -> List[Dict[str, Any]]:
        """Prioritizes a list of tasks based on due date and keywords."""
        tasks_to_sort = [self.tasks[tid] for tid in task_ids_to_prioritize if tid in self.tasks]
        
        def priority_score(task):
            score = 0
            # Due date score (closer is higher)
            days_until_due = (date.fromisoformat(task['due_date']) - date.today()).days
            if days_until_due < 1: score += 100
            elif days_until_due < 7: score += 50
            else: score += max(0, 10 - days_until_due)
            
            # Keyword score
            if re.search(r'urgent|blocker|critical', task['description'], re.IGNORECASE): score += 200
            return score

        return sorted(tasks_to_sort, key=priority_score, reverse=True)

    def list_tasks(self, assignee: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists tasks, with optional filters."""
        filtered = list(self.tasks.values())
        if assignee: filtered = [t for t in filtered if t.get("assignee") == assignee]
        if status: filtered = [t for t in filtered if t.get("status") == status]
        return filtered

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_task": self.create_task, "add_subtask": self.add_subtask, "update_status": self.update_status,
            "suggest_assignee": self.suggest_assignee, "prioritize_tasks": self.prioritize_tasks, "list_tasks": self.list_tasks
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating ManusTaskManagementTool functionality...")
    temp_dir = "temp_manus_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    manus_tool = ManusTaskManagementTool(data_dir=temp_dir)
    
    try:
        # 1. Create tasks
        print("\n--- Creating tasks ---")
        manus_tool.execute(operation="create_task", task_id="T1", description="Fix critical backend server bug", due_date="2025-11-14")
        manus_tool.execute(operation="create_task", task_id="T2", description="Design new UI for dashboard", due_date="2025-11-20")
        manus_tool.execute(operation="create_task", task_id="T3", description="Generate Q3 sales report", due_date="2025-11-30")

        # 2. Use AI to suggest an assignee
        print("\n--- Suggesting assignee for 'Fix critical backend server bug' ---")
        suggestions = manus_tool.execute(operation="suggest_assignee", description="Fix critical backend server bug")
        print(f"Suggestions: {suggestions}")
        if suggestions:
            # Auto-assign to top suggestion
            manus_tool.tasks['T1']['assignee'] = suggestions[0]['assignee']
            print(f"Task T1 auto-assigned to {suggestions[0]['assignee']}")

        # 3. Use AI to prioritize tasks
        print("\n--- Prioritizing tasks T1, T2, T3 ---")
        prioritized_list = manus_tool.execute(operation="prioritize_tasks", task_ids_to_prioritize=["T1", "T2", "T3"])
        print("Prioritized Order:")
        for task in prioritized_list:
            print(f"  - {task['task_id']}: {task['description']} (Due: {task['due_date']})")

        # 4. Add a subtask
        print("\n--- Adding a subtask ---")
        manus_tool.execute(operation="add_subtask", parent_task_id="T2", task_id="T2.1", description="Create wireframes", due_date="2025-11-16", assignee="Charlie")
        print("Subtask T2.1 added to T2.")
        print(json.dumps(manus_tool.tasks['T2'], indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
