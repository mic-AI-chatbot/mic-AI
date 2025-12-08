import logging
import json
import random
import psutil
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import Counter
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class GetProcessMetricsTool(BaseTool):
    """Tool to get real-time performance metrics for a running process."""
    def __init__(self, tool_name="get_process_metrics"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Gets real-time performance metrics (CPU, memory, status) for a process specified by its Process ID (PID)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"pid": {"type": "integer", "description": "The Process ID of the application to monitor."}},
            "required": ["pid"]
        }

    def execute(self, pid: int, **kwargs: Any) -> str:
        try:
            if not psutil.pid_exists(pid):
                return json.dumps({"error": f"Process with PID {pid} not found."})
            
            process = psutil.Process(pid)
            # The 'with' statement ensures that the context is managed correctly
            with process.oneshot():
                metrics = {
                    "pid": pid,
                    "name": process.name(),
                    "status": process.status(),
                    "cpu_percent": process.cpu_percent(interval=0.1), # A short interval for a quick reading
                    "memory_info_bytes": process.memory_info()._asdict(),
                    "memory_percent": round(process.memory_percent(), 2)
                }
            return json.dumps(metrics, indent=2)
        except psutil.NoSuchProcess:
            return json.dumps({"error": f"Process with PID {pid} no longer exists."})
        except Exception as e:
            logger.error(f"Error getting metrics for PID {pid}: {e}")
            return json.dumps({"error": f"An error occurred while fetching process metrics: {e}"})

def generate_mock_log_content(num_lines: int) -> str:
    """Generates content for a mock log file."""
    log_content = ""
    now = datetime.utcnow()
    log_levels = ["INFO"] * 7 + ["WARNING"] * 2 + ["ERROR"] # 70% INFO, 20% WARNING, 10% ERROR
    error_types = ["NullPointerException", "NetworkTimeout", "DatabaseConnectionError", "AccessDeniedError", "ConfigurationError"]
    
    for i in range(num_lines):
        timestamp = (now - timedelta(seconds=random.randint(0, 3600))).isoformat() + "Z"  # nosec B311
        level = random.choice(log_levels)  # nosec B311
        message = "Request processed successfully."
        if level == "WARNING":
            message = f"High latency detected on endpoint /api/v1/{random.choice(['users', 'orders'])}."  # nosec B311
        elif level == "ERROR":
            message = f"Exception occurred: {random.choice(error_types)} in module {random.choice(['auth', 'payment', 'inventory'])}."  # nosec B311
        
        log_content += f"{timestamp} [{level}] {message}\n"
    return log_content

class GenerateMockLogFileTool(BaseTool):
    """Tool to generate a mock log file for analysis."""
    def __init__(self, tool_name="generate_mock_log_file"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a mock application log file with a mix of INFO, WARNING, and ERROR messages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "The path where the generated log file will be saved."},
                "num_lines": {"type": "integer", "description": "The number of lines to generate in the log file.", "default": 200}
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, num_lines: int = 200, **kwargs: Any) -> str:
        try:
            log_content = generate_mock_log_content(num_lines)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(log_content)
            return json.dumps({"message": f"Mock log file with {num_lines} lines created at '{os.path.abspath(file_path)}'."})
        except Exception as e:
            logger.error(f"Failed to create mock log file at {file_path}: {e}")
            return json.dumps({"error": f"Failed to create mock log file: {e}"})

class AnalyzeLogForErrorsTool(BaseTool):
    """Tool to analyze a log file for errors."""
    def __init__(self, tool_name="analyze_log_for_errors"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a log file to find and summarize errors, providing a count of each error type and a sample of error messages."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "The path to the log file to analyze."}},
            "required": ["file_path"]
        }

    def execute(self, file_path: str, **kwargs: Any) -> str:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"Log file not found at '{file_path}'."})

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            errors = [line.strip() for line in lines if "[ERROR]" in line]
            # A more robust way to extract the error type
            error_summary = Counter(line.split("Exception occurred: ")[1].split(" ")[0] for line in errors if "Exception occurred: " in line)

            report = {
                "log_file": file_path,
                "lines_analyzed": len(lines),
                "total_errors_found": len(errors),
                "error_summary": dict(error_summary),
                "error_samples": errors[:5] # Provide a sample of the first 5 errors
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"Failed to analyze log file {file_path}: {e}")
            return json.dumps({"error": f"Failed to analyze log file: {e}"})