import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DesignSprintFacilitatorTool(BaseTool):
    """
    A tool for simulating the facilitation of design sprints.
    """

    def __init__(self, tool_name: str = "design_sprint_facilitator"):
        super().__init__(tool_name)
        self.sprints_file = "design_sprints.json"
        self.sprints: Dict[str, Dict[str, Any]] = self._load_sprints()

    @property
    def description(self) -> str:
        return "Simulates design sprint facilitation: starts sprints, advances phases, and generates reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The design sprint operation to perform.",
                    "enum": ["start_sprint", "advance_phase", "generate_sprint_report", "list_sprints", "get_sprint_details"]
                },
                "sprint_id": {"type": "string"},
                "project_name": {"type": "string"},
                "duration_days": {"type": "integer", "minimum": 1},
                "initial_phase": {"type": "string", "enum": ["understand", "map", "sketch", "decide", "prototype", "test"]},
                "description": {"type": "string"},
                "next_phase": {"type": "string", "enum": ["understand", "map", "sketch", "decide", "prototype", "test", "completed"]}
            },
            "required": ["operation"]
        }

    def _load_sprints(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.sprints_file):
            with open(self.sprints_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted sprints file '{self.sprints_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_sprints(self) -> None:
        with open(self.sprints_file, 'w') as f:
            json.dump(self.sprints, f, indent=4)

    def _start_sprint(self, sprint_id: str, project_name: str, duration_days: int, initial_phase: str = "understand", description: Optional[str] = None) -> Dict[str, Any]:
        if not all([sprint_id, project_name, duration_days, initial_phase]):
            raise ValueError("Sprint ID, project name, duration, and initial phase cannot be empty.")
        if sprint_id in self.sprints: raise ValueError(f"Design sprint '{sprint_id}' already exists.")
        if initial_phase not in ["understand", "map", "sketch", "decide", "prototype", "test"]: raise ValueError(f"Invalid initial_phase: '{initial_phase}'.")

        new_sprint = {
            "sprint_id": sprint_id, "project_name": project_name, "description": description,
            "duration_days": duration_days, "current_phase": initial_phase, "status": "in_progress",
            "started_at": datetime.now().isoformat(), "completed_at": None,
            "phase_history": [{"phase": initial_phase, "started_at": datetime.now().isoformat()}]
        }
        self.sprints[sprint_id] = new_sprint
        self._save_sprints()
        return new_sprint

    def _advance_phase(self, sprint_id: str, next_phase: str) -> Dict[str, Any]:
        sprint = self.sprints.get(sprint_id)
        if not sprint: raise ValueError(f"Design sprint '{sprint_id}' not found.")
        if sprint["status"] != "in_progress": raise ValueError(f"Sprint '{sprint_id}' is not in progress.")
        if next_phase not in ["understand", "map", "sketch", "decide", "prototype", "test", "completed"]: raise ValueError(f"Invalid next_phase: '{next_phase}'.")

        sprint["current_phase"] = next_phase
        sprint["phase_history"].append({"phase": next_phase, "started_at": datetime.now().isoformat()})
        if next_phase == "completed": sprint["status"] = "completed"; sprint["completed_at"] = datetime.now().isoformat()
        
        self._save_sprints()
        return sprint

    def _generate_sprint_report(self, sprint_id: str) -> Dict[str, Any]:
        sprint = self.sprints.get(sprint_id)
        if not sprint: raise ValueError(f"Design sprint '{sprint_id}' not found.")
        
        report = {
            "report_id": f"SPRINT_REPORT-{sprint_id}", "sprint_id": sprint_id, "project_name": sprint["project_name"],
            "status": sprint["status"], "current_phase": sprint["current_phase"], "duration_days": sprint["duration_days"],
            "started_at": sprint["started_at"], "completed_at": sprint["completed_at"],
            "phase_history": sprint["phase_history"],
            "summary": f"Design sprint for '{sprint['project_name']}' is currently '{sprint['status']}'. Last phase was '{sprint['current_phase']}'.",
            "generated_at": datetime.now().isoformat()
        }
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "start_sprint":
            return self._start_sprint(kwargs.get("sprint_id"), kwargs.get("project_name"), kwargs.get("duration_days"), kwargs.get("initial_phase", "understand"), kwargs.get("description"))
        elif operation == "advance_phase":
            return self._advance_phase(kwargs.get("sprint_id"), kwargs.get("next_phase"))
        elif operation == "generate_sprint_report":
            return self._generate_sprint_report(kwargs.get("sprint_id"))
        elif operation == "list_sprints":
            return list(self.sprints.values())
        elif operation == "get_sprint_details":
            return self.sprints.get(kwargs.get("sprint_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DesignSprintFacilitatorTool functionality...")
    tool = DesignSprintFacilitatorTool()
    
    try:
        print("\n--- Starting Design Sprint ---")
        tool.execute(operation="start_sprint", sprint_id="sprint_001", project_name="New Feature X", duration_days=5, initial_phase="understand")
        
        print("\n--- Advancing Phase ---")
        tool.execute(operation="advance_phase", sprint_id="sprint_001", next_phase="map")

        print("\n--- Generating Sprint Report ---")
        report = tool.execute(operation="generate_sprint_report", sprint_id="sprint_001")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.sprints_file): os.remove(tool.sprints_file)
        print("\nCleanup complete.")