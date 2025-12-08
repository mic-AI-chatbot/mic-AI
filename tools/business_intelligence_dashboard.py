import logging
import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class KPIDataGenerator:
    """Generates mock sales data and calculates KPIs from it."""
    def generate_sales_data(self, num_months: int = 12) -> pd.DataFrame:
        dates = pd.date_range(start="2024-01-01", periods=num_months, freq="MS")
        base_sales = np.linspace(100000, 200000, num_months) + np.random.normal(0, 10000, num_months)
        
        # Add some seasonality (e.g., higher sales in certain months)
        seasonal_factor = np.sin(np.linspace(0, 2 * np.pi, num_months)) * 30000
        sales = base_sales + seasonal_factor
        
        df = pd.DataFrame({"date": dates, "sales": sales.round(2)})
        return df

    def calculate_kpis(self, df: pd.DataFrame) -> Dict[str, float]:
        total_sales = df["sales"].sum()
        avg_monthly_sales = df["sales"].mean()
        
        # Simulate other KPIs (these could also be derived from more complex data)
        conversion_rate = random.uniform(1.0, 5.0)  # nosec B311
        customer_acquisition_cost = random.uniform(50, 200)  # nosec B311
        
        return {
            "total_sales": round(total_sales, 2),
            "average_monthly_sales": round(avg_monthly_sales, 2),
            "conversion_rate_percent": round(conversion_rate, 2),
            "customer_acquisition_cost": round(customer_acquisition_cost, 2)
        }

kpi_data_generator = KPIDataGenerator()

class GetKPIsTool(BaseTool):
    """Retrieves key performance indicators (KPIs) for a business."""
    def __init__(self, tool_name="get_kpis"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves key performance indicators (KPIs) for a business, such as total sales, conversion rate, or customer acquisition cost, calculated from simulated data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "kpi_name": {"type": "string", "description": "The name of the KPI to retrieve (e.g., 'total_sales', 'conversion_rate_percent'). Use 'all' to get all available KPIs.", "default": "all"},
                "num_months_data": {"type": "integer", "description": "Number of months of simulated data to use for KPI calculation.", "default": 12}
            },
            "required": []
        }

    def execute(self, kpi_name: str = "all", num_months_data: int = 12, **kwargs: Any) -> str:
        df = kpi_data_generator.generate_sales_data(num_months_data)
        kpis = kpi_data_generator.calculate_kpis(df)
        
        if kpi_name == "all":
            return json.dumps(kpis, indent=2)
        elif kpi_name in kpis:
            return json.dumps({kpi_name: kpis[kpi_name]}, indent=2)
        else:
            return json.dumps({"error": f"KPI '{kpi_name}' not found. Available KPIs: {', '.join(kpis.keys())}."})

class GenerateDashboardTool(BaseTool):
    """Generates a business intelligence dashboard with specified KPIs and visualization types."""
    def __init__(self, tool_name="generate_dashboard"):
        super().__init__(tool_name=tool_name)
        self.get_kpis_tool = GetKPIsTool()

    @property
    def description(self) -> str:
        return "Generates a business intelligence dashboard with specified KPIs and visualization types, saving the visualization to a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dashboard_name": {"type": "string", "description": "The name of the dashboard to generate."},
                "kpis_to_display": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["total_sales", "average_monthly_sales", "conversion_rate_percent", "customer_acquisition_cost"]},
                    "description": "A list of KPIs to display on the dashboard."
                },
                "visualization_type": {"type": "string", "description": "The type of visualization.", "enum": ["bar_chart", "line_graph"], "default": "bar_chart"},
                "output_path": {"type": "string", "description": "The absolute path to save the generated dashboard image (e.g., 'dashboard.png')."}
            },
            "required": ["dashboard_name", "kpis_to_display", "output_path"]
        }

    def execute(self, dashboard_name: str, kpis_to_display: List[str], visualization_type: str = "bar_chart", output_path: str = "dashboard.png", **kwargs: Any) -> str:
        kpis_json = self.get_kpis_tool.execute(kpi_name="all")
        all_kpis = json.loads(kpis_json)
        
        data_for_chart = {kpi: all_kpis.get(kpi) for kpi in kpis_to_display if kpi in all_kpis}
        
        if not data_for_chart:
            return json.dumps({"error": "No valid KPIs selected for display or KPIs not found."})

        try:
            plt.figure(figsize=(10, 6))
            if visualization_type == "bar_chart":
                plt.bar(data_for_chart.keys(), data_for_chart.values(), color='skyblue')
                plt.ylabel("Value")
            elif visualization_type == "line_graph":
                plt.plot(data_for_chart.keys(), data_for_chart.values(), marker='o', linestyle='-')
                plt.ylabel("Value")
            
            plt.title(f"{dashboard_name} - Key Performance Indicators")
            plt.xlabel("KPI")
            plt.xticks(rotation=45, ha="right")
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            plt.tight_layout()
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close() # Close the plot to free memory
            
            report = {
                "message": f"Dashboard '{dashboard_name}' generated and saved to '{os.path.abspath(output_path)}'.",
                "file_path": os.path.abspath(output_path)
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return json.dumps({"error": f"Error generating dashboard: {e}"})