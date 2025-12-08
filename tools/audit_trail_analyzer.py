import logging
import json
import os
import re
from datetime import datetime
from collections import Counter
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LogEntryParser:
    """Parses a raw log line into a structured dictionary based on a common log format."""
    def __init__(self, tool_name):
        # Regex to match a common log format: YYYY-MM-DD HH:MM:SS [LEVEL] MESSAGE (and optional user/action)
        # Example: 2025-11-08 10:30:00 [INFO] user:admin action:login Message: User logged in successfully.
        self.log_pattern = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(INFO|WARNING|ERROR|DEBUG)\] (.*)")
        self.user_action_pattern = re.compile(r"user:(\w+)\s+action:(\w+)")

    def parse_line(self, line: str) -> Dict[str, Any]:
        match = self.log_pattern.match(line)
        if match:
            timestamp_str, level, message = match.groups()
            
            parsed_entry = {
                "timestamp": timestamp_str,
                "level": level,
                "message": message.strip()
            }

            user_action_match = self.user_action_pattern.search(message)
            if user_action_match:
                parsed_entry["user"] = user_action_match.group(1)
                parsed_entry["action"] = user_action_match.group(2)
            else:
                parsed_entry["user"] = "N/A"
                parsed_entry["action"] = "N/A"

            return parsed_entry
        return {"raw_line": line}

class SearchAndParseAuditLogTool(BaseTool):
    """Searches and parses audit log entries based on a regex pattern."""
    def __init__(self, tool_name="search_and_parse_audit_log"):
        super().__init__(tool_name=tool_name)
        self.parser = LogEntryParser(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes an audit log file, searches for a regex pattern, and returns matching log entries in a structured (parsed) format."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "log_file_path": {"type": "string", "description": "The absolute path to the audit log file."},
                "search_pattern": {"type": "string", "description": "Optional regex pattern to filter log messages. If not provided, all lines are parsed."}
            },
            "required": ["log_file_path"]
        }

    def execute(self, log_file_path: str, search_pattern: str = None, **kwargs: Any) -> str:
        if not os.path.isabs(log_file_path):
            return json.dumps({"error": "log_file_path must be an absolute path."})
        if not os.path.exists(log_file_path):
            return json.dumps({"error": f"Audit log file not found at '{log_file_path}'."})

        results = []
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    if search_pattern and not re.search(search_pattern, line):
                        continue
                    
                    parsed_entry = self.parser.parse_line(line.strip())
                    if "raw_line" in parsed_entry: # If parsing failed, include raw line and line number
                        parsed_entry["line_number"] = line_num
                    else:
                        parsed_entry["line_number"] = line_num
                    results.append(parsed_entry)
        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {e}")
            return json.dumps({"error": f"Error reading log file: {e}"})

        return json.dumps(results, indent=2)

class SummarizeUserActivityTool(BaseTool):
    """Summarizes the activities of a specific user from an audit log."""
    def __init__(self, tool_name="summarize_user_activity"):
        super().__init__(tool_name=tool_name)
        self.parser = LogEntryParser(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Summarizes all actions performed by a specific user in an audit log file, providing a count of each action."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "log_file_path": {"type": "string", "description": "The absolute path to the audit log file."},
                "user_id": {"type": "string", "description": "The user ID or username to summarize activity for."}
            },
            "required": ["log_file_path", "user_id"]
        }

    def execute(self, log_file_path: str, user_id: str, **kwargs: Any) -> str:
        if not os.path.isabs(log_file_path):
            return json.dumps({"error": "log_file_path must be an absolute path."})
        if not os.path.exists(log_file_path):
            return json.dumps({"error": f"Audit log file not found at '{log_file_path}'."})

        user_activities = []
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parsed_entry = self.parser.parse_line(line.strip())
                    if parsed_entry.get("user") == user_id:
                        user_activities.append(parsed_entry)
        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {e}")
            return json.dumps({"error": f"Error reading log file: {e}"})

        if not user_activities:
            return json.dumps({"message": f"No activities found for user '{user_id}' in the log."})

        action_counts = Counter(activity["action"] for activity in user_activities if activity.get("action") != "N/A")
        
        report = {
            "user_id": user_id,
            "total_activities": len(user_activities),
            "action_summary": dict(action_counts),
            "recent_activities_sample": user_activities[-5:] # Show last 5 activities for context
        }
        return json.dumps(report, indent=2)

class DetectLogAnomaliesTool(BaseTool):
    """Detects anomalies in an audit log file."""
    def __init__(self, tool_name="detect_log_anomalies"):
        super().__init__(tool_name=tool_name)
        self.parser = LogEntryParser(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Detects anomalies in an audit log file, such as sudden spikes in error messages or unusual login patterns."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"log_file_path": {"type": "string", "description": "The absolute path to the audit log file."}},
            "required": ["log_file_path"]
        }

    def execute(self, log_file_path: str, **kwargs: Any) -> str:
        if not os.path.isabs(log_file_path):
            return json.dumps({"error": "log_file_path must be an absolute path."})
        if not os.path.exists(log_file_path):
            return json.dumps({"error": f"Audit log file not found at '{log_file_path}'."})

        parsed_logs = []
        try:
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    parsed_entry = self.parser.parse_line(line.strip())
                    if "raw_line" not in parsed_entry:
                        parsed_logs.append(parsed_entry)
        except Exception as e:
            logger.error(f"Error reading log file {log_file_path}: {e}")
            return json.dumps({"error": f"Error reading log file: {e}"})

        if not parsed_logs:
            return json.dumps({"message": "No parsable log entries found for anomaly detection."})

        anomalies = []

        # Anomaly 1: Sudden spike in errors (simple threshold)
        error_logs = [log for log in parsed_logs if log.get("level") == "ERROR"]
        if len(error_logs) > len(parsed_logs) * 0.15: # More than 15% errors
            anomalies.append({"type": "High Error Rate", "details": f"{len(error_logs)} out of {len(parsed_logs)} log entries are errors. This is unusually high and may indicate a system issue."})

        # Anomaly 2: Unusual login attempts (e.g., many failed logins from different IPs, or many successful logins for one user)
        login_attempts = [log for log in parsed_logs if log.get("action") == "login"]
        failed_logins = [log for log in login_attempts if "failed" in log.get("message", "").lower()]
        successful_logins = [log for log in login_attempts if "successful" in log.get("message", "").lower()]
        
        if len(failed_logins) > 5 and len(failed_logins) > len(login_attempts) * 0.5:
            anomalies.append({"type": "High Failed Login Rate", "details": f"{len(failed_logins)} failed login attempts out of {len(login_attempts)} total login attempts. This could indicate a brute-force attack or misconfiguration."})
        
        if len(successful_logins) > 10 and len(successful_logins) > len(login_attempts) * 0.8:
            anomalies.append({"type": "High Successful Login Rate", "details": f"{len(successful_logins)} successful login attempts in a short period. This could indicate unusual user activity or a session hijacking."})


        if not anomalies:
            return json.dumps({"message": "No significant anomalies detected in the log based on current rules."})
        
        return json.dumps({"detected_anomalies": anomalies}, indent=2)
