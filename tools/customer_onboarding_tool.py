import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

ONBOARDING_PROCESSES_FILE = Path("onboarding_processes.json")

class OnboardingManager:
    """Manages customer onboarding processes, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = ONBOARDING_PROCESSES_FILE):
        if cls._instance is None:
            cls._instance = super(OnboardingManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.processes: Dict[str, Any] = cls._instance._load_processes()
        return cls._instance

    def _load_processes(self) -> Dict[str, Any]:
        """Loads onboarding processes from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty processes.")
                return {}
            except Exception as e:
                logger.error(f"Error loading processes from {self.file_path}: {e}")
                return {}
        return {}

    def _save_processes(self) -> None:
        """Saves onboarding processes to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.processes, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving processes to {self.file_path}: {e}")

    def start_onboarding(self, customer_id: str, onboarding_plan_id: str, plan_steps: List[Dict[str, Any]]) -> bool:
        if customer_id in self.processes:
            return False
        self.processes[customer_id] = {
            "onboarding_plan_id": onboarding_plan_id,
            "status": "in_progress",
            "current_step_index": 0,
            "steps": [{"name": step["name"], "status": "pending"} for step in plan_steps],
            "started_at": datetime.now().isoformat() + "Z",
            "completed_at": None
        }
        # Mark the first step as in_progress
        if self.processes[customer_id]["steps"]:
            self.processes[customer_id]["steps"][0]["status"] = "in_progress"
        self._save_processes()
        return True

    def get_onboarding_status(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self.processes.get(customer_id)

    def advance_onboarding_step(self, customer_id: str) -> bool:
        if customer_id not in self.processes:
            return False
        
        process = self.processes[customer_id]
        if process["status"] != "in_progress":
            return False
        
        # Mark current step as completed
        if process["current_step_index"] < len(process["steps"]):
            process["steps"][process["current_step_index"]]["status"] = "completed"
        
        # Advance to next step
        process["current_step_index"] += 1
        if process["current_step_index"] >= len(process["steps"]):
            process["status"] = "completed"
            process["completed_at"] = datetime.now().isoformat() + "Z"
        else:
            process["steps"][process["current_step_index"]]["status"] = "in_progress"
        
        self._save_processes()
        return True

    def list_onboarding_plans(self) -> List[Dict[str, Any]]:
        # This is a mock list of available plans
        return [
            {"plan_id": "basic_onboarding", "name": "Basic Customer Onboarding", "steps": [{"name": "Welcome Email"}, {"name": "Profile Setup"}, {"name": "First Purchase"}]},
            {"plan_id": "premium_onboarding", "name": "Premium Customer Onboarding", "steps": [{"name": "Welcome Call"}, {"name": "Product Demo"}, {"name": "Dedicated Support"}]}
        ]

onboarding_manager = OnboardingManager()

class StartOnboardingTool(BaseTool):
    """Starts a new onboarding process for a customer."""
    def __init__(self, tool_name="start_onboarding"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a new onboarding process for a customer based on a specified onboarding plan."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The ID of the customer to start onboarding for."},
                "onboarding_plan_id": {"type": "string", "description": "The ID of the onboarding plan to use (e.g., 'basic_onboarding', 'premium_onboarding')."}
            },
            "required": ["customer_id", "onboarding_plan_id"]
        }

    def execute(self, customer_id: str, onboarding_plan_id: str, **kwargs: Any) -> str:
        plan_details = None
        for plan in onboarding_manager.list_onboarding_plans():
            if plan["plan_id"] == onboarding_plan_id:
                plan_details = plan
                break
        
        if not plan_details:
            return json.dumps({"error": f"Onboarding plan '{onboarding_plan_id}' not found."})

        success = onboarding_manager.start_onboarding(customer_id, onboarding_plan_id, plan_details["steps"])
        if success:
            report = {"message": f"Onboarding process started for customer '{customer_id}' using plan '{onboarding_plan_id}'. Status: in_progress."}
        else:
            report = {"error": f"Onboarding process already exists for customer '{customer_id}'. Cannot start a new one."}
        return json.dumps(report, indent=2)

class AdvanceOnboardingStepTool(BaseTool):
    """Advances a customer's onboarding process to the next step."""
    def __init__(self, tool_name="advance_onboarding_step"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Advances a customer's onboarding process to the next step, marking the current step as completed."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "description": "The ID of the customer whose onboarding process to advance."}},
            "required": ["customer_id"]
        }

    def execute(self, customer_id: str, **kwargs: Any) -> str:
        process = onboarding_manager.get_onboarding_status(customer_id)
        if not process:
            return json.dumps({"error": f"No active onboarding process found for customer '{customer_id}'. Please start one first."})
        if process["status"] == "completed":
            return json.dumps({"message": f"Onboarding process for customer '{customer_id}' is already completed. No further steps to advance."})
        
        success = onboarding_manager.advance_onboarding_step(customer_id)
        if success:
            updated_process = onboarding_manager.get_onboarding_status(customer_id)
            report = {"message": f"Onboarding process for customer '{customer_id}' advanced to next step.", "current_status": updated_process["status"], "current_step": updated_process["steps"][updated_process["current_step_index"]]["name"] if updated_process["status"] == "in_progress" else "N/A"}
        else:
            report = {"error": f"Failed to advance onboarding step for customer '{customer_id}'. Process might not be in progress or an unexpected error occurred."}
        return json.dumps(report, indent=2)

class GetOnboardingStatusTool(BaseTool):
    """Retrieves the current status of a customer's onboarding process."""
    def __init__(self, tool_name="get_onboarding_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status and progress of a customer's onboarding process, including completed and pending steps."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "description": "The ID of the customer to get onboarding status for."}},
            "required": ["customer_id"]
        }

    def execute(self, customer_id: str, **kwargs: Any) -> str:
        onboarding = onboarding_manager.get_onboarding_status(customer_id)
        if not onboarding:
            return json.dumps({"error": f"No active onboarding process found for customer '{customer_id}'. Please start one first."})
            
        return json.dumps(onboarding, indent=2)

class ListOnboardingPlansTool(BaseTool):
    """Lists all available onboarding plans."""
    def __init__(self, tool_name="list_onboarding_plans"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all available onboarding plans, showing their ID, name, and steps."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        plans = onboarding_manager.list_onboarding_plans()
        if not plans:
            return json.dumps({"message": "No onboarding plans found."})
        
        return json.dumps({"total_plans": len(plans), "onboarding_plans": plans}, indent=2)
