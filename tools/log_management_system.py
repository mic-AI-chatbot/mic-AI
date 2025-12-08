

import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
import re

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LogManagementSystemTool(BaseTool):
    """
    A centralized system to ingest, search, and analyze log data from multiple sources.
    This tool provides a more realistic approach to log management and analysis.
    """

    def __init__(self, tool_name: str = "LogManagementSystem", data_dir: str = ".", **kwargs):
        """
        Initializes the LogManagementSystemTool.

        Args:
            tool_name: The name of the tool.
            data_dir: The directory to store log and report data files.
        """
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.logs_file = os.path.join(self.data_dir, "managed_logs.json")
        self.reports_file = os.path.join(self.data_dir, "log_analysis_reports.json")
        
        self.logs: List[Dict[str, Any]] = self._load_data(self.logs_file, default=[])
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "A system to ingest, search, and analyze log data from multiple sources."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform.",
                    "enum": ["ingest_logs", "search_logs", "analyze_logs", "list_logs", "get_report_details"]
                },
                "source": {"type": "string", "description": "Source of the logs (e.g., 'web_server')."},
                "log_entries": {"type": "array", "description": "A list of log entry dictionaries."},
                "search_id": {"type": "string", "description": "Unique ID for a search operation."},
                "query": {"type": "string", "description": "Search query (e.g., 'level:ERROR AND user:alice')."},
                "time_range_hours": {"type": "integer", "description": "Number of past hours to search."},
                "analysis_id": {"type": "string", "description": "Unique ID for an analysis operation."},
                "analysis_type": {"type": "string", "description": "Type of analysis ('error_rate', 'user_activity', 'anomaly_detection')."},
                "report_id": {"type": "string", "description": "ID of the report to retrieve."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        """Loads data from a JSON file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_logs(self):
        with open(self.logs_file, 'w') as f: json.dump(self.logs, f, indent=4)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=4)

    def ingest_logs(self, source: str, log_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests logs from a source, adding timestamps."""
        if not source or not log_entries:
            raise ValueError("Source and log entries are required.")
        
        for entry in log_entries:
            log_entry = {"source": source, "timestamp": datetime.now().isoformat(), **entry}
            self.logs.append(log_entry)
        
        self._save_logs()
        self.logger.info(f"{len(log_entries)} log entries ingested from '{source}'.")
        return {"status": "success", "ingested_count": len(log_entries)}

    def _parse_query(self, query: str) -> Dict[str, str]:
        """Parses a simple 'key:value AND key2:value2' query string."""
        filters = {}
        parts = re.split(r'\s+AND\s+', query, flags=re.IGNORECASE)
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                filters[key.strip()] = value.strip()
        return filters

    def search_logs(self, search_id: str, query: str, time_range_hours: int) -> Dict[str, Any]:
        """Searches logs using a structured query within a time range."""
        if not all([search_id, query]) or time_range_hours <= 0:
            raise ValueError("Search ID, query, and a positive time range are required.")
        if search_id in self.analysis_reports:
            raise ValueError(f"Report with ID '{search_id}' already exists.")

        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_range_hours)
        filters = self._parse_query(query)
        
        matching_logs = []
        for log in self.logs:
            if datetime.fromisoformat(log["timestamp"]) >= start_time:
                match = all(str(log.get(k)) == v for k, v in filters.items())
                if match:
                    matching_logs.append(log)

        report = {
            "report_id": search_id, "query": query, "time_range_hours": time_range_hours,
            "report_type": "log_search", "num_matches": len(matching_logs), "matches": matching_logs,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[search_id] = report
        self._save_reports()
        self.logger.info(f"Log search '{search_id}' found {len(matching_logs)} matches.")
        return report

    def analyze_logs(self, analysis_id: str, analysis_type: str) -> Dict[str, Any]:
        """Performs a specified analysis on the log data."""
        if not all([analysis_id, analysis_type]):
            raise ValueError("Analysis ID and type are required.")
        if analysis_id in self.analysis_reports:
            raise ValueError(f"Report with ID '{analysis_id}' already exists.")

        results: Dict[str, Any] = {}
        if analysis_type == "error_rate":
            error_logs = [log for log in self.logs if str(log.get("level")).upper() == "ERROR"]
            results["total_logs"] = len(self.logs)
            results["total_errors"] = len(error_logs)
            results["error_rate_percent"] = (len(error_logs) / len(self.logs) * 100) if self.logs else 0
        elif analysis_type == "user_activity":
            user_activities = Counter(log.get("user_id") for log in self.logs if "user_id" in log)
            results["unique_users"] = len(user_activities)
            results["top_3_active_users"] = user_activities.most_common(3)
        elif analysis_type == "anomaly_detection":
            # Simple anomaly: error rate spike in the last hour vs previous 23 hours
            last_hour = datetime.now() - timedelta(hours=1)
            logs_last_hour = [l for l in self.logs if datetime.fromisoformat(l["timestamp"]) > last_hour]
            errors_last_hour = [l for l in logs_last_hour if str(l.get("level")).upper() == "ERROR"]
            rate_last_hour = (len(errors_last_hour) / len(logs_last_hour)) if logs_last_hour else 0
            results["error_rate_last_hour"] = rate_last_hour * 100
            results["anomaly_detected"] = rate_last_hour > 0.5 # Anomaly if error rate > 50%
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        report = {
            "report_id": analysis_id, "analysis_type": analysis_type, "results": results,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[analysis_id] = report
        self._save_reports()
        self.logger.info(f"Log analysis '{analysis_id}' of type '{analysis_type}' completed.")
        return report

    def list_logs(self, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists ingested logs, optionally filtered by source."""
        if source:
            return [log for log in self.logs if log.get("source") == source]
        return self.logs

    def get_report_details(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a specific analysis or search report."""
        return self.analysis_reports.get(report_id)

    def execute(self, **kwargs: Any) -> Any:
        """Executes a specified operation."""
        operation = kwargs.get("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "ingest_logs": self.ingest_logs, "search_logs": self.search_logs,
            "analyze_logs": self.analyze_logs, "list_logs": self.list_logs,
            "get_report_details": self.get_report_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")

        import inspect
        sig = inspect.signature(op_map[operation])
        op_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        return op_map[operation](**op_kwargs)

if __name__ == '__main__':
    print("Demonstrating LogManagementSystemTool functionality...")
    temp_dir = "temp_log_manager_data"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    manager_tool = LogManagementSystemTool(data_dir=temp_dir)
    
    try:
        # --- Ingest Logs ---
        print("\n--- Ingesting logs ---")
        manager_tool.execute(operation="ingest_logs", source="web_server", log_entries=[
            {"level": "INFO", "message": "User 'alice' logged in.", "user_id": "alice"},
            {"level": "ERROR", "message": "DB connection failed.", "user_id": "alice"},
        ])
        manager_tool.execute(operation="ingest_logs", source="db_server", log_entries=[
            {"level": "INFO", "message": "Query executed.", "user_id": "bob"},
        ])
        print(f"Total logs ingested: {len(manager_tool.logs)}")

        # --- Search Logs (Structured Query) ---
        print("\n--- Searching for logs from 'alice' with level 'ERROR' ---")
        search_report = manager_tool.execute(
            operation="search_logs", search_id="search001",
            query="level:ERROR AND user_id:alice", time_range_hours=1
        )
        print(json.dumps(search_report, indent=2))

        # --- Analyze Logs (Realistic) ---
        print("\n--- Analyzing for user activity ---")
        analysis_report = manager_tool.execute(
            operation="analyze_logs", analysis_id="analysis001", analysis_type="user_activity"
        )
        print(json.dumps(analysis_report, indent=2))

        # --- Get Report Details ---
        print("\n--- Retrieving details for report 'search001' ---")
        details = manager_tool.execute(operation="get_report_details", report_id="search001")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
