import logging
import json
import random
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class TestCase:
    """Represents a single test case within a test run."""
    def __init__(self, case_id: str, description: str):
        self.case_id = case_id
        self.description = description
        self.status = "pending" # pending, passed, failed, skipped
        self.duration_ms = 0
        self.error_message = None

    def run(self):
        """Simulates running the test case."""
        self.duration_ms = random.randint(10, 500)  # nosec B311
        if random.random() < 0.8: # 80% pass rate for simulation  # nosec B311
            self.status = "passed"
        else:
            self.status = "failed"
            self.error_message = random.choice([  # nosec B311
                "AssertionError: Expected 'success', got 'failure'.",
                "TimeoutError: Test case exceeded maximum execution time.",
                "DatabaseError: Failed to connect to the test database.",
                "NetworkError: API endpoint unreachable."
            ])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "description": self.description,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message
        }

class TestRun:
    """Represents a single execution of a test suite."""
    def __init__(self, test_suite_name: str, test_type: str):
        self.test_run_id = f"test_run_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"  # nosec B311
        self.test_suite_name = test_suite_name
        self.test_type = test_type
        self.timestamp = datetime.now().isoformat()
        self.test_cases: List[TestCase] = []
        self.overall_status = "pending" # pending, passed, failed, skipped

    def add_test_case(self, test_case: TestCase):
        self.test_cases.append(test_case)

    def run_all_tests(self):
        """Simulates running all test cases and updates overall status."""
        for tc in self.test_cases:
            tc.run()
        
        if all(tc.status == "passed" for tc in self.test_cases):
            self.overall_status = "passed"
        elif any(tc.status == "failed" for tc in self.test_cases):
            self.overall_status = "failed"
        else:
            self.overall_status = "skipped" # If all are skipped or pending (unlikely after run)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_run_id": self.test_run_id,
            "test_suite_name": self.test_suite_name,
            "test_type": self.test_type,
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "test_cases": [tc.to_dict() for tc in self.test_cases]
        }

class TestOrchestrator:
    """Manages all test runs, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TestOrchestrator, cls).__new__(cls)
            cls._instance.test_runs: Dict[str, TestRun] = {}
        return cls._instance

    def create_test_run(self, test_suite_name: str, test_type: str) -> TestRun:
        test_run = TestRun(test_suite_name, test_type)
        self.test_runs[test_run.test_run_id] = test_run
        return test_run

    def get_test_run(self, test_run_id: str) -> TestRun:
        return self.test_runs.get(test_run_id)

test_orchestrator = TestOrchestrator()

class RunTestsTool(BaseTool):
    """Runs a test suite and generates detailed results."""
    def __init__(self, tool_name="run_tests"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates running a specified test suite (e.g., unit, integration, end-to-end) and returns a test run ID and detailed results."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "test_suite_name": {"type": "string", "description": "The name or identifier of the test suite to run."},
                "test_type": {"type": "string", "description": "The type of tests to run.", "enum": ["unit", "integration", "e2e"]},
                "num_test_cases": {"type": "integer", "description": "The number of individual test cases to simulate.", "default": 10}
            },
            "required": ["test_suite_name", "test_type"]
        }

    def execute(self, test_suite_name: str, test_type: str, num_test_cases: int = 10, **kwargs: Any) -> str:
        test_run = test_orchestrator.create_test_run(test_suite_name, test_type)
        
        for i in range(num_test_cases):
            test_run.add_test_case(TestCase(f"TC_{i+1}", f"Test case {i+1} for {test_type} suite."))
        
        test_run.run_all_tests()
        
        return json.dumps(test_run.to_dict(), indent=2)

class GetTestResultsTool(BaseTool):
    """Retrieves detailed results for a specific test run."""
    def __init__(self, tool_name="get_test_results"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves detailed results for a specific test run, including individual test statuses, durations, and error messages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"test_run_id": {"type": "string", "description": "The ID of the test run to retrieve results for."}},
            "required": ["test_run_id"]
        }

    def execute(self, test_run_id: str, **kwargs: Any) -> str:
        test_run = test_orchestrator.get_test_run(test_run_id)
        if not test_run:
            return json.dumps({"error": f"Test run with ID '{test_run_id}' not found."})
            
        return json.dumps(test_run.to_dict(), indent=2)

class GenerateTestReportTool(BaseTool):
    """Generates a summary report for a test run."""
    def __init__(self, tool_name="generate_test_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a summary report for a test run, including overall status, pass/fail rates, and a list of failed tests."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"test_run_id": {"type": "string", "description": "The ID of the test run to generate a report for."}},
            "required": ["test_run_id"]
        }

    def execute(self, test_run_id: str, **kwargs: Any) -> str:
        test_run = test_orchestrator.get_test_run(test_run_id)
        if not test_run:
            return json.dumps({"error": f"Test run with ID '{test_run_id}' not found."})
        
        total_tests = len(test_run.test_cases)
        passed_tests = sum(1 for tc in test_run.test_cases if tc.status == "passed")
        failed_tests = sum(1 for tc in test_run.test_cases if tc.status == "failed")
        skipped_tests = sum(1 for tc in test_run.test_cases if tc.status == "skipped")

        failed_test_details = [tc.to_dict() for tc in test_run.test_cases if tc.status == "failed"]

        report = {
            "test_run_id": test_run.test_run_id,
            "test_suite_name": test_run.test_suite_name,
            "test_type": test_run.test_type,
            "overall_status": test_run.overall_status,
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "pass_rate_percent": round((passed_tests / total_tests) * 100, 2) if total_tests > 0 else 0,
                "fail_rate_percent": round((failed_tests / total_tests) * 100, 2) if total_tests > 0 else 0
            },
            "failed_test_details": failed_test_details
        }
        return json.dumps(report, indent=2)