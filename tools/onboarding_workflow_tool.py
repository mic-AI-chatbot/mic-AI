import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class OnboardingWorkflowSimulatorTool(BaseTool):
    """
    A tool that simulates an onboarding workflow system, allowing for defining
    workflows, tracking user progress, and completing individual steps.
    """

    def __init__(self, tool_name: str = "OnboardingWorkflowSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.workflows_file = os.path.join(self.data_dir, "onboarding_workflows.json")
        self.progress_file = os.path.join(self.data_dir, "user_onboarding_progress.json")
        
        # Workflows structure: {workflow_id: {name: ..., steps: [{name: ..., description: ...}]}}
        self.workflows: Dict[str, Dict[str, Any]] = self._load_data(self.workflows_file, default={})
        # User progress structure: {user_id: {workflow_id: {step_name: "pending"|"completed"}}}
        self.user_progress: Dict[str, Dict[str, Dict[str, str]]] = self._load_data(self.progress_file, default={})

    @property
    def description(self) -> str:
        return "Simulates onboarding workflows: define workflows, track user progress, complete steps."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_workflow", "start_onboarding", "complete_step", "get_user_progress", "list_workflows"]},
                "workflow_id": {"type": "string"},
                "name": {"type": "string", "description": "Name of the workflow."},
                "steps": {
                    "type": "array", 
                    "items": {
                        "type": "object", 
                        "properties": {
                            "name": {"type": "string"}, 
                            "description": {"type": "string"}
                        }
                    }
                },
                "user_id": {"type": "string"},
                "step_name": {"type": "string"}
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

    def _save_workflows(self):
        with open(self.workflows_file, 'w') as f: json.dump(self.workflows, f, indent=2)

    def _save_user_progress(self):
        with open(self.progress_file, 'w') as f: json.dump(self.user_progress, f, indent=2)

    def define_workflow(self, workflow_id: str, name: str, steps: List[Dict[str, str]]) -> Dict[str, Any]:
        """Defines a new onboarding workflow with a series of steps."""
        if workflow_id in self.workflows: raise ValueError(f"Workflow '{workflow_id}' already exists.")
        
        new_workflow = {"id": workflow_id, "name": name, "steps": steps, "created_at": datetime.now().isoformat()}
        self.workflows[workflow_id] = new_workflow
        self._save_workflows()
        return new_workflow

    def start_onboarding(self, user_id: str, workflow_id: str) -> Dict[str, Any]:
        """Initializes a user's progress for a specific workflow."""
        if workflow_id not in self.workflows: raise ValueError(f"Workflow '{workflow_id}' not found.")
        if user_id not in self.user_progress: self.user_progress[user_id] = {}
        if workflow_id in self.user_progress[user_id]: raise ValueError(f"User '{user_id}' already started workflow '{workflow_id}'.")

        self.user_progress[user_id][workflow_id] = {step["name"]: "pending" for step in self.workflows[workflow_id]["steps"]}
        self._save_user_progress()
        return {"status": "success", "message": f"Onboarding started for user '{user_id}' in workflow '{workflow_id}'."}

    def complete_step(self, user_id: str, workflow_id: str, step_name: str) -> Dict[str, Any]:
        """Marks a specific step as completed for a user in a workflow."""
        if user_id not in self.user_progress or workflow_id not in self.user_progress[user_id]:
            raise ValueError(f"User '{user_id}' not found in workflow '{workflow_id}'.")
        if step_name not in self.user_progress[user_id][workflow_id]:
            raise ValueError(f"Step '{step_name}' not found in workflow '{workflow_id}'.")
        
        self.user_progress[user_id][workflow_id][step_name] = "completed"
        self._save_user_progress()
        return {"status": "success", "message": f"Step '{step_name}' completed for user '{user_id}' in workflow '{workflow_id}'."}

    def get_user_progress(self, user_id: str, workflow_id: str) -> Dict[str, Any]:
        """Retrieves a user's current progress through a workflow."""
        if user_id not in self.user_progress or workflow_id not in self.user_progress[user_id]:
            raise ValueError(f"User '{user_id}' not found in workflow '{workflow_id}'.")
        
        workflow_steps = self.workflows[workflow_id]["steps"]
        progress_details = []
        completed_count = 0
        
        for step in workflow_steps:
            status = self.user_progress[user_id][workflow_id].get(step["name"], "pending")
            progress_details.append({"step_name": step["name"], "description": step["description"], "status": status})
            if status == "completed": completed_count += 1
        
        total_steps = len(workflow_steps)
        completion_percentage = round((completed_count / total_steps) * 100, 2) if total_steps > 0 else 0
        
        return {
            "user_id": user_id, "workflow_id": workflow_id,
            "completion_percentage": completion_percentage,
            "steps": progress_details
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """Lists all defined onboarding workflows."""
        return list(self.workflows.values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "define_workflow": self.define_workflow,
            "start_onboarding": self.start_onboarding,
            "complete_step": self.complete_step,
            "get_user_progress": self.get_user_progress,
            "list_workflows": self.list_workflows
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating OnboardingWorkflowSimulatorTool functionality...")
    temp_dir = "temp_onboarding_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    onboarding_tool = OnboardingWorkflowSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a new employee onboarding workflow
        print("\n--- Defining 'New Employee Onboarding' workflow ---")
        employee_workflow_steps = [
            {"name": "HR Paperwork", "description": "Complete all necessary HR forms."},
            {"name": "IT Setup", "description": "Get laptop, accounts, and access configured."},
            {"name": "Team Introduction", "description": "Meet the team and key stakeholders."},
            {"name": "Training Modules", "description": "Complete mandatory compliance training."}
        ]
        onboarding_tool.execute(operation="define_workflow", workflow_id="new_hire_onboarding", name="New Employee Onboarding", steps=employee_workflow_steps)
        print("Workflow 'new_hire_onboarding' defined.")

        # 2. Start onboarding for a new user
        print("\n--- Starting onboarding for 'user_alice' ---")
        onboarding_tool.execute(operation="start_onboarding", user_id="user_alice", workflow_id="new_hire_onboarding")
        print("Onboarding started for 'user_alice'.")

        # 3. Complete a few steps
        print("\n--- Completing 'HR Paperwork' and 'IT Setup' for 'user_alice' ---")
        onboarding_tool.execute(operation="complete_step", user_id="user_alice", workflow_id="new_hire_onboarding", step_name="HR Paperwork")
        onboarding_tool.execute(operation="complete_step", user_id="user_alice", workflow_id="new_hire_onboarding", step_name="IT Setup")
        print("Steps completed.")

        # 4. Get user's progress report
        print("\n--- Getting progress report for 'user_alice' ---")
        progress_report = onboarding_tool.execute(operation="get_user_progress", user_id="user_alice", workflow_id="new_hire_onboarding")
        print(json.dumps(progress_report, indent=2))

        # 5. List all defined workflows
        print("\n--- Listing all defined workflows ---")
        all_workflows = onboarding_tool.execute(operation="list_workflows")
        print(json.dumps(all_workflows, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")