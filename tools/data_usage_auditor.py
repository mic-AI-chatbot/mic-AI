import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataUsageAuditorTool(BaseTool):
    """
    A tool for simulating data usage auditing, allowing for the recording of
    usage events and the generation of audit reports.
    """

    def __init__(self, tool_name: str = "data_usage_auditor"):
        super().__init__(tool_name)
        self.logs_file = "data_usage_logs.json"
        self.usage_logs: List[Dict[str, Any]] = self._load_logs()

    @property
    def description(self) -> str:
        return "Simulates data usage auditing: records usage events, audits usage based on criteria, and generates reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data usage audit operation to perform.",
                    "enum": ["record_usage_event", "audit_usage", "generate_usage_report", "list_usage_events"]
                },
                "event_id": {"type": "string"},
                "user_id": {"type": "string"},
                "data_asset_name": {"type": "string"},
                "action": {"type": "string"},
                "timestamp": {"type": "string"},
                "start_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"},
                "end_date": {"type": "string", "description": "ISO format (YYYY-MM-DD)"}
            },
            "required": ["operation"]
        }

    def _load_logs(self) -> List[Dict[str, Any]]:
        if os.path.exists(self.logs_file):
            with open(self.logs_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted logs file '{self.logs_file}'. Starting fresh.")
                    return []
        return []

    def _save_logs(self) -> None:
        with open(self.logs_file, 'w') as f:
            json.dump(self.usage_logs, f, indent=4)

    def _record_usage_event(self, event_id: str, user_id: str, data_asset_name: str, action: str, timestamp: Optional[str] = None) -> Dict[str, Any]:
        if not all([event_id, user_id, data_asset_name, action]):
            raise ValueError("Event ID, user ID, data asset name, and action cannot be empty.")
        if any(log["event_id"] == event_id for log in self.usage_logs):
            raise ValueError(f"Usage event '{event_id}' already exists.")

        new_event = {
            "event_id": event_id, "user_id": user_id, "data_asset_name": data_asset_name,
            "action": action, "timestamp": timestamp if timestamp else datetime.now().isoformat()
        }
        self.usage_logs.append(new_event)
        self._save_logs()
        return new_event

    def _audit_usage(self, data_asset_name: str, user_id: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        if not data_asset_name: raise ValueError("Data asset name cannot be empty for auditing.")

        filtered_logs = []
        for log in self.usage_logs:
            if log["data_asset_name"] == data_asset_name:
                if user_id is None or log["user_id"] == user_id:
                    log_timestamp = datetime.fromisoformat(log["timestamp"])
                    
                    if start_date:
                        start_dt = datetime.fromisoformat(start_date)
                        if log_timestamp < start_dt: continue
                    if end_date:
                        end_dt = datetime.fromisoformat(end_date)
                        if log_timestamp > end_dt: continue
                    filtered_logs.append(log)
        return filtered_logs

    def _generate_usage_report(self, data_asset_name: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        audit_results = self._audit_usage(data_asset_name, user_id)
        
        total_accesses = len(audit_results)
        actions_count: Dict[str, int] = {}
        users_involved: Dict[str, int] = {}

        for event in audit_results:
            actions_count[event["action"]] = actions_count.get(event["action"], 0) + 1
            users_involved[event["user_id"]] = users_involved.get(event["user_id"], 0) + 1

        report = {
            "report_id": f"USAGE_REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "data_asset_name": data_asset_name, "user_id_filter": user_id,
            "total_access_events": total_accesses, "actions_summary": actions_count,
            "users_summary": users_involved, "generated_at": datetime.now().isoformat()
        }
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "record_usage_event":
            return self._record_usage_event(kwargs.get("event_id"), kwargs.get("user_id"), kwargs.get("data_asset_name"), kwargs.get("action"), kwargs.get("timestamp"))
        elif operation == "audit_usage":
            return self._audit_usage(kwargs.get("data_asset_name"), kwargs.get("user_id"), kwargs.get("start_date"), kwargs.get("end_date"))
        elif operation == "generate_usage_report":
            return self._generate_usage_report(kwargs.get("data_asset_name"), kwargs.get("user_id"))
        elif operation == "list_usage_events":
            return self.usage_logs
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataUsageAuditorTool functionality...")
    tool = DataUsageAuditorTool()
    
    try:
        print("\n--- Recording Usage Events ---")
        tool.execute(operation="record_usage_event", event_id="event_001", user_id="user_alice", data_asset_name="customer_db", action="read")
        
        print("\n--- Auditing Usage ---")
        audit_results = tool.execute(operation="audit_usage", data_asset_name="customer_db", user_id="user_alice")
        print(json.dumps(audit_results, indent=2))

        print("\n--- Generating Usage Report ---")
        report = tool.execute(operation="generate_usage_report", data_asset_name="customer_db")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.logs_file): os.remove(tool.logs_file)
        print("\nCleanup complete.")