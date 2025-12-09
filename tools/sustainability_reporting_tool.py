import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SustainabilityReportingTool(BaseTool):
    """
    A tool that generates sustainability reports based on input data.
    """

    def __init__(self, tool_name: str = "SustainabilityReportingTool", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "sustainability_reports.json")
        
        # Reports: {report_id: {sustainability_data: {}, generated_report: ""}}
        self.generated_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Generates sustainability reports based on input data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_sustainability_report", "get_report"]},
                "report_id": {"type": "string"},
                "sustainability_data": {
                    "type": "object",
                    "description": "A dictionary containing sustainability metrics, e.g., {'reporting_period': '2025-Q3', 'carbon_footprint': {'total_tonnes_co2e': 1500}}."
                }
            },
            "required": ["operation", "report_id"]
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
        with open(self.reports_file, 'w') as f: json.dump(self.generated_reports, f, indent=2)

    def generate_sustainability_report(self, report_id: str, sustainability_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a sustainability report based on input data.
        """
        if report_id in self.generated_reports: raise ValueError(f"Report '{report_id}' already exists.")

        report_content = f"""Sustainability Report: {sustainability_data.get('reporting_period', 'N/A')}\n"""
        report_content += "=" * 40 + "\n"

        # Carbon Footprint
        carbon_data = sustainability_data.get('carbon_footprint', {})
        if carbon_data:
            report_content += "\n--- Carbon Footprint ---\n"
            report_content += f"Total Emissions: {carbon_data.get('total_tonnes_co2e', 'N/A')} tonnes CO2e\n"
            if 'previous_period' in carbon_data and carbon_data.get('total_tonnes_co2e') is not None:
                change = carbon_data['total_tonnes_co2e'] - carbon_data['previous_period']
                percentage_change = (change / carbon_data['previous_period']) * 100 if carbon_data['previous_period'] != 0 else 0
                report_content += f"Change from previous period: {change} tonnes ({percentage_change:.2f}%)\n"

        # Water Usage
        water_data = sustainability_data.get('water_usage', {})
        if water_data:
            report_content += "\n--- Water Usage ---\n"
            report_content += f"Total Consumption: {water_data.get('total_m3', 'N/A')} m3\n"
            if 'previous_period' in water_data and water_data.get('total_m3') is not None:
                change = water_data['total_m3'] - water_data['previous_period']
                percentage_change = (change / water_data['previous_period']) * 100 if water_data['previous_period'] != 0 else 0
                report_content += f"Change from previous period: {change} m3 ({percentage_change:.2f}%)\n"

        # Waste Generation
        waste_data = sustainability_data.get('waste_generation', {})
        if waste_data:
            report_content += "\n--- Waste Generation ---\n"
            report_content += f"Total Waste: {waste_data.get('total_tonnes', 'N/A')} tonnes\n"
            if 'recycled_tonnes' in waste_data and waste_data.get('total_tonnes') is not None:
                recycling_rate = (waste_data['recycled_tonnes'] / waste_data['total_tonnes']) * 100 if waste_data['total_tonnes'] != 0 else 0
                report_content += f"Recycled: {waste_data['recycled_tonnes']} tonnes ({recycling_rate:.2f}% recycling rate)\n"
            if 'previous_period' in waste_data and waste_data.get('total_tonnes') is not None:
                change = waste_data['total_tonnes'] - waste_data['previous_period']
                percentage_change = (change / waste_data['previous_period']) * 100 if waste_data['previous_period'] != 0 else 0
                report_content += f"Change from previous period: {change} tonnes ({percentage_change:.2f}%)\n"

        report_content += "\n" + "=" * 40 + "\n"
        report_content += "End of Report\n"

        new_report = {
            "id": report_id, "sustainability_data": sustainability_data,
            "generated_report": report_content, "generated_at": datetime.now().isoformat()
        }
        self.generated_reports[report_id] = new_report
        self._save_data()
        return new_report

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated sustainability report."""
        report = self.generated_reports.get(report_id)
        if not report: raise ValueError(f"Sustainability report '{report_id}' not found.")
        return report

    def execute(self, operation: str, report_id: str, **kwargs: Any) -> Any:
        if operation == "generate_sustainability_report":
            sustainability_data = kwargs.get('sustainability_data')
            if not sustainability_data:
                raise ValueError("Missing 'sustainability_data' for 'generate_sustainability_report' operation.")
            return self.generate_sustainability_report(report_id, sustainability_data)
        elif operation == "get_report":
            # No additional kwargs required for get_report
            return self.get_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SustainabilityReportingTool functionality...")
    temp_dir = "temp_sustainability_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    reporting_tool = SustainabilityReportingTool(data_dir=temp_dir)
    
    try:
        # 1. Generate a sustainability report
        print("\n--- Generating Sustainability Report 'Q3_2025_Report' ---")
        sustainability_data = {
            'reporting_period': '2025-Q3',
            'carbon_footprint': {'total_tonnes_co2e': 1500, 'previous_period': 1600},
            'water_usage': {'total_m3': 5000, 'previous_period': 5200},
            'waste_generation': {'total_tonnes': 120, 'recycled_tonnes': 80, 'previous_period': 125}
        }
        report_result = reporting_tool.execute(operation="generate_sustainability_report", report_id="Q3_2025_Report", sustainability_data=sustainability_data)
        print(json.dumps(report_result, indent=2))

        # 2. Get the report
        print(f"\n--- Getting report for '{report_result['id']}' ---")
        retrieved_report = reporting_tool.execute(operation="get_report", report_id=report_result["id"])
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")