import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated workflows
workflows: Dict[str, Dict[str, Any]] = {}

class WorkflowAutomationTool(BaseTool):
    """
    A tool to simulate a workflow automation system.
    """
    def __init__(self, tool_name: str = "workflow_automation_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates workflow automation: define, start, get status, complete tasks, and list workflows."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'define_workflow', 'start_workflow', 'get_status', 'complete_task', 'list_workflows'."
                },
                "workflow_name": {"type": "string", "description": "The unique name of the workflow."},
                "tasks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "An ordered list of task names for the workflow definition."
                },
                "current_task_name": {"type": "string", "description": "The name of the task to complete."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            workflow_name = kwargs.get("workflow_name")

            if action in ['define_workflow', 'start_workflow', 'get_status', 'complete_task'] and not workflow_name:
                raise ValueError(f"'workflow_name' is required for the '{action}' action.")

            actions = {
                "define_workflow": self._define_workflow,
                "start_workflow": self._start_workflow,
                "get_status": self._get_workflow_status,
                "complete_task": self._complete_task,
                "list_workflows": self._list_workflows,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WorkflowAutomationTool: {e}")
            return {"error": str(e)}

    def _define_workflow(self, workflow_name: str, tasks: List[str], **kwargs) -> Dict:
        if not tasks:
            raise ValueError("'tasks' list cannot be empty for workflow definition.")
        if workflow_name in workflows:
            raise ValueError(f"Workflow '{workflow_name}' already defined.")
            
        new_workflow = {
            "name": workflow_name,
            "definition": tasks,
            "status": "defined",
            "current_task_index": -1, # -1 means not started
            "started_at": None,
            "completed_at": None
        }
        workflows[workflow_name] = new_workflow
        logger.info(f"Workflow '{workflow_name}' defined with {len(tasks)} tasks.")
        return {"message": "Workflow defined successfully.", "details": new_workflow}

    def _start_workflow(self, workflow_name: str, **kwargs) -> Dict:
        if workflow_name not in workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found.")
        
        workflow = workflows[workflow_name]
        if workflow["status"] == "running":
            return {"message": f"Workflow '{workflow_name}' is already running."}
        if workflow["status"] == "completed":
            return {"message": f"Workflow '{workflow_name}' has already completed."}

        workflow["status"] = "running"
        workflow["current_task_index"] = 0
        workflow["started_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Workflow '{workflow_name}' started.")
        return {"message": "Workflow started successfully.", "details": workflow}

    def _get_workflow_status(self, workflow_name: str, **kwargs) -> Dict:
        if workflow_name not in workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found.")
        return {"workflow_status": workflows[workflow_name]}

    def _complete_task(self, workflow_name: str, current_task_name: str, **kwargs) -> Dict:
        if workflow_name not in workflows:
            raise ValueError(f"Workflow '{workflow_name}' not found.")
        
        workflow = workflows[workflow_name]
        if workflow["status"] != "running":
            raise ValueError(f"Workflow '{workflow_name}' is not running.")
        
        expected_task = workflow["definition"][workflow["current_task_index"]]
        if expected_task != current_task_name:
            raise ValueError(f"Expected task '{expected_task}', but received '{current_task_name}'.")

        workflow["current_task_index"] += 1
        
        if workflow["current_task_index"] >= len(workflow["definition"]):
            workflow["status"] = "completed"
            workflow["completed_at"] = datetime.now(timezone.utc).isoformat()
            message = f"Task '{current_task_name}' completed. Workflow '{workflow_name}' has finished."
        else:
            message = f"Task '{current_task_name}' completed. Next task: '{workflow['definition'][workflow['current_task_index']]}'."
        
        logger.info(message)
        return {"message": message, "workflow_status": workflow}

    def _list_workflows(self, **kwargs) -> Dict:
        if not workflows:
            return {"message": "No workflows defined yet."}
        return {"workflows": list(workflows.values())}