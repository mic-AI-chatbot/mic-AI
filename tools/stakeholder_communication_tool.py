import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class StakeholderCommunicationSimulatorTool(BaseTool):
    """
    A tool that simulates stakeholder communication, allowing for managing
    stakeholder profiles, sending updates, collecting feedback, and generating reports.
    """

    def __init__(self, tool_name: str = "StakeholderCommunicationSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.profiles_file = os.path.join(self.data_dir, "stakeholder_profiles.json")
        self.logs_file = os.path.join(self.data_dir, "communication_logs.json")
        
        # Stakeholder profiles: {stakeholder_id: {name: ..., role: ..., communication_preference: ...}}
        self.stakeholder_profiles: Dict[str, Dict[str, Any]] = self._load_data(self.profiles_file, default={})
        # Communication logs: {stakeholder_id: [{timestamp: ..., type: ..., message: ...}]}
        self.communication_logs: Dict[str, List[Dict[str, Any]]] = self._load_data(self.logs_file, default={})

    @property
    def description(self) -> str:
        return "Simulates stakeholder communication: send updates, collect feedback, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_stakeholder", "send_update", "collect_feedback", "generate_report", "get_stakeholder_details"]},
                "stakeholder_id": {"type": "string"},
                "name": {"type": "string"},
                "role": {"type": "string"},
                "communication_preference": {"type": "string", "enum": ["email", "report", "meeting"]},
                "message": {"type": "string", "description": "The message content for the update."},
                "feedback_text": {"type": "string", "description": "The feedback text collected from the stakeholder."}
            },
            "required": ["operation", "stakeholder_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_profiles(self):
        with open(self.profiles_file, 'w') as f: json.dump(self.stakeholder_profiles, f, indent=2)

    def _save_logs(self):
        with open(self.logs_file, 'w') as f: json.dump(self.communication_logs, f, indent=2)

    def add_stakeholder(self, stakeholder_id: str, name: str, role: str, communication_preference: str) -> Dict[str, Any]:
        """Adds a new stakeholder profile."""
        if stakeholder_id in self.stakeholder_profiles: raise ValueError(f"Stakeholder '{stakeholder_id}' already exists.")
        
        new_stakeholder = {
            "id": stakeholder_id, "name": name, "role": role,
            "communication_preference": communication_preference,
            "created_at": datetime.now().isoformat()
        }
        self.stakeholder_profiles[stakeholder_id] = new_stakeholder
        self._save_profiles()
        return new_stakeholder

    def send_update(self, stakeholder_id: str, message: str) -> Dict[str, Any]:
        """Simulates sending an update message to a stakeholder."""
        if stakeholder_id not in self.stakeholder_profiles: raise ValueError(f"Stakeholder '{stakeholder_id}' not found. Add them first.")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "type": "update_sent", "message": message
        }
        self.communication_logs.setdefault(stakeholder_id, []).append(log_entry)
        self._save_logs()
        return {"status": "success", "message": f"Update sent to '{stakeholder_id}'."}

    def collect_feedback(self, stakeholder_id: str, feedback_text: str) -> Dict[str, Any]:
        """Simulates collecting feedback from a stakeholder."""
        if stakeholder_id not in self.stakeholder_profiles: raise ValueError(f"Stakeholder '{stakeholder_id}' not found. Add them first.")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "type": "feedback_received", "feedback": feedback_text
        }
        self.communication_logs.setdefault(stakeholder_id, []).append(log_entry)
        self._save_logs()
        return {"status": "success", "message": f"Feedback collected from '{stakeholder_id}'."}

    def generate_report(self, stakeholder_id: str) -> Dict[str, Any]:
        """Generates a report summarizing communication and feedback for a stakeholder."""
        stakeholder = self.stakeholder_profiles.get(stakeholder_id)
        if not stakeholder: raise ValueError(f"Stakeholder '{stakeholder_id}' not found.")
        
        logs = self.communication_logs.get(stakeholder_id, [])
        
        update_count = sum(1 for log in logs if log["type"] == "update_sent")
        feedback_count = sum(1 for log in logs if log["type"] == "feedback_received")
        
        report = {
            "stakeholder_id": stakeholder_id, "name": stakeholder["name"],
            "role": stakeholder["role"], "communication_preference": stakeholder["communication_preference"],
            "total_updates_sent": update_count, "total_feedback_received": feedback_count,
            "communication_log": logs,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def get_stakeholder_details(self, stakeholder_id: str) -> Dict[str, Any]:
        """Retrieves the details of a stakeholder."""
        stakeholder = self.stakeholder_profiles.get(stakeholder_id)
        if not stakeholder: raise ValueError(f"Stakeholder '{stakeholder_id}' not found.")
        return stakeholder

    def execute(self, operation: str, stakeholder_id: str, **kwargs: Any) -> Any:
        if operation == "add_stakeholder":
            name = kwargs.get('name')
            role = kwargs.get('role')
            communication_preference = kwargs.get('communication_preference')
            if not all([name, role, communication_preference]):
                raise ValueError("Missing 'name', 'role', or 'communication_preference' for 'add_stakeholder' operation.")
            return self.add_stakeholder(stakeholder_id, name, role, communication_preference)
        elif operation == "send_update":
            message = kwargs.get('message')
            if not message:
                raise ValueError("Missing 'message' for 'send_update' operation.")
            return self.send_update(stakeholder_id, message)
        elif operation == "collect_feedback":
            feedback_text = kwargs.get('feedback_text')
            if not feedback_text:
                raise ValueError("Missing 'feedback_text' for 'collect_feedback' operation.")
            return self.collect_feedback(stakeholder_id, feedback_text)
        elif operation == "generate_report":
            # No additional kwargs required for generate_report
            return self.generate_report(stakeholder_id)
        elif operation == "get_stakeholder_details":
            # No additional kwargs required for get_stakeholder_details
            return self.get_stakeholder_details(stakeholder_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating StakeholderCommunicationSimulatorTool functionality...")
    temp_dir = "temp_stakeholder_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    comm_tool = StakeholderCommunicationSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add a stakeholder
        print("\n--- Adding stakeholder 'project_manager_alice' ---")
        comm_tool.execute(operation="add_stakeholder", stakeholder_id="project_manager_alice", name="Alice Smith", role="Project Manager", communication_preference="email")
        print("Stakeholder added.")

        # 2. Send an update
        print("\n--- Sending update to 'project_manager_alice' ---")
        comm_tool.execute(operation="send_update", stakeholder_id="project_manager_alice", message="Project Alpha is on track for Q4 delivery.")
        print("Update sent.")

        # 3. Collect feedback
        print("\n--- Collecting feedback from 'project_manager_alice' ---")
        comm_tool.execute(operation="collect_feedback", stakeholder_id="project_manager_alice", feedback_text="Great progress, keep up the good work!")
        print("Feedback collected.")

        # 4. Generate a report
        print("\n--- Generating report for 'project_manager_alice' ---")
        report = comm_tool.execute(operation="generate_report", stakeholder_id="project_manager_alice")
        print(json.dumps(report, indent=2))

        # 5. Get stakeholder details
        print("\n--- Getting details for 'project_manager_alice' ---")
        details = comm_tool.execute(operation="get_stakeholder_details", stakeholder_id="project_manager_alice")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")