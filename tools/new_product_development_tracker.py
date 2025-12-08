import logging
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NewProductDevelopmentTrackerTool(BaseTool):
    """
    A tool for tracking the development lifecycle of new products,
    allowing for creation, status updates, and progress reporting.
    """

    def __init__(self, tool_name: str = "NewProductDevelopmentTracker", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.products_file = os.path.join(self.data_dir, "products.json")
        # Products structure: {product_name: {description: ..., status: ..., history: []}}
        self.products: Dict[str, Dict[str, Any]] = self._load_data(self.products_file, default={})

    @property
    def description(self) -> str:
        return "Tracks new product development: create, update status, and generate progress reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_product", "update_status", "generate_report", "list_products"]},
                "product_name": {"type": "string"},
                "description": {"type": "string"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "target_launch_date": {"type": "string", "description": "YYYY-MM-DD"},
                "new_status": {"type": "string", "enum": ["ideation", "development", "testing", "launch", "paused", "cancelled"]}
            },
            "required": ["operation", "product_name"]
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
        with open(self.products_file, 'w') as f: json.dump(self.products, f, indent=2)

    def create_product(self, product_name: str, description: str, start_date: str, target_launch_date: str) -> Dict[str, Any]:
        """Creates a new product record."""
        if product_name in self.products: raise ValueError(f"Product '{product_name}' already exists.")
        
        new_product = {
            "name": product_name, "description": description,
            "start_date": start_date, "target_launch_date": target_launch_date,
            "current_status": "ideation", "status_history": [],
            "created_at": datetime.now().isoformat()
        }
        new_product["status_history"].append({"status": "ideation", "timestamp": datetime.now().isoformat()})
        self.products[product_name] = new_product
        self._save_data()
        return new_product

    def update_status(self, product_name: str, new_status: str) -> Dict[str, Any]:
        """Updates the status of a product."""
        product = self.products.get(product_name)
        if not product: raise ValueError(f"Product '{product_name}' not found.")
        
        product["current_status"] = new_status
        product["status_history"].append({"status": new_status, "timestamp": datetime.now().isoformat()})
        self._save_data()
        return product

    def generate_report(self, product_name: str) -> Dict[str, Any]:
        """Generates a progress report for a product."""
        product = self.products.get(product_name)
        if not product: raise ValueError(f"Product '{product_name}' not found.")
        
        start_dt = datetime.fromisoformat(product["start_date"])
        target_dt = datetime.fromisoformat(product["target_launch_date"])
        now = datetime.now()

        total_duration = (target_dt - start_dt).days
        elapsed_duration = (now - start_dt).days
        
        progress_percent = min(100, max(0, round((elapsed_duration / total_duration) * 100))) if total_duration > 0 else 0
        
        report = {
            "product_name": product_name,
            "current_status": product["current_status"],
            "progress_percent": progress_percent,
            "days_remaining": max(0, (target_dt - now).days),
            "status_history": product["status_history"]
        }
        return report

    def list_products(self) -> List[Dict[str, Any]]:
        """Lists all tracked products."""
        return list(self.products.values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_product": self.create_product,
            "update_status": self.update_status,
            "generate_report": self.generate_report,
            "list_products": self.list_products
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating NewProductDevelopmentTrackerTool functionality...")
    temp_dir = "temp_product_tracker_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    tracker_tool = NewProductDevelopmentTrackerTool(data_dir=temp_dir)
    
    try:
        # 1. Create a new product
        print("\n--- Creating new product 'Quantum Leap Device' ---")
        tracker_tool.execute(
            operation="create_product", product_name="Quantum Leap Device",
            description="A device for instantaneous teleportation.",
            start_date="2025-01-01", target_launch_date="2025-12-31"
        )
        print("Product created.")

        # 2. Update its status
        print("\n--- Updating status to 'development' ---")
        tracker_tool.execute(operation="update_status", product_name="Quantum Leap Device", new_status="development")
        print("Status updated.")

        # 3. Generate a report
        print("\n--- Generating report for 'Quantum Leap Device' ---")
        report = tracker_tool.execute(operation="generate_report", product_name="Quantum Leap Device")
        print(json.dumps(report, indent=2))

        # 4. List all products
        print("\n--- Listing all products ---")
        all_products = tracker_tool.execute(operation="list_products")
        print(json.dumps(all_products, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")