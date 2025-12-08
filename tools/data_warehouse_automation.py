import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataWarehouseAutomationTool(BaseTool):
    """
    A tool for simulating data warehouse automation, allowing for the definition
    and execution of automation tasks such as data loading, schema updates, etc.
    """

    def __init__(self, tool_name: str = "data_warehouse_automation"):
        super().__init__(tool_name)
        self.tasks_file = "warehouse_automation_tasks.json"
        self.tasks: Dict[str, Dict[str, Any]] = self._load_tasks()

    @property
    def description(self) -> str:
        return "Defines and executes data warehouse automation tasks like data loading, schema updates, and report generation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The automation operation to perform.",
                    "enum": ["define_task", "execute_task", "get_task_status", "list_tasks"]
                },
                "task_id": {"type": "string"},
                "task_name": {"type": "string"},
                "task_type": {"type": "string", "enum": ["data_load", "schema_update", "report_generation"]},
                "configuration": {"type": "object"},
                "schedule": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_tasks(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted tasks file '{self.tasks_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_tasks(self) -> None:
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f, indent=4)

    def _define_task(self, task_id: str, task_name: str, task_type: str, configuration: Dict[str, Any], schedule: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([task_id, task_name, task_type, configuration]):
            raise ValueError("Task ID, name, type, and configuration cannot be empty.")
        if task_id in self.tasks:
            raise ValueError(f"Automation task '{task_id}' already exists.")

        new_task = {
            "task_id": task_id, "task_name": task_name, "task_type": task_type,
            "configuration": configuration, "schedule": schedule, "description": description,
            "status": "defined", "defined_at": datetime.now().isoformat(), "last_executed_at": None
        }
        self.tasks[task_id] = new_task
        self._save_tasks()
        return new_task

    def _execute_task(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task: raise ValueError(f"Automation task '{task_id}' not found.")
        
        task["status"] = "running"
        task["last_executed_at"] = datetime.now().isoformat()
        self._save_tasks()

        execution_result = {
            "task_id": task_id, "task_name": task["task_name"], "status": "completed",
            "message": f"Simulated execution of task '{task_id}' ({task['task_type']}).",
            "executed_at": datetime.now().isoformat()
        }
        task["status"] = "completed"
        self._save_tasks()
        return execution_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_task":
            return self._define_task(kwargs.get("task_id"), kwargs.get("task_name"), kwargs.get("task_type"), kwargs.get("configuration"), kwargs.get("schedule"), kwargs.get("description"))
        elif operation == "execute_task":
            return self._execute_task(kwargs.get("task_id"))
        elif operation == "get_task_status":
            return self.tasks.get(kwargs.get("task_id"))
        elif operation == "list_tasks":
            return list(self.tasks.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataWarehouseAutomationTool functionality...")
    tool = DataWarehouseAutomationTool()
    
    try:
        print("\n--- Defining Task ---")
        tool.execute(operation="define_task", task_id="daily_load", task_name="Daily Data Load", task_type="data_load", configuration={"source": "CRM", "target": "DWH"}, schedule="daily")
        
        print("\n--- Executing Task ---")
        execution_result = tool.execute(operation="execute_task", task_id="daily_load")
        print(json.dumps(execution_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.tasks_file): os.remove(tool.tasks_file)
        print("\nCleanup complete.")