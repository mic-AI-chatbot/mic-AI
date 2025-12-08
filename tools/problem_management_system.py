import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProblemManagementSimulatorTool(BaseTool):
    """
    A tool that simulates a problem management system, allowing for creating
    problem records, analyzing root causes, and tracking resolution progress.
    """

    def __init__(self, tool_name: str = "ProblemManagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.problems_file = os.path.join(self.data_dir, "problem_records.json")
        # Problem records structure: {problem_id: {description: ..., severity: ..., status: ..., root_cause: ...}}
        self.problem_records: Dict[str, Dict[str, Any]] = self._load_data(self.problems_file, default={})

    @property
    def description(self) -> str:
        return "Simulates problem management: create records, analyze root cause, and track resolution."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_problem", "analyze_root_cause", "track_resolution", "get_problem_details", "list_problems"]},
                "problem_id": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "reported_by": {"type": "string"},
                "new_status": {"type": "string", "enum": ["open", "in_progress", "resolved", "closed"]},
                "filter_status": {"type": "string", "enum": ["open", "in_progress", "resolved", "closed"]}
            },
            "required": ["operation", "problem_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.problems_file, 'w') as f: json.dump(self.problem_records, f, indent=2)

    def create_problem(self, problem_id: str, description: str, severity: str, reported_by: str) -> Dict[str, Any]:
        """Creates a new problem record."""
        if problem_id in self.problem_records: raise ValueError(f"Problem '{problem_id}' already exists.")
        
        new_problem = {
            "id": problem_id, "description": description, "severity": severity,
            "reported_by": reported_by, "status": "open",
            "created_at": datetime.now().isoformat()
        }
        self.problem_records[problem_id] = new_problem
        self._save_data()
        return new_problem

    def analyze_root_cause(self, problem_id: str) -> Dict[str, Any]:
        """Simulates root cause analysis for a problem."""
        problem = self.problem_records.get(problem_id)
        if not problem: raise ValueError(f"Problem '{problem_id}' not found.")
        
        root_cause = random.choice(["software bug", "hardware failure", "user error", "configuration mismatch"])  # nosec B311
        recommended_solution = f"Investigate {root_cause} and implement a fix. Test thoroughly."
        
        problem["root_cause"] = root_cause
        problem["recommended_solution"] = recommended_solution
        problem["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Root cause for '{problem_id}' analyzed.", "root_cause": root_cause, "recommended_solution": recommended_solution}

    def track_resolution(self, problem_id: str, new_status: str) -> Dict[str, Any]:
        """Tracks the resolution progress of a problem."""
        problem = self.problem_records.get(problem_id)
        if not problem: raise ValueError(f"Problem '{problem_id}' not found.")
        
        problem["status"] = new_status
        problem["last_updated_at"] = datetime.now().isoformat()
        if new_status == "resolved" or new_status == "closed":
            problem["resolved_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Problem '{problem_id}' status updated to '{new_status}'."}

    def get_problem_details(self, problem_id: str) -> Dict[str, Any]:
        """Retrieves the full details of a problem."""
        problem = self.problem_records.get(problem_id)
        if not problem: raise ValueError(f"Problem '{problem_id}' not found.")
        return problem

    def list_problems(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all problem records, optionally filtered by status."""
        filtered_list = list(self.problem_records.values())
        if filter_status:
            filtered_list = [p for p in filtered_list if p["status"] == filter_status]
        return filtered_list

    def execute(self, operation: str, problem_id: str, **kwargs: Any) -> Any:
        if operation == "create_problem":
            description = kwargs.get('description')
            severity = kwargs.get('severity')
            reported_by = kwargs.get('reported_by')
            if not all([description, severity, reported_by]):
                raise ValueError("Missing 'description', 'severity', or 'reported_by' for 'create_problem' operation.")
            return self.create_problem(problem_id, description, severity, reported_by)
        elif operation == "analyze_root_cause":
            # No additional kwargs required for analyze_root_cause
            return self.analyze_root_cause(problem_id)
        elif operation == "track_resolution":
            new_status = kwargs.get('new_status')
            if not new_status:
                raise ValueError("Missing 'new_status' for 'track_resolution' operation.")
            return self.track_resolution(problem_id, new_status)
        elif operation == "get_problem_details":
            # No additional kwargs required for get_problem_details
            return self.get_problem_details(problem_id)
        elif operation == "list_problems":
            # filter_status is optional, so no strict check needed here
            return self.list_problems(kwargs.get('filter_status'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProblemManagementSimulatorTool functionality...")
    temp_dir = "temp_problem_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pm_tool = ProblemManagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a problem
        print("\n--- Creating problem 'PROB-001' ---")
        pm_tool.execute(operation="create_problem", problem_id="PROB-001", description="Database connection intermittent", severity="high", reported_by="Alice")
        print("Problem created.")

        # 2. Analyze root cause
        print("\n--- Analyzing root cause for 'PROB-001' ---")
        rca_result = pm_tool.execute(operation="analyze_root_cause", problem_id="PROB-001")
        print(json.dumps(rca_result, indent=2))

        # 3. Track resolution
        print("\n--- Tracking resolution for 'PROB-001' to 'in_progress' ---")
        pm_tool.execute(operation="track_resolution", problem_id="PROB-001", new_status="in_progress")
        print("Status updated.")

        # 4. Get problem details
        print("\n--- Getting details for 'PROB-001' ---")
        details = pm_tool.execute(operation="get_problem_details", problem_id="PROB-001")
        print(json.dumps(details, indent=2))

        # 5. List problems
        print("\n--- Listing all problems ---")
        all_problems = pm_tool.execute(operation="list_problems", problem_id="any") # problem_id is not used for list_problems
        print(json.dumps(all_problems, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")