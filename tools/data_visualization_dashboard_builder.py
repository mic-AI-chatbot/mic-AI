import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataVisualizationDashboardBuilderTool(BaseTool):
    """
    A tool for simulating the creation and management of data visualization dashboards.
    """

    def __init__(self, tool_name: str = "data_visualization_dashboard_builder"):
        super().__init__(tool_name)
        self.dashboards_file = "dashboards.json"
        self.dashboards: Dict[str, Dict[str, Any]] = self._load_dashboards()

    @property
    def description(self) -> str:
        return "Simulates creating and managing data visualization dashboards, including generating HTML representations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The dashboard operation to perform.",
                    "enum": ["create_dashboard", "generate_dashboard_html", "list_dashboards", "get_dashboard_details"]
                },
                "dashboard_id": {"type": "string"},
                "dashboard_name": {"type": "string"},
                "layout": {"type": "array", "items": {"type": "object"}},
                "data_sources": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"},
                "output_file": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_dashboards(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.dashboards_file):
            with open(self.dashboards_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted dashboards file '{self.dashboards_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_dashboards(self) -> None:
        with open(self.dashboards_file, 'w') as f:
            json.dump(self.dashboards, f, indent=4)

    def _create_dashboard(self, dashboard_id: str, dashboard_name: str, layout: List[Dict[str, Any]], data_sources: List[str], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([dashboard_id, dashboard_name, layout, data_sources]):
            raise ValueError("Dashboard ID, name, layout, and data sources cannot be empty.")
        if dashboard_id in self.dashboards:
            raise ValueError(f"Dashboard '{dashboard_id}' already exists.")

        new_dashboard = {
            "dashboard_id": dashboard_id, "dashboard_name": dashboard_name, "layout": layout,
            "data_sources": data_sources, "description": description, "created_at": datetime.now().isoformat()
        }
        self.dashboards[dashboard_id] = new_dashboard
        self._save_dashboards()
        return new_dashboard

    def _generate_dashboard_html(self, dashboard_id: str, output_file: str) -> str:
        dashboard = self.dashboards.get(dashboard_id)
        if not dashboard: raise ValueError(f"Dashboard '{dashboard_id}' not found.")

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dashboard['dashboard_name']} Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }}
        .dashboard-container {{ max-width: 1200px; margin: auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; text-align: center; }}
        .description {{ text-align: center; color: #666; margin-bottom: 30px; }}
        .grid-container {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .chart-card {{ background: #fff; border: 1px solid #ddd; border-radius: 5px; padding: 15px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .chart-card h2 {{ margin-top: 0; color: #555; font-size: 1.2em; }}
        .placeholder {{ background-color: #e0e0e0; height: 150px; display: flex; align-items: center; justify-content: center; color: #888; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <h1>{dashboard['dashboard_name']}</h1>
        <p class="description">{dashboard.get('description', 'No description provided.')}</p>
        <div class="grid-container">
"""
        for item in dashboard['layout']:
            html_content += f"""
            <div class="chart-card">
                <h2>{item.get('title', 'Untitled Chart')}</h2>
                <div class="placeholder">
                    Simulated {item.get('type', 'Visualization')} for {item.get('data_field', 'Data')}
                </div>
                <p>Data Source: {', '.join(dashboard['data_sources'])}</p>
            </div>
"""
        html_content += """
        </div>
    </div>
</body>
</html>
"""
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        with open(output_file, 'w') as f: f.write(html_content)
        return f"Dashboard HTML generated at '{output_file}'."

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_dashboard":
            return self._create_dashboard(kwargs.get("dashboard_id"), kwargs.get("dashboard_name"), kwargs.get("layout"), kwargs.get("data_sources"), kwargs.get("description"))
        elif operation == "generate_dashboard_html":
            return self._generate_dashboard_html(kwargs.get("dashboard_id"), kwargs.get("output_file"))
        elif operation == "list_dashboards":
            return [{k: v for k, v in dash.items() if k != "layout"} for dash in self.dashboards.values()]
        elif operation == "get_dashboard_details":
            return self.dashboards.get(kwargs.get("dashboard_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataVisualizationDashboardBuilderTool functionality...")
    tool = DataVisualizationDashboardBuilderTool()
    
    output_html_dir = "generated_dashboards"
    
    try:
        os.makedirs(output_html_dir, exist_ok=True)

        print("\n--- Creating Dashboard ---")
        tool.execute(operation="create_dashboard", dashboard_id="sales_overview", dashboard_name="Sales Performance Overview", layout=[{"type": "bar_chart", "data_field": "revenue", "title": "Revenue by Product"}], data_sources=["sales_db"], description="Key metrics for sales team performance.")
        
        print("\n--- Generating Dashboard HTML ---")
        output_html_file = os.path.join(output_html_dir, "sales_overview.html")
        html_message = tool.execute(operation="generate_dashboard_html", dashboard_id="sales_overview", output_file=output_html_file)
        print(html_message)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.dashboards_file): os.remove(tool.dashboards_file)
        if os.path.exists(output_html_dir): shutil.rmtree(output_html_dir)
        print("\nCleanup complete.")
