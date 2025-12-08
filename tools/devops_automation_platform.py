import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DevOpsAutomationPlatformTool(BaseTool):
    """
    A tool for simulating a DevOps automation platform.
    """

    def __init__(self, tool_name: str = "devops_automation_platform"):
        super().__init__(tool_name)
        self.automations_file = "devops_automations.json"
        self.automations: Dict[str, Dict[str, Any]] = self._load_automations()

    @property
    def description(self) -> str:
        return "Simulates a DevOps automation platform: defines, runs, and monitors automation workflows."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The DevOps automation operation to perform.",
                    "enum": ["define_automation", "run_automation", "get_automation_status", "list_automations", "list_automation_runs"]
                },
                "automation_id": {"type": "string"},
                "automation_name": {"type": "string"},
                "workflow_definition": {"type": "object"},
                "description": {"type": "string"},
                "parameters": {"type": "object"},
                "run_id": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_automations(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.automations_file):
            with open(self.automations_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted automations file '{self.automations_file}'. Starting fresh.")
                    return {"workflows": {}, "runs": {}}
        return {"workflows": {}, "runs": {}}

    def _save_automations(self) -> None:
        with open(self.automations_file, 'w') as f:
            json.dump(self.automations, f, indent=4)

    def _define_automation(self, automation_id: str, automation_name: str, workflow_definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([automation_id, automation_name, workflow_definition]):
            raise ValueError("Automation ID, name, and workflow definition cannot be empty.")
        if automation_id in self.automations["workflows"]:
            raise ValueError(f"Automation workflow '{automation_id}' already exists.")

        new_workflow = {
            "automation_id": automation_id, "automation_name": automation_name, "description": description,
            "workflow_definition": workflow_definition, "defined_at": datetime.now().isoformat()
        }
        self.automations["workflows"][automation_id] = new_workflow
        self._save_automations()
        return new_workflow

    def _run_automation(self, automation_id: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        workflow = self.automations["workflows"].get(automation_id)
        if not workflow: raise ValueError(f"Automation workflow '{automation_id}' not found.")
        
        run_id = f"RUN-{automation_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        run_status = random.choice(["succeeded", "failed", "partially_succeeded"])  # nosec B311
        run_log = f"Simulated execution of '{automation_id}'. Status: {run_status}."

        new_run = {
            "run_id": run_id, "automation_id": automation_id, "parameters": parameters,
            "status": run_status, "log": run_log, "started_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }
        self.automations["runs"][run_id] = new_run
        self._save_automations()
        return new_run

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_automation":
            return self._define_automation(kwargs.get("automation_id"), kwargs.get("automation_name"), kwargs.get("workflow_definition"), kwargs.get("description"))
        elif operation == "run_automation":
            return self._run_automation(kwargs.get("automation_id"), kwargs.get("parameters"))
        elif operation == "get_automation_status":
            return self.automations["runs"].get(kwargs.get("run_id"))
        elif operation == "list_automations":
            return list(self.automations["workflows"].values())
        elif operation == "list_automation_runs":
            automation_id = kwargs.get("automation_id")
            if automation_id: return [r for r in self.automations["runs"].values() if r.get("automation_id") == automation_id]
            return list(self.automations["runs"].values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DevOpsAutomationPlatformTool functionality...")
    tool = DevOpsAutomationPlatformTool()
    
    try:
        print("\n--- Defining Automation ---")
        tool.execute(operation="define_automation", automation_id="ci_pipeline", automation_name="CI Pipeline", workflow_definition={"steps": ["build", "test"]}, description="Continuous Integration pipeline.")
        
        print("\n--- Running Automation ---")
        run_result = tool.execute(operation="run_automation", automation_id="ci_pipeline", parameters={"branch": "main"})
        print(json.dumps(run_result, indent=2))

        print("\n--- Getting Automation Status ---")
        status = tool.execute(operation="get_automation_status", run_id=run_result["run_id"])
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.automations_file): os.remove(tool.automations_file)
        print("\nCleanup complete.")
