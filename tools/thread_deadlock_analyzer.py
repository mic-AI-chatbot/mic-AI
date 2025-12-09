import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ThreadDeadlockAnalyzerTool(BaseTool):
    """
    A tool that simulates thread deadlock analysis, allowing for analyzing
    thread dumps and generating reports on detected deadlocks.
    """

    def __init__(self, tool_name: str = "ThreadDeadlockAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "deadlock_analysis_reports.json")
        
        # Analysis reports: {report_id: {dump_path: ..., deadlocks_found: ..., findings: []}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates thread deadlock analysis: analyze thread dumps and generate reports on detected deadlocks."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_thread_dump", "get_analysis_report"]},
                "report_id": {"type": "string"},
                "dump_path": {"type": "string", "description": "Absolute path to the thread dump file."}
            },
            "required": ["operation", "report_id"]
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
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def analyze_thread_dump(self, report_id: str, dump_path: str) -> Dict[str, Any]:
        """Simulates analyzing a thread dump for deadlocks."""
        if report_id in self.analysis_reports: raise ValueError(f"Report '{report_id}' already exists.")
        
        # Simulate analysis success/failure
        if random.random() < 0.1: # 10% chance of simulated analysis error  # nosec B311
            return {"status": "error", "message": f"Simulated: Failed to analyze thread dump at '{dump_path}'. (Analysis error)."}

        deadlocks_found = random.choice([True, False])  # nosec B311
        findings = []
        if deadlocks_found:
            num_deadlocks = random.randint(1, 3)  # nosec B311
            for i in range(num_deadlocks):
                thread1 = f"Thread-{random.randint(1, 10)}"  # nosec B311
                thread2 = f"Thread-{random.randint(1, 10)}"  # nosec B311
                findings.append(f"Deadlock detected between {thread1} and {thread2} over resource X.")
        
        report = {
            "id": report_id, "dump_path": dump_path, "deadlocks_found": deadlocks_found,
            "findings": findings, "analyzed_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_data()
        return report

    def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated thread deadlock analysis report."""
        report = self.analysis_reports.get(report_id)
        if not report: raise ValueError(f"Analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, report_id: str, **kwargs: Any) -> Any:
        if operation == "analyze_thread_dump":
            dump_path = kwargs.get('dump_path')
            if not dump_path:
                raise ValueError("Missing 'dump_path' for 'analyze_thread_dump' operation.")
            return self.analyze_thread_dump(report_id, dump_path)
        elif operation == "get_analysis_report":
            # No additional kwargs required for get_analysis_report
            return self.get_analysis_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ThreadDeadlockAnalyzerTool functionality...")
    temp_dir = "temp_deadlock_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = ThreadDeadlockAnalyzerTool(data_dir=temp_dir)
    
    # Create a dummy thread dump file for testing
    dummy_dump_path = os.path.join(temp_dir, "thread_dump_1.txt")
    with open(dummy_dump_path, 'w') as f:
        f.write("Simulated thread dump content...")
    print(f"Dummy thread dump file created at: {dummy_dump_path}")

    try:
        # 1. Analyze a thread dump
        print("\n--- Analyzing thread dump 'thread_dump_1.txt' ---")
        report = analyzer_tool.execute(operation="analyze_thread_dump", report_id="RPT-001", dump_path=dummy_dump_path)
        print(json.dumps(report, indent=2))

        # 2. Get analysis report
        print(f"\n--- Getting analysis report for '{report['id']}' ---")
        retrieved_report = analyzer_tool.execute(operation="get_analysis_report", report_id=report["id"])
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")