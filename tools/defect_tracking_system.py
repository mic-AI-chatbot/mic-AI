import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DefectTrackingSystemTool(BaseTool):
    """
    A tool for simulating a defect tracking system.
    """

    def __init__(self, tool_name: str = "defect_tracking_system"):
        super().__init__(tool_name)
        self.defects_file = "defects.json"
        self.defects: Dict[str, Dict[str, Any]] = self._load_defects()

    @property
    def description(self) -> str:
        return "Simulates a defect tracking system: creates, updates, and lists defect records."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The defect tracking operation to perform.",
                    "enum": ["create_defect", "update_defect_status", "list_defects", "get_defect_details"]
                },
                "defect_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "reported_by": {"type": "string"},
                "new_status": {"type": "string", "enum": ["open", "in_progress", "resolved", "closed", "reopened"]},
                "assigned_to": {"type": "string"},
                "status_filter": {"type": "string", "enum": ["open", "in_progress", "resolved", "closed", "reopened"]},
                "assigned_to_filter": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_defects(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.defects_file):
            with open(self.defects_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted defects file '{self.defects_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_defects(self) -> None:
        with open(self.defects_file, 'w') as f:
            json.dump(self.defects, f, indent=4)

    def _create_defect(self, defect_id: str, title: str, description: str, severity: str, reported_by: str) -> Dict[str, Any]:
        if not all([defect_id, title, description, severity, reported_by]):
            raise ValueError("Defect ID, title, description, severity, and reported_by cannot be empty.")
        if defect_id in self.defects: raise ValueError(f"Defect '{defect_id}' already exists.")
        if severity not in ["low", "medium", "high", "critical"]: raise ValueError(f"Invalid severity: '{severity}'.")

        new_defect = {
            "defect_id": defect_id, "title": title, "description": description, "severity": severity,
            "reported_by": reported_by, "status": "open", "reported_at": datetime.now().isoformat(),
            "assigned_to": None, "resolved_at": None
        }
        self.defects[defect_id] = new_defect
        self._save_defects()
        return new_defect

    def _update_defect_status(self, defect_id: str, new_status: str, assigned_to: Optional[str] = None) -> Dict[str, Any]:
        defect = self.defects.get(defect_id)
        if not defect: raise ValueError(f"Defect '{defect_id}' not found.")
        if new_status not in ["open", "in_progress", "resolved", "closed", "reopened"]: raise ValueError(f"Invalid new_status: '{new_status}'.")

        defect["status"] = new_status
        if assigned_to: defect["assigned_to"] = assigned_to
        if new_status == "resolved": defect["resolved_at"] = datetime.now().isoformat()
        
        self._save_defects()
        return defect

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_defect":
            return self._create_defect(kwargs.get("defect_id"), kwargs.get("title"), kwargs.get("description"), kwargs.get("severity"), kwargs.get("reported_by"))
        elif operation == "update_defect_status":
            return self._update_defect_status(kwargs.get("defect_id"), kwargs.get("new_status"), kwargs.get("assigned_to"))
        elif operation == "list_defects":
            status_filter = kwargs.get("status_filter")
            assigned_to_filter = kwargs.get("assigned_to_filter")
            filtered_defects = list(self.defects.values())
            if status_filter: filtered_defects = [d for d in filtered_defects if d.get("status") == status_filter]
            if assigned_to_filter: filtered_defects = [d for d in filtered_defects if d.get("assigned_to") == assigned_to_filter]
            return filtered_defects
        elif operation == "get_defect_details":
            return self.defects.get(kwargs.get("defect_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DefectTrackingSystemTool functionality...")
    tool = DefectTrackingSystemTool()
    
    try:
        print("\n--- Creating Defect ---")
        tool.execute(operation="create_defect", defect_id="BUG-001", title="Login button not working", description="User cannot log in.", severity="critical", reported_by="QA")
        
        print("\n--- Updating Defect Status ---")
        tool.execute(operation="update_defect_status", defect_id="BUG-001", new_status="in_progress", assigned_to="Dev_Alice")

        print("\n--- Listing Defects ---")
        defects = tool.execute(operation="list_defects", status_filter="in_progress")
        print(json.dumps(defects, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.defects_file): os.remove(tool.defects_file)
        print("\nCleanup complete.")