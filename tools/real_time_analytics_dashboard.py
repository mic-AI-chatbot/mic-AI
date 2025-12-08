import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RealtimeAnalyticsDashboardSimulatorTool(BaseTool):
    """
    A tool that simulates a real-time analytics dashboard, allowing for
    creating dashboards and retrieving simulated real-time metrics.
    """

    def __init__(self, tool_name: str = "RealtimeAnalyticsDashboardSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.dashboards_file = os.path.join(self.data_dir, "analytics_dashboards.json")
        # Dashboards structure: {dashboard_name: {data_sources: [], metrics: {}}}
        self.dashboards: Dict[str, Dict[str, Any]] = self._load_data(self.dashboards_file, default={})

    @property
    def description(self) -> str:
        return "Simulates real-time analytics dashboard: create dashboards and get real-time metrics."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_dashboard", "get_dashboard_metrics"]},
                "dashboard_name": {"type": "string"},
                "data_sources": {"type": "array", "items": {"type": "string"}, "description": "List of data sources (e.g., 'web_traffic', 'sales_db', 'api_logs')."}
            },
            "required": ["operation", "dashboard_name"]
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
        with open(self.dashboards_file, 'w') as f: json.dump(self.dashboards, f, indent=2)

    def create_dashboard(self, dashboard_name: str, data_sources: List[str]) -> Dict[str, Any]:
        """Creates a new simulated analytics dashboard."""
        if dashboard_name in self.dashboards: raise ValueError(f"Dashboard '{dashboard_name}' already exists.")
        
        new_dashboard = {
            "name": dashboard_name, "data_sources": data_sources,
            "created_at": datetime.now().isoformat()
        }
        self.dashboards[dashboard_name] = new_dashboard
        self._save_data()
        return new_dashboard

    def get_dashboard_metrics(self, dashboard_name: str) -> Dict[str, Any]:
        """Retrieves simulated real-time metrics for a dashboard."""
        dashboard = self.dashboards.get(dashboard_name)
        if not dashboard: raise ValueError(f"Dashboard '{dashboard_name}' not found.")
        
        # Simulate metrics based on data sources
        current_users = random.randint(50, 500)  # nosec B311
        requests_per_second = round(random.uniform(100, 1000), 2)  # nosec B311
        error_rate_percent = round(random.uniform(0.1, 2.5), 2)  # nosec B311
        
        if "api_logs" in dashboard["data_sources"]:
            requests_per_second *= random.uniform(1.2, 1.5) # Higher traffic  # nosec B311
            error_rate_percent += random.uniform(0.5, 1.0) # More errors  # nosec B311
        if "sales_db" in dashboard["data_sources"]:
            current_users += random.randint(10, 50) # More active users  # nosec B311
        
        metrics = {
            "current_users": current_users,
            "requests_per_second": round(requests_per_second, 2),
            "error_rate_percent": round(error_rate_percent, 2),
            "last_updated": datetime.now().isoformat()
        }
        
        return {"status": "success", "dashboard_name": dashboard_name, "metrics": metrics}

    def execute(self, operation: str, dashboard_name: str, **kwargs: Any) -> Any:
        if operation == "create_dashboard":
            data_sources = kwargs.get('data_sources')
            if not data_sources:
                raise ValueError("Missing 'data_sources' for 'create_dashboard' operation.")
            return self.create_dashboard(dashboard_name, data_sources)
        elif operation == "get_dashboard_metrics":
            # No additional kwargs required for get_dashboard_metrics
            return self.get_dashboard_metrics(dashboard_name)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RealtimeAnalyticsDashboardSimulatorTool functionality...")
    temp_dir = "temp_analytics_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    dashboard_tool = RealtimeAnalyticsDashboardSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a dashboard for web traffic
        print("\n--- Creating dashboard 'WebTrafficDashboard' ---")
        dashboard_tool.execute(operation="create_dashboard", dashboard_name="WebTrafficDashboard", data_sources=["web_traffic", "cdn_logs"])
        print("Dashboard created.")

        # 2. Get real-time metrics for the web traffic dashboard
        print("\n--- Getting metrics for 'WebTrafficDashboard' ---")
        metrics1 = dashboard_tool.execute(operation="get_dashboard_metrics", dashboard_name="WebTrafficDashboard")
        print(json.dumps(metrics1, indent=2))

        # 3. Create a dashboard for API performance
        print("\n--- Creating dashboard 'APIPerformanceDashboard' ---")
        dashboard_tool.execute(operation="create_dashboard", dashboard_name="APIPerformanceDashboard", data_sources=["api_logs", "database_metrics"])
        print("Dashboard created.")

        # 4. Get real-time metrics for the API performance dashboard
        print("\n--- Getting metrics for 'APIPerformanceDashboard' ---")
        metrics2 = dashboard_tool.execute(operation="get_dashboard_metrics", dashboard_name="APIPerformanceDashboard")
        print(json.dumps(metrics2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")