import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PerformanceMonitoringTool(BaseTool):
    """
    A tool to simulate performance monitoring by recording system metrics
    and checking them against defined thresholds for alerts.
    """

    def __init__(self, tool_name: str = "PerformanceMonitor", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.metrics_file = os.path.join(self.data_dir, "performance_metrics.json")
        self.metrics: Dict[str, List[Dict[str, Any]]] = self._load_data(self.metrics_file, default={})

    @property
    def description(self) -> str:
        return "Records and checks system performance metrics against thresholds to generate alerts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["record_metric", "check_alerts", "list_metrics"]},
                "system_name": {"type": "string"},
                "metric_name": {"type": "string"},
                "metric_value": {"type": "number"},
                "thresholds": {"type": "object", "description": "A dict of metric names to their alert thresholds, e.g., {'CPU_Usage': 0.9}."}
            },
            "required": ["operation", "system_name"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_metrics(self):
        with open(self.metrics_file, 'w') as f: json.dump(self.metrics, f, indent=4)

    def record_metric(self, system_name: str, metric_name: str, metric_value: float) -> Dict[str, Any]:
        """Records a new performance metric for a given system."""
        if not all([system_name, metric_name, metric_value is not None]):
            raise ValueError("System name, metric name, and metric value are required.")
        
        if system_name not in self.metrics:
            self.metrics[system_name] = []
            
        metric_record = {
            "timestamp": datetime.now().isoformat(),
            "name": metric_name,
            "value": metric_value
        }
        self.metrics[system_name].append(metric_record)
        self._save_metrics()
        self.logger.info(f"Recorded metric '{metric_name}' for system '{system_name}'.")
        return metric_record

    def check_alerts(self, system_name: str, thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Checks the latest metrics for a system against given thresholds."""
        if not system_name in self.metrics:
            return {"status": "NO_DATA", "alerts": []}
        
        latest_metrics: Dict[str, Dict[str, Any]] = {}
        for metric in self.metrics[system_name]:
            latest_metrics[metric['name']] = metric

        alerts = []
        for metric_name, threshold in thresholds.items():
            if metric_name in latest_metrics and latest_metrics[metric_name]['value'] > threshold:
                alerts.append({
                    "metric": metric_name,
                    "value": latest_metrics[metric_name]['value'],
                    "threshold": threshold,
                    "timestamp": latest_metrics[metric_name]['timestamp']
                })
        
        status = "ALERT" if alerts else "OK"
        self.logger.info(f"Alert check for '{system_name}': {status}")
        return {"status": status, "alerts": alerts}

    def list_metrics(self, system_name: str) -> List[Dict[str, Any]]:
        """Lists all recorded metrics for a specific system."""
        return self.metrics.get(system_name, [])

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "record_metric": self.record_metric,
            "check_alerts": self.check_alerts,
            "list_metrics": self.list_metrics,
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PerformanceMonitoringTool functionality...")
    temp_dir = "temp_perf_monitor_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    monitor_tool = PerformanceMonitoringTool(data_dir=temp_dir)
    
    try:
        # --- Record some metrics ---
        print("\n--- Recording metrics for 'backend_api' ---")
        monitor_tool.execute(operation="record_metric", system_name="backend_api", metric_name="CPU_Usage", metric_value=0.55)
        monitor_tool.execute(operation="record_metric", system_name="backend_api", metric_name="Memory_Usage", metric_value=0.85)
        print("Metrics recorded.")

        # --- Check for alerts (OK scenario) ---
        print("\n--- Checking alerts with normal thresholds ---")
        alerts_ok = monitor_tool.execute(
            operation="check_alerts", system_name="backend_api", 
            thresholds={"CPU_Usage": 0.9, "Memory_Usage": 0.9}
        )
        print(f"Alert Status: {alerts_ok['status']}")

        # --- Record a high metric and check again (ALERT scenario) ---
        print("\n--- Recording high CPU usage ---")
        monitor_tool.execute(operation="record_metric", system_name="backend_api", metric_name="CPU_Usage", metric_value=0.96)
        
        print("\n--- Checking alerts with high CPU usage ---")
        alerts_cpu = monitor_tool.execute(
            operation="check_alerts", system_name="backend_api", 
            thresholds={"CPU_Usage": 0.9, "Memory_Usage": 0.9}
        )
        print(f"Alert Status: {alerts_cpu['status']}")
        print(json.dumps(alerts_cpu['alerts'], indent=2))

        # --- List all metrics for the system ---
        print("\n--- Listing all metrics for 'backend_api' ---")
        all_metrics = monitor_tool.execute(operation="list_metrics", system_name="backend_api")
        print(json.dumps(all_metrics, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")