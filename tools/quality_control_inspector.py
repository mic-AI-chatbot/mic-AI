import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class QualityControlInspectorSimulatorTool(BaseTool):
    """
    A tool that simulates quality control inspection, allowing for defining
    products, inspecting them based on criteria, and generating quality reports.
    """

    def __init__(self, tool_name: str = "QualityControlInspectorSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.products_file = os.path.join(self.data_dir, "product_definitions.json")
        self.inspections_file = os.path.join(self.data_dir, "inspection_records.json")
        
        # Product definitions: {product_id: {name: ..., specifications: {}, quality_criteria: {}}}
        self.product_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.products_file, default={})
        # Inspection records: {inspection_id: {product_id: ..., type: ..., defects: [], grade: ...}}
        self.inspection_records: Dict[str, Dict[str, Any]] = self._load_data(self.inspections_file, default={})

    @property
    def description(self) -> str:
        return "Simulates quality control inspection: inspects products and generates quality reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_product", "inspect_product", "generate_report", "list_products"]},
                "product_id": {"type": "string"},
                "name": {"type": "string"},
                "specifications": {"type": "object", "description": "e.g., {'dimensions': '10x10x10', 'material': 'steel'}"},
                "quality_criteria": {"type": "object", "description": "e.g., {'visual': 'no scratches', 'functional': 'passes power-on test'}"},
                "inspection_type": {"type": "string", "enum": ["visual", "functional", "dimensional"]},
                "test_id": {"type": "string", "description": "ID of the inspection record to generate report for."}
            },
            "required": ["operation", "product_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_products(self):
        with open(self.products_file, 'w') as f: json.dump(self.product_definitions, f, indent=2)

    def _save_inspections(self):
        with open(self.inspections_file, 'w') as f: json.dump(self.inspection_records, f, indent=2)

    def define_product(self, product_id: str, name: str, specifications: Dict[str, Any], quality_criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Defines a new product with its specifications and quality criteria."""
        if product_id in self.product_definitions: raise ValueError(f"Product '{product_id}' already exists.")
        
        new_product = {
            "id": product_id, "name": name, "specifications": specifications,
            "quality_criteria": quality_criteria, "defined_at": datetime.now().isoformat()
        }
        self.product_definitions[product_id] = new_product
        self._save_products()
        return new_product

    def inspect_product(self, product_id: str, inspection_type: str) -> Dict[str, Any]:
        """Simulates inspecting a product based on its quality criteria."""
        product = self.product_definitions.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        inspection_id = f"insp_{product_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        defects_found = []
        overall_grade = "pass"
        
        # Simulate defects based on inspection type and some randomness
        if inspection_type == "visual":
            if random.random() < 0.3: defects_found.append("minor scratch")  # nosec B311
            if random.random() < 0.1: defects_found.append("paint chip")  # nosec B311
        elif inspection_type == "functional":
            if random.random() < 0.2: defects_found.append("power-on failure")  # nosec B311
            if random.random() < 0.1: defects_found.append("button malfunction")  # nosec B311
        elif inspection_type == "dimensional":
            if random.random() < 0.15: defects_found.append("dimension out of tolerance")  # nosec B311
        
        if defects_found: overall_grade = "fail"
        
        new_inspection = {
            "id": inspection_id, "product_id": product_id, "inspection_type": inspection_type,
            "defects_found": defects_found, "overall_grade": overall_grade,
            "inspected_at": datetime.now().isoformat()
        }
        self.inspection_records[inspection_id] = new_inspection
        self._save_inspections()
        return new_inspection

    def generate_report(self, product_id: str) -> Dict[str, Any]:
        """Generates a quality report for a product."""
        product = self.product_definitions.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        related_inspections = [insp for insp in self.inspection_records.values() if insp["product_id"] == product_id]
        
        report_lines = [
            f"--- Quality Report for: {product['name']} ({product_id}) ---",
            f"Specifications: {json.dumps(product['specifications'])}",
            f"Quality Criteria: {json.dumps(product['quality_criteria'])}",
            "\n--- Inspection History ---"
        ]
        
        if related_inspections:
            for insp in related_inspections:
                report_lines.append(f"\nInspection ID: {insp['id']} (Type: {insp['inspection_type']}, Grade: {insp['overall_grade']})")
                if insp["defects_found"]:
                    report_lines.append(f"  Defects: {', '.join(insp['defects_found'])}")
                else:
                    report_lines.append("  No defects found.")
        else:
            report_lines.append("No inspection records found.")
        
        return {"status": "success", "product_id": product_id, "report": "\n".join(report_lines)}

    def list_products(self) -> List[Dict[str, Any]]:
        """Lists all defined products."""
        return list(self.product_definitions.values())

    def execute(self, operation: str, product_id: str, **kwargs: Any) -> Any:
        if operation == "define_product":
            name = kwargs.get('name')
            specifications = kwargs.get('specifications')
            quality_criteria = kwargs.get('quality_criteria')
            if not all([name, specifications, quality_criteria]):
                raise ValueError("Missing 'name', 'specifications', or 'quality_criteria' for 'define_product' operation.")
            return self.define_product(product_id, name, specifications, quality_criteria)
        elif operation == "inspect_product":
            inspection_type = kwargs.get('inspection_type')
            if not inspection_type:
                raise ValueError("Missing 'inspection_type' for 'inspect_product' operation.")
            return self.inspect_product(product_id, inspection_type)
        elif operation == "generate_report":
            # No additional kwargs required for generate_report
            return self.generate_report(product_id)
        elif operation == "list_products":
            # No additional kwargs required for list_products
            return self.list_products()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating QualityControlInspectorSimulatorTool functionality...")
    temp_dir = "temp_qc_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    qc_tool = QualityControlInspectorSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a product
        print("\n--- Defining product 'Widget_Pro' ---")
        qc_tool.execute(operation="define_product", product_id="WIDGET-PRO", name="Widget Pro",
                        specifications={"dimensions": "10x5x2cm", "material": "aluminum"},
                        quality_criteria={"visual": "no scratches", "functional": "passes power-on test"})
        print("Product defined.")

        # 2. Inspect the product (visual)
        print("\n--- Inspecting 'WIDGET-PRO' (visual) ---")
        visual_inspection = qc_tool.execute(operation="inspect_product", product_id="WIDGET-PRO", inspection_type="visual")
        print(json.dumps(visual_inspection, indent=2))

        # 3. Inspect the product (functional)
        print("\n--- Inspecting 'WIDGET-PRO' (functional) ---")
        functional_inspection = qc_tool.execute(operation="inspect_product", product_id="WIDGET-PRO", inspection_type="functional")
        print(json.dumps(functional_inspection, indent=2))

        # 4. Generate a report
        print("\n--- Generating report for 'WIDGET-PRO' ---")
        report = qc_tool.execute(operation="generate_report", product_id="WIDGET-PRO")
        print(report["report"])

        # 5. List all products
        print("\n--- Listing all products ---")
        all_products = qc_tool.execute(operation="list_products", product_id="any") # product_id is not used for list_products
        print(json.dumps(all_products, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")