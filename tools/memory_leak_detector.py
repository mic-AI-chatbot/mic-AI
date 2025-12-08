

import logging
import os
import json
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MemoryLeakSimulatorTool(BaseTool):
    """
    A tool for simulating memory leak detection by profiling an application's
    memory usage over time and calculating the growth rate.
    """

    def __init__(self, tool_name: str = "MemoryLeakSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "profiling_reports.json")
        self.reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates memory leak detection by calculating memory growth over a profiling session."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["start_profiling", "stop_profiling", "get_report"]},
                "app_name": {"type": "string"},
                "session_id": {"type": "string"}
            },
            "required": ["operation"]
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
        with open(self.reports_file, 'w') as f: json.dump(self.reports, f, indent=2)

    def _start_profiling(self, app_name: str) -> Dict[str, Any]:
        """Starts a new memory profiling session."""
        session_id = f"profile_{app_name}_{random.randint(1000, 9999)}"  # nosec B311
        
        if session_id in self.reports:
            raise ValueError("Session ID conflict, please try again.")

        self.reports[session_id] = {
            "app_name": app_name,
            "status": "running",
            "start_time": datetime.now().isoformat(),
            "start_memory_mb": round(random.uniform(50.0, 150.0), 2) # Simulate initial memory  # nosec B311
        }
        self._save_data()
        return {"status": "success", "session_id": session_id, "message": f"Profiling started for '{app_name}'."}

    def _stop_profiling(self, session_id: str) -> Dict[str, Any]:
        """Stops a profiling session and generates a leak report."""
        session = self.reports.get(session_id)
        if not session: raise ValueError(f"Profiling session '{session_id}' not found.")
        if session["status"] != "running": raise ValueError(f"Session '{session_id}' is not currently running.")

        start_time = datetime.fromisoformat(session["start_time"])
        duration_s = (datetime.now() - start_time).total_seconds()
        
        # Simulate memory growth - higher chance of growth if it's a "leaky" app
        leak_multiplier = random.uniform(1.0, 1.0 + (duration_s / 60.0) * 0.5) # up to 50% growth over 60s  # nosec B311
        end_memory = session["start_memory_mb"] * leak_multiplier
        
        growth_mb = end_memory - session["start_memory_mb"]
        growth_rate_mb_s = growth_mb / duration_s if duration_s > 0 else 0

        # Determine if there's a leak
        leak_threshold_mb_s = 0.5 # Arbitrary threshold: 0.5 MB/s is a leak
        is_leak = growth_rate_mb_s > leak_threshold_mb_s
        
        report = {
            "duration_seconds": round(duration_s, 2),
            "start_memory_mb": session["start_memory_mb"],
            "end_memory_mb": round(end_memory, 2),
            "memory_growth_mb": round(growth_mb, 2),
            "growth_rate_mb_s": round(growth_rate_mb_s, 4),
            "potential_leak_detected": is_leak,
            "finding": f"Potential memory leak detected (growth rate > {leak_threshold_mb_s} MB/s)." if is_leak else "No significant memory growth detected."
        }
        
        session["status"] = "stopped"
        session["report"] = report
        self._save_data()
        
        return self.reports[session_id]

    def _get_report(self, session_id: str) -> Dict[str, Any]:
        """Retrieves a completed profiling report."""
        session = self.reports.get(session_id)
        if not session: raise ValueError(f"Profiling session '{session_id}' not found.")
        return session

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "start_profiling": self._start_profiling,
            "stop_profiling": self._stop_profiling,
            "get_report": self._get_report
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MemoryLeakSimulatorTool functionality...")
    temp_dir = "temp_memory_leak_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    detector_tool = MemoryLeakSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Start a profiling session
        print("\n--- Starting profiling for 'webapp' ---")
        start_result = detector_tool.execute(operation="start_profiling", app_name="webapp")
        session_id = start_result["session_id"]
        print(f"Profiling started with session ID: {session_id}")

        # 2. Simulate some work happening
        print("\n--- Simulating work for 2 seconds... ---")
        time.sleep(2)

        # 3. Stop the session and generate the report
        print("\n--- Stopping profiling ---")
        stop_result = detector_tool.execute(operation="stop_profiling", session_id=session_id)
        print("Profiling stopped. Final Report:")
        print(json.dumps(stop_result, indent=2))

        # 4. Retrieve the report again
        print("\n--- Retrieving report separately ---")
        report = detector_tool.execute(operation="get_report", session_id=session_id)
        print(json.dumps(report.get("report"), indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
