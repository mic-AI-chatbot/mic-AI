import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DisasterRecoveryOrchestratorTool(BaseTool):
    """
    A tool for simulating disaster recovery (DR) orchestration.
    """

    def __init__(self, tool_name: str = "disaster_recovery_orchestrator"):
        super().__init__(tool_name)
        self.plans_file = "dr_plans.json"
        self.plans: Dict[str, Dict[str, Any]] = self._load_plans()

    @property
    def description(self) -> str:
        return "Simulates disaster recovery orchestration: defines DR plans, executes them, and tracks their status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The DR orchestration operation to perform.",
                    "enum": ["create_plan", "execute_plan", "get_plan_status", "list_plans", "get_execution_logs"]
                },
                "plan_id": {"type": "string"},
                "plan_name": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "object"}},
                "description": {"type": "string"},
                "target_environment": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_plans(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.plans_file):
            with open(self.plans_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted plans file '{self.plans_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_plans(self) -> None:
        with open(self.plans_file, 'w') as f:
            json.dump(self.plans, f, indent=4)

    def _create_plan(self, plan_id: str, plan_name: str, steps: List[Dict[str, Any]], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([plan_id, plan_name, steps]):
            raise ValueError("Plan ID, name, and steps cannot be empty.")
        if plan_id in self.plans: raise ValueError(f"DR plan '{plan_id}' already exists.")

        new_plan = {
            "plan_id": plan_id, "plan_name": plan_name, "description": description,
            "steps": steps, "status": "ready", "created_at": datetime.now().isoformat(),
            "last_execution": None, "execution_history": []
        }
        self.plans[plan_id] = new_plan
        self._save_plans()
        return new_plan

    def _execute_plan(self, plan_id: str, target_environment: str) -> Dict[str, Any]:
        plan = self.plans.get(plan_id)
        if not plan: raise ValueError(f"DR plan '{plan_id}' not found.")
        if plan["status"] == "executing": raise ValueError(f"DR plan '{plan_id}' is already executing.")

        plan["status"] = "executing"
        self._save_plans()

        execution_log: List[Dict[str, Any]] = []
        overall_execution_status = "completed"

        for i, step in enumerate(plan["steps"]):
            step_status = random.choice(["succeeded", "failed"])  # nosec B311
            step_message = f"Step '{step.get('name', f'Step {i+1}')}' executed on '{target_environment}'."
            if step_status == "failed": overall_execution_status = "failed"; step_message += " (Simulated failure)."
            
            execution_log.append({
                "step_index": i + 1, "step_name": step.get("name", f"Step {i+1}"),
                "status": step_status, "message": step_message, "timestamp": datetime.now().isoformat()
            })
            if step_status == "failed": break

        plan["status"] = overall_execution_status
        plan["last_execution"] = {
            "execution_id": f"EXEC-{plan_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "target_environment": target_environment, "status": overall_execution_status,
            "executed_at": datetime.now().isoformat(), "log_summary": execution_log
        }
        plan["execution_history"].append(plan["last_execution"])
        self._save_plans()
        return plan["last_execution"]

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_plan":
            return self._create_plan(kwargs.get("plan_id"), kwargs.get("plan_name"), kwargs.get("steps"), kwargs.get("description"))
        elif operation == "execute_plan":
            return self._execute_plan(kwargs.get("plan_id"), kwargs.get("target_environment"))
        elif operation == "get_plan_status":
            plan = self.plans.get(kwargs.get("plan_id"))
            if not plan: return None
            return {
                "plan_id": plan["plan_id"], "plan_name": plan["plan_name"], "status": plan["status"],
                "last_execution": plan["last_execution"], "created_at": plan["created_at"]
            }
        elif operation == "list_plans":
            return [{k: v for k, v in plan.items() if k not in ["steps", "execution_history"]} for plan in self.plans.values()]
        elif operation == "get_execution_logs":
            plan = self.plans.get(kwargs.get("plan_id"))
            if not plan: raise ValueError(f"DR plan '{kwargs.get('plan_id')}' not found.")
            return plan["execution_history"]
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DisasterRecoveryOrchestratorTool functionality...")
    tool = DisasterRecoveryOrchestratorTool()
    
    try:
        print("\n--- Creating DR Plan ---")
        tool.execute(operation="create_plan", plan_id="app_failover", plan_name="Web App Failover", steps=[{"name": "switch_dns"}], description="Plan to failover web app.")
        
        print("\n--- Executing Plan ---")
        execution_summary = tool.execute(operation="execute_plan", plan_id="app_failover", target_environment="DR_Site_A")
        print(json.dumps(execution_summary, indent=2))

        print("\n--- Getting Plan Status ---")
        status = tool.execute(operation="get_plan_status", plan_id="app_failover")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.plans_file): os.remove(tool.plans_file)
        print("\nCleanup complete.")