import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DefectDetectionInManufacturingTool(BaseTool):
    """
    A tool for simulating defect detection in manufacturing.
    """

    def __init__(self, tool_name: str = "defect_detection_in_manufacturing"):
        super().__init__(tool_name)
        self.reports_file = "defect_reports.json"
        self.reports: Dict[str, Dict[str, Any]] = self._load_reports()

    @property
    def description(self) -> str:
        return "Simulates defect detection in manufacturing: inspects products, generates defect reports, and lists inspections."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The defect detection operation to perform.",
                    "enum": ["inspect_product", "generate_defect_report", "list_inspections", "get_inspection_details"]
                },
                "product_id": {"type": "string"},
                "inspection_data": {"type": "string", "description": "Data representing the product (e.g., sensor readings, image analysis results)."},
                "inspection_id": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_reports(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.reports_file):
            with open(self.reports_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted reports file '{self.reports_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_reports(self) -> None:
        with open(self.reports_file, 'w') as f:
            json.dump(self.reports, f, indent=4)

    def _inspect_product(self, product_id: str, inspection_data: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not all([product_id, inspection_data]):
            raise ValueError("Product ID and inspection data cannot be empty.")
        
        inspection_id = f"INSP-{product_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        
        has_defect = random.random() < 0.3  # nosec B311
        defect_type = None
        severity = None
        details = "No defects found."

        if has_defect:
            defect_type = random.choice(["Scratch", "Dent", "Discoloration"])  # nosec B311
            severity = random.choice(["Minor", "Moderate", "Critical"])  # nosec B311
            details = f"Detected {defect_type} with {severity} severity."

        inspection_result = {
            "inspection_id": inspection_id, "product_id": product_id,
            "inspection_data_summary": str(inspection_data)[:100],
            "has_defect": has_defect, "defect_type": defect_type, "severity": severity,
            "details": details, "inspected_at": datetime.now().isoformat()
        }
        self.reports[inspection_id] = inspection_result
        self._save_reports()
        return inspection_result

    def _generate_defect_report(self, inspection_id: str) -> Dict[str, Any]:
        report = self.reports.get(inspection_id)
        if not report: raise ValueError(f"Inspection '{inspection_id}' not found.")
        
        detailed_report = {
            "report_id": f"DEFECT_REPORT-{inspection_id}", "inspection_id": inspection_id,
            "product_id": report["product_id"], "inspection_date": report["inspected_at"],
            "overall_status": "Defective" if report["has_defect"] else "No Defects",
            "defect_details": {
                "type": report["defect_type"], "severity": report["severity"], "description": report["details"]
            } if report["has_defect"] else "N/A",
            "recommendations": "Repair or discard product." if report["has_defect"] else "Approve for shipment.",
            "generated_at": datetime.now().isoformat()
        }
        return detailed_report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "inspect_product":
            return self._inspect_product(kwargs.get("product_id"), kwargs.get("inspection_data"))
        elif operation == "generate_defect_report":
            return self._generate_defect_report(kwargs.get("inspection_id"))
        elif operation == "list_inspections":
            return list(self.reports.values())
        elif operation == "get_inspection_details":
            return self.reports.get(kwargs.get("inspection_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DefectDetectionInManufacturingTool functionality...")
    tool = DefectDetectionInManufacturingTool()
    
    try:
        print("\n--- Inspecting Product ---")
        inspection_result = tool.execute(operation="inspect_product", product_id="prod_X_001", inspection_data="sensor_data_normal_range")
        print(json.dumps(inspection_result, indent=2))
        inspection_id = inspection_result["inspection_id"]

        print("\n--- Generating Defect Report ---")
        report = tool.execute(operation="generate_defect_report", inspection_id=inspection_id)
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.reports_file): os.remove(tool.reports_file)
        print("\nCleanup complete.")