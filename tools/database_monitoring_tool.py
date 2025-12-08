import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DatabaseMonitoringTool(BaseTool):
    """
    A tool for simulating database monitoring actions, including recording and
    retrieving metrics, listing active/slow queries, and checking database health.
    """

    def __init__(self, tool_name: str = "database_monitoring_tool"):
        super().__init__(tool_name)
        self.monitoring_data_file = "db_monitoring_data.json"
        self.monitoring_data: Dict[str, Dict[str, Any]] = self._load_data()
        if "databases" not in self.monitoring_data:
            self.monitoring_data["databases"] = {}

    @property
    def description(self) -> str:
        return "Simulates database monitoring: records metrics, lists queries, and checks database health."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The monitoring operation to perform.",
                    "enum": ["record_metrics", "get_current_metrics", "list_active_queries", "identify_slow_queries", "check_health", "list_monitored_databases"]
                },
                "database_id": {"type": "string"},
                "metrics": {"type": "object"},
                "threshold_ms": {"type": "integer", "minimum": 1}
            },
            "required": ["operation"]
        }

    def _load_data(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.monitoring_data_file):
            with open(self.monitoring_data_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted data file '{self.monitoring_data_file}'. Starting fresh.")
                    return {"databases": {}}
        return {"databases": {}}

    def _save_data(self) -> None:
        with open(self.monitoring_data_file, 'w') as f:
            json.dump(self.monitoring_data, f, indent=4)

    def _get_db_entry(self, database_id: str) -> Dict[str, Any]:
        if database_id not in self.monitoring_data["databases"]:
            self.monitoring_data["databases"][database_id] = {
                "metrics_history": [], "active_queries": [], "slow_queries": [], "health_status": "unknown"
            }
        return self.monitoring_data["databases"][database_id]

    def _record_metrics(self, database_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        db_entry = self._get_db_entry(database_id)
        metric_record = {"timestamp": datetime.now().isoformat(), "metrics": metrics}
        db_entry["metrics_history"].append(metric_record)
        self._save_data()
        return metric_record

    def _get_current_metrics(self, database_id: str) -> Optional[Dict[str, Any]]:
        db_entry = self.monitoring_data["databases"].get(database_id)
        if db_entry and db_entry["metrics_history"]: return db_entry["metrics_history"][-1]
        return None

    def _list_active_queries(self, database_id: str) -> List[Dict[str, Any]]:
        db_entry = self._get_db_entry(database_id)
        num_queries = random.randint(0, 3)  # nosec B311
        active_queries = []
        for i in range(num_queries):
            active_queries.append({
                "query_id": f"Q-{database_id}-{random.randint(100, 999)}",  # nosec B311
                "query_text": "SELECT * FROM users WHERE status = 'active'", # Static simulated query  # nosec B311
                "duration_ms": random.randint(10, 100), "user": random.choice(["user_A", "user_B", "user_C"])  # nosec B311
            })
        db_entry["active_queries"] = active_queries
        self._save_data()
        return active_queries

    def _identify_slow_queries(self, database_id: str, threshold_ms: int = 100) -> List[Dict[str, Any]]:
        db_entry = self._get_db_entry(database_id)
        num_slow_queries = random.randint(0, 2)  # nosec B311
        slow_queries = []
        for i in range(num_slow_queries):
            slow_queries.append({
                "query_id": f"SLOW-Q-{database_id}-{random.randint(100, 999)}",  # nosec B311
                "query_text": "SELECT * FROM audit_logs WHERE timestamp < '2023-01-01' ORDER BY timestamp DESC", # Static simulated slow query  # nosec B311
                "duration_ms": random.randint(threshold_ms + 10, threshold_ms + 500),  # nosec B311
                "user": random.choice(["user_D", "user_E"]), "recommendation": "Add index to date column."  # nosec B311
            })
        db_entry["slow_queries"] = slow_queries
        self._save_data()
        return slow_queries

    def _check_health(self, database_id: str) -> Dict[str, Any]:
        db_entry = self._get_db_entry(database_id)
        status = random.choice(["healthy", "degraded", "unreachable"])  # nosec B311
        db_entry["health_status"] = status
        self._save_data()
        health_report = {
            "database_id": database_id, "status": status, "timestamp": datetime.now().isoformat(),
            "details": f"Simulated health check result: {status}."
        }
        return health_report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "record_metrics":
            return self._record_metrics(kwargs.get("database_id"), kwargs.get("metrics"))
        elif operation == "get_current_metrics":
            return self._get_current_metrics(kwargs.get("database_id"))
        elif operation == "list_active_queries":
            return self._list_active_queries(kwargs.get("database_id"))
        elif operation == "identify_slow_queries":
            return self._identify_slow_queries(kwargs.get("database_id"), kwargs.get("threshold_ms", 100))
        elif operation == "check_health":
            return self._check_health(kwargs.get("database_id"))
        elif operation == "list_monitored_databases":
            return list(self.monitoring_data["databases"].keys())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DatabaseMonitoringTool functionality...")
    tool = DatabaseMonitoringTool()
    
    try:
        print("\n--- Recording Metrics ---")
        tool.execute(operation="record_metrics", database_id="prod_db_001", metrics={"cpu_usage_percent": 45, "memory_usage_percent": 60})
        
        print("\n--- Getting Current Metrics ---")
        metrics = tool.execute(operation="get_current_metrics", database_id="prod_db_001")
        print(json.dumps(metrics, indent=2))

        print("\n--- Checking Health ---")
        health = tool.execute(operation="check_health", database_id="prod_db_001")
        print(json.dumps(health, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.monitoring_data_file): os.remove(tool.monitoring_data_file)
        print("\nCleanup complete.")