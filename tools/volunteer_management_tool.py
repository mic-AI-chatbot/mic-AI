import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated volunteers and tasks
volunteers: Dict[str, Dict[str, Any]] = {}
tasks: Dict[str, Dict[str, Any]] = {}

class VolunteerManagementTool(BaseTool):
    """
    A tool to simulate managing volunteers and their assigned tasks.
    """
    def __init__(self, tool_name: str = "volunteer_management_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates volunteer management: register, assign tasks, update task status, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'register_volunteer', 'assign_task', 'update_task_status', 'get_volunteer_report', 'list_volunteers', 'list_tasks'."
                },
                "volunteer_id": {"type": "string", "description": "The unique ID of the volunteer."},
                "name": {"type": "string", "description": "The name of the volunteer."},
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of skills the volunteer possesses (e.g., 'first_aid', 'driving')."
                },
                "availability": {"type": "string", "description": "The volunteer's availability (e.g., 'weekends', 'weekdays', 'any')."},
                "task_id": {"type": "string", "description": "The unique ID of the task."},
                "task_description": {"type": "string", "description": "A description of the task."},
                "due_date": {"type": "string", "description": "The due date for the task (YYYY-MM-DD)."},
                "task_status": {
                    "type": "string",
                    "description": "The new status for a task ('pending', 'in_progress', 'completed', 'cancelled')."
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            volunteer_id = kwargs.get("volunteer_id")
            task_id = kwargs.get("task_id")

            if action in ['register_volunteer', 'assign_task', 'get_volunteer_report'] and not volunteer_id:
                raise ValueError(f"'volunteer_id' is required for the '{action}' action.")
            if action in ['assign_task', 'update_task_status'] and not task_id:
                raise ValueError(f"'task_id' is required for the '{action}' action.")

            actions = {
                "register_volunteer": self._register_volunteer,
                "assign_task": self._assign_task,
                "update_task_status": self._update_task_status,
                "get_volunteer_report": self._get_volunteer_report,
                "list_volunteers": self._list_volunteers,
                "list_tasks": self._list_tasks,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VolunteerManagementTool: {e}")
            return {"error": str(e)}

    def _register_volunteer(self, volunteer_id: str, name: str, skills: List[str], availability: str = "any", **kwargs) -> Dict:
        if not all([name, skills]):
            raise ValueError("'name' and 'skills' are required to register a volunteer.")
        if volunteer_id in volunteers:
            raise ValueError(f"Volunteer '{volunteer_id}' already registered.")
        
        new_volunteer = {
            "id": volunteer_id,
            "name": name,
            "skills": skills,
            "availability": availability,
            "assigned_tasks": [],
            "registration_date": datetime.now().isoformat()
        }
        volunteers[volunteer_id] = new_volunteer
        logger.info(f"Volunteer '{volunteer_id}' registered.")
        return {"message": "Volunteer registered successfully.", "details": new_volunteer}

    def _assign_task(self, volunteer_id: str, task_id: str, task_description: str, due_date: str, **kwargs) -> Dict:
        if not all([task_description, due_date]):
            raise ValueError("'task_description' and 'due_date' are required to assign a task.")
        if volunteer_id not in volunteers:
            raise ValueError(f"Volunteer '{volunteer_id}' not found.")
        if task_id in tasks:
            raise ValueError(f"Task '{task_id}' already exists.")
        
        new_task = {
            "id": task_id,
            "description": task_description,
            "assigned_to": volunteer_id,
            "due_date": due_date,
            "status": "pending",
            "assigned_date": datetime.now().isoformat()
        }
        tasks[task_id] = new_task
        volunteers[volunteer_id]["assigned_tasks"].append(task_id)
        logger.info(f"Task '{task_id}' assigned to volunteer '{volunteer_id}'.")
        return {"message": "Task assigned successfully.", "details": new_task}

    def _update_task_status(self, task_id: str, task_status: str, **kwargs) -> Dict:
        if task_id not in tasks:
            raise ValueError(f"Task '{task_id}' not found.")
        if task_status not in ["pending", "in_progress", "completed", "cancelled"]:
            raise ValueError(f"Invalid task status. Must be one of: 'pending', 'in_progress', 'completed', 'cancelled'.")
            
        task = tasks[task_id]
        task["status"] = task_status
        task["last_updated"] = datetime.now().isoformat()
        logger.info(f"Task '{task_id}' status updated to '{task_status}'.")
        return {"message": "Task status updated successfully.", "task_id": task_id, "new_status": task_status}

    def _get_volunteer_report(self, volunteer_id: str, **kwargs) -> Dict:
        if volunteer_id not in volunteers:
            raise ValueError(f"Volunteer '{volunteer_id}' not found.")
        
        volunteer_details = volunteers[volunteer_id]
        assigned_tasks_details = [tasks[tid] for tid in volunteer_details["assigned_tasks"] if tid in tasks]
        
        return {"volunteer_report": {"details": volunteer_details, "assigned_tasks": assigned_tasks_details}}

    def _list_volunteers(self, **kwargs) -> Dict:
        if not volunteers:
            return {"message": "No volunteers registered yet."}
        return {"volunteers": list(volunteers.values())}

    def _list_tasks(self, **kwargs) -> Dict:
        if not tasks:
            return {"message": "No tasks created yet."}
        return {"tasks": list(tasks.values())}