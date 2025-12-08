import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PerformanceTestingSimulatorTool(BaseTool):
    """
    A tool that simulates performance testing, including running load tests,
    stress tests, and generating reports based on simulated metrics.
    """

    def __init__(self, tool_name: str = "PerformanceTestingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.results_file = os.path.join(self.data_dir, "performance_test_results.json")
        # Results structure: {test_name: {target_url: ..., num_users: ..., metrics: {}}}
        self.performance_test_results: Dict[str, Dict[str, Any]] = self._load_data(self.results_file, default={})

    @property
    def description(self) -> str:
        return "Simulates performance testing: run load/stress tests and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["run_load_test", "run_stress_test", "generate_report", "list_tests"]},
                "test_name": {"type": "string"},
                "target_url": {"type": "string"},
                "num_users": {"type": "integer", "minimum": 1},
                "duration_seconds": {"type": "integer", "minimum": 10, "default": 60}
            },
            "required": ["operation", "test_name"]
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
        with open(self.results_file, 'w') as f: json.dump(self.performance_test_results, f, indent=2)

    def run_load_test(self, test_name: str, target_url: str, num_users: int, duration_seconds: int) -> Dict[str, Any]:
        """Simulates running a load test."""
        if test_name in self.performance_test_results: raise ValueError(f"Test '{test_name}' already exists.")
        
        # Simulate metrics based on num_users and duration
        avg_response_time_ms = round(random.uniform(50 + num_users * 0.5, 200 + num_users * 1.5), 2)  # nosec B311
        throughput_rps = round(random.uniform(num_users * 0.8, num_users * 1.2), 2)  # nosec B311
        error_rate_percent = round(random.uniform(0.0, 2.0 + num_users * 0.01), 2)  # nosec B311
        
        results = {
            "test_type": "load_test",
            "target_url": target_url,
            "num_users": num_users,
            "duration_seconds": duration_seconds,
            "metrics": {
                "average_response_time_ms": avg_response_time_ms,
                "throughput_requests_per_second": throughput_rps,
                "error_rate_percent": error_rate_percent
            },
            "run_at": datetime.now().isoformat()
        }
        self.performance_test_results[test_name] = results
        self._save_data()
        return results

    def run_stress_test(self, test_name: str, target_url: str, num_users: int, duration_seconds: int) -> Dict[str, Any]:
        """Simulates running a stress test."""
        if test_name in self.performance_test_results: raise ValueError(f"Test '{test_name}' already exists.")
        
        # Simulate metrics for stress test (higher errors, slower response, potential crash)
        avg_response_time_ms = round(random.uniform(500 + num_users * 2, 2000 + num_users * 5), 2)  # nosec B311
        throughput_rps = round(random.uniform(num_users * 0.5, num_users * 0.8), 2)  # nosec B311
        error_rate_percent = round(random.uniform(5.0 + num_users * 0.05, 20.0 + num_users * 0.1), 2)  # nosec B311
        system_crashed = random.random() < (num_users / 500.0) # Higher chance of crash with more users  # nosec B311
        
        results = {
            "test_type": "stress_test",
            "target_url": target_url,
            "num_users": num_users,
            "duration_seconds": duration_seconds,
            "metrics": {
                "average_response_time_ms": avg_response_time_ms,
                "throughput_requests_per_second": throughput_rps,
                "error_rate_percent": error_rate_percent,
                "system_crashed": system_crashed
            },
            "run_at": datetime.now().isoformat()
        }
        self.performance_test_results[test_name] = results
        self._save_data()
        return results

    def generate_report(self, test_name: str) -> Dict[str, Any]:
        """Generates a report for a specific performance test."""
        test_result = self.performance_test_results.get(test_name)
        if not test_result: raise ValueError(f"Test '{test_name}' not found.")
        
        report_lines = [
            f"--- Performance Test Report: {test_name} ---",
            f"Test Type: {test_result['test_type'].replace('_', ' ').title()}",
            f"Target URL: {test_result['target_url']}",
            f"Simulated Users: {test_result['num_users']}",
            f"Duration: {test_result['duration_seconds']} seconds",
            f"Run At: {test_result['run_at']}",
            "\nMetrics:"
        ]
        for metric, value in test_result["metrics"].items():
            report_lines.append(f"- {metric.replace('_', ' ').title()}: {value}")
        
        return {"status": "success", "test_name": test_name, "report": "\n".join(report_lines)}

    def list_tests(self) -> List[Dict[str, Any]]:
        """Lists all performed performance tests."""
        return list(self.performance_test_results.values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "run_load_test": self.run_load_test,
            "run_stress_test": self.run_stress_test,
            "generate_report": self.generate_report,
            "list_tests": self.list_tests
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PerformanceTestingSimulatorTool functionality...")
    temp_dir = "temp_perf_test_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    perf_tool = PerformanceTestingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Run a load test
        print("\n--- Running load test 'homepage_load' ---")
        perf_tool.execute(operation="run_load_test", test_name="homepage_load", target_url="https://example.com", num_users=50, duration_seconds=30)
        print("Load test 'homepage_load' completed.")

        # 2. Run a stress test
        print("\n--- Running stress test 'api_stress' ---")
        perf_tool.execute(operation="run_stress_test", test_name="api_stress", target_url="https://api.example.com", num_users=300, duration_seconds=60)
        print("Stress test 'api_stress' completed.")

        # 3. Generate a report for the load test
        print("\n--- Generating report for 'homepage_load' ---")
        report_load = perf_tool.execute(operation="generate_report", test_name="homepage_load")
        print(report_load["report"])

        # 4. Generate a report for 'api_stress' ---")
        report_stress = perf_tool.execute(operation="generate_report", test_name="api_stress")
        print(report_stress["report"])

        # 5. List all tests
        print("\n--- Listing all performance tests ---")
        all_tests = perf_tool.execute(operation="list_tests")
        print(json.dumps(all_tests, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")