import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PrototypeTestingSimulatorTool(BaseTool):
    """
    A tool that simulates prototype testing, including running user tests,
    collecting feedback, and generating reports on prototype performance.
    """

    def __init__(self, tool_name: str = "PrototypeTestingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.prototypes_file = os.path.join(self.data_dir, "prototype_records.json")
        self.results_file = os.path.join(self.data_dir, "prototype_test_results.json")
        
        # Prototype records: {prototype_id: {name: ..., description: ..., feedback: []}}
        self.prototype_records: Dict[str, Dict[str, Any]] = self._load_data(self.prototypes_file, default={})
        # Test results: {test_id: {prototype_id: ..., metrics: {}, feedback: []}}
        self.test_results: Dict[str, Dict[str, Any]] = self._load_data(self.results_file, default={})

    @property
    def description(self) -> str:
        return "Simulates prototype testing: run user tests, collect feedback, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_prototype", "run_user_test", "collect_feedback", "generate_report", "list_prototypes"]},
                "prototype_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "num_users": {"type": "integer", "minimum": 1},
                "feedback_comments": {"type": "array", "items": {"type": "string"}},
                "test_id": {"type": "string"}
            },
            "required": ["operation", "prototype_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_prototypes(self):
        with open(self.prototypes_file, 'w') as f: json.dump(self.prototype_records, f, indent=2)

    def _save_test_results(self):
        with open(self.results_file, 'w') as f: json.dump(self.test_results, f, indent=2)

    def create_prototype(self, prototype_id: str, name: str, description: str) -> Dict[str, Any]:
        """Creates a new prototype record."""
        if prototype_id in self.prototype_records: raise ValueError(f"Prototype '{prototype_id}' already exists.")
        
        new_prototype = {
            "id": prototype_id, "name": name, "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.prototype_records[prototype_id] = new_prototype
        self._save_prototypes()
        return new_prototype

    def run_user_test(self, prototype_id: str, num_users: int) -> Dict[str, Any]:
        """Simulates running a user test on a prototype."""
        if prototype_id not in self.prototype_records: raise ValueError(f"Prototype '{prototype_id}' not found.")
        
        test_id = f"test_{prototype_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate metrics
        task_completion_rate = round(random.uniform(0.6, 0.95), 2)  # nosec B311
        user_satisfaction_score = round(random.uniform(3.0, 5.0), 1)  # nosec B311
        issues_found = random.randint(0, 5)  # nosec B311
        
        results = {
            "test_id": test_id, "prototype_id": prototype_id, "num_users": num_users,
            "metrics": {
                "task_completion_rate": task_completion_rate,
                "user_satisfaction_score": user_satisfaction_score,
                "issues_found": issues_found
            },
            "run_at": datetime.now().isoformat()
        }
        self.test_results[test_id] = results
        self._save_test_results()
        return results

    def collect_feedback(self, prototype_id: str, feedback_comments: List[str]) -> Dict[str, Any]:
        """Collects feedback comments for a prototype."""
        prototype = self.prototype_records.get(prototype_id)
        if not prototype: raise ValueError(f"Prototype '{prototype_id}' not found.")
        
        if "feedback" not in prototype: prototype["feedback"] = []
        prototype["feedback"].extend(feedback_comments)
        self._save_prototypes()
        return {"status": "success", "message": f"Collected {len(feedback_comments)} feedback comments for '{prototype_id}'."}

    def generate_report(self, prototype_id: str) -> Dict[str, Any]:
        """Generates a report for a prototype, combining test results and feedback."""
        prototype = self.prototype_records.get(prototype_id)
        if not prototype: raise ValueError(f"Prototype '{prototype_id}' not found.")
        
        related_tests = [res for res in self.test_results.values() if res["prototype_id"] == prototype_id]
        
        report_lines = [
            f"--- Prototype Test Report for: {prototype['name']} ({prototype_id}) ---",
            f"Description: {prototype['description']}",
            f"Created At: {prototype['created_at']}",
            "\n--- Test Results ---"
        ]
        
        if related_tests:
            for test in related_tests:
                report_lines.append(f"\nTest ID: {test['test_id']} (Users: {test['num_users']}, Run At: {test['run_at']})")
                for metric, value in test['metrics'].items():
                    report_lines.append(f"- {metric.replace('_', ' ').title()}: {value}")
        else:
            report_lines.append("No user test results found.")
        
        report_lines.append("\n--- User Feedback ---")
        feedback = prototype.get("feedback", [])
        if feedback:
            for i, comment in enumerate(feedback):
                report_lines.append(f"- Comment {i+1}: {comment}")
        else:
            report_lines.append("No feedback collected.")
        
        return {"status": "success", "prototype_id": prototype_id, "report": "\n".join(report_lines)}

    def list_prototypes(self) -> List[Dict[str, Any]]:
        """Lists all created prototypes."""
        return list(self.prototype_records.values())

    def execute(self, operation: str, prototype_id: str, **kwargs: Any) -> Any:
        if operation == "create_prototype":
            name = kwargs.get('name')
            description = kwargs.get('description')
            if not all([name, description]):
                raise ValueError("Missing 'name' or 'description' for 'create_prototype' operation.")
            return self.create_prototype(prototype_id, name, description)
        elif operation == "run_user_test":
            num_users = kwargs.get('num_users')
            if num_users is None: # Check for None specifically as 0 is a valid int
                raise ValueError("Missing 'num_users' for 'run_user_test' operation.")
            return self.run_user_test(prototype_id, num_users)
        elif operation == "collect_feedback":
            feedback_comments = kwargs.get('feedback_comments')
            if not feedback_comments:
                raise ValueError("Missing 'feedback_comments' for 'collect_feedback' operation.")
            return self.collect_feedback(prototype_id, feedback_comments)
        elif operation == "generate_report":
            # No additional kwargs required for generate_report
            return self.generate_report(prototype_id)
        elif operation == "list_prototypes":
            # No additional kwargs required for list_prototypes
            return self.list_prototypes()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PrototypeTestingSimulatorTool functionality...")
    temp_dir = "temp_prototype_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    pt_tool = PrototypeTestingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a prototype
        print("\n--- Creating prototype 'mobile_app_v1' ---")
        pt_tool.execute(operation="create_prototype", prototype_id="mobile_app_v1", name="Mobile App Prototype V1", description="First version of the mobile application.")
        print("Prototype created.")

        # 2. Run a user test
        print("\n--- Running user test for 'mobile_app_v1' with 10 users ---")
        test_result = pt_tool.execute(operation="run_user_test", prototype_id="mobile_app_v1", num_users=10)
        print(json.dumps(test_result, indent=2))

        # 3. Collect feedback
        print("\n--- Collecting feedback for 'mobile_app_v1' ---")
        feedback = ["UI is intuitive.", "Found a bug on the login screen.", "Performance is a bit slow."]
        pt_tool.execute(operation="collect_feedback", prototype_id="mobile_app_v1", feedback_comments=feedback)
        print("Feedback collected.")

        # 4. Generate a report
        print("\n--- Generating report for 'mobile_app_v1' ---")
        report = pt_tool.execute(operation="generate_report", prototype_id="mobile_app_v1")
        print(report["report"])

        # 5. List all prototypes
        print("\n--- Listing all prototypes ---")
        all_prototypes = pt_tool.execute(operation="list_prototypes", prototype_id="any") # prototype_id is not used for list_prototypes
        print(json.dumps(all_prototypes, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")