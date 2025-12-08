import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProductLifecycleManagerTool(BaseTool):
    """
    A tool that simulates product lifecycle management, allowing for launching
    products, managing their phases, and retiring them.
    """

    def __init__(self, tool_name: str = "ProductLifecycleManager", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.products_file = os.path.join(self.data_dir, "product_lifecycle_records.json")
        # Products structure: {product_id: {name: ..., current_phase: ..., phase_history: [], metrics: {}}}
        self.products: Dict[str, Dict[str, Any]] = self._load_data(self.products_file, default={})

    @property
    def description(self) -> str:
        return "Simulates product lifecycle management: launch, manage phases, and retire products."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["launch_product", "update_phase", "retire_product", "get_product_status", "list_products"]},
                "product_id": {"type": "string"},
                "name": {"type": "string"},
                "initial_phase": {"type": "string", "enum": ["introduction", "growth", "maturity", "decline"]},
                "new_phase": {"type": "string", "enum": ["introduction", "growth", "maturity", "decline", "retired"]},
                "filter_phase": {"type": "string", "enum": ["introduction", "growth", "maturity", "decline", "retired"]}
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

    def _save_data(self):
        with open(self.products_file, 'w') as f: json.dump(self.products, f, indent=2)

    def launch_product(self, product_id: str, name: str, initial_phase: str = "introduction") -> Dict[str, Any]:
        """Launches a new product into its lifecycle."""
        if product_id in self.products: raise ValueError(f"Product '{product_id}' already exists.")
        
        new_product = {
            "id": product_id, "name": name, "current_phase": initial_phase,
            "phase_history": [{"phase": initial_phase, "timestamp": datetime.now().isoformat()}],
            "metrics": {"revenue": 0, "market_share": 0},
            "launched_at": datetime.now().isoformat()
        }
        self.products[product_id] = new_product
        self._save_data()
        return new_product

    def update_phase(self, product_id: str, new_phase: str) -> Dict[str, Any]:
        """Updates the lifecycle phase of a product."""
        product = self.products.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        if new_phase not in ["introduction", "growth", "maturity", "decline", "retired"]: raise ValueError(f"Invalid phase: {new_phase}.")
        
        product["current_phase"] = new_phase
        product["phase_history"].append({"phase": new_phase, "timestamp": datetime.now().isoformat()})
        
        # Simulate some metric changes based on phase
        if new_phase == "growth":
            product["metrics"]["revenue"] += random.uniform(10000, 50000)  # nosec B311
            product["metrics"]["market_share"] += random.uniform(0.01, 0.05)  # nosec B311
        elif new_phase == "decline":
            product["metrics"]["revenue"] -= random.uniform(5000, 20000)  # nosec B311
            product["metrics"]["market_share"] -= random.uniform(0.005, 0.02)  # nosec B311

        self._save_data()
        return product

    def retire_product(self, product_id: str) -> Dict[str, Any]:
        """Retires a product from its lifecycle."""
        product = self.products.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        
        product["current_phase"] = "retired"
        product["phase_history"].append({"phase": "retired", "timestamp": datetime.now().isoformat()})
        product["retired_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Product '{product_id}' has been retired."}

    def get_product_status(self, product_id: str) -> Dict[str, Any]:
        """Retrieves the current status and phase of a product."""
        product = self.products.get(product_id)
        if not product: raise ValueError(f"Product '{product_id}' not found.")
        return product

    def list_products(self, filter_phase: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all products, optionally filtered by phase."""
        filtered_list = list(self.products.values())
        if filter_phase:
            filtered_list = [p for p in filtered_list if p["current_phase"] == filter_phase]
        return filtered_list

    def execute(self, operation: str, product_id: str, **kwargs: Any) -> Any:
        if operation == "launch_product":
            name = kwargs.get('name')
            if not name:
                raise ValueError("Missing 'name' for 'launch_product' operation.")
            return self.launch_product(product_id, name, kwargs.get('initial_phase', 'introduction'))
        elif operation == "update_phase":
            new_phase = kwargs.get('new_phase')
            if not new_phase:
                raise ValueError("Missing 'new_phase' for 'update_phase' operation.")
            return self.update_phase(product_id, new_phase)
        elif operation == "retire_product":
            # No additional kwargs required for retire_product
            return self.retire_product(product_id)
        elif operation == "get_product_status":
            # No additional kwargs required for get_product_status
            return self.get_product_status(product_id)
        elif operation == "list_products":
            # filter_phase is optional, so no strict check needed here
            return self.list_products(kwargs.get('filter_phase'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProductLifecycleManagerTool functionality...")
    temp_dir = "temp_plm_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    plm_tool = ProductLifecycleManagerTool(data_dir=temp_dir)
    
    try:
        # 1. Launch a new product
        print("\n--- Launching product 'QuantumLeap' ---")
        plm_tool.execute(operation="launch_product", product_id="QuantumLeap", name="Quantum Leap Device")
        print("Product launched.")

        # 2. Update its phase to growth
        print("\n--- Updating 'QuantumLeap' phase to 'growth' ---")
        plm_tool.execute(operation="update_phase", product_id="QuantumLeap", new_phase="growth")
        print("Phase updated.")

        # 3. Get product status
        print("\n--- Getting status for 'QuantumLeap' ---")
        status = plm_tool.execute(operation="get_product_status", product_id="QuantumLeap")
        print(json.dumps(status, indent=2))

        # 4. Update its phase to decline
        print("\n--- Updating 'QuantumLeap' phase to 'decline' ---")
        plm_tool.execute(operation="update_phase", product_id="QuantumLeap", new_phase="decline")
        print("Phase updated.")

        # 5. Retire the product
        print("\n--- Retiring 'QuantumLeap' ---")
        plm_tool.execute(operation="retire_product", product_id="QuantumLeap")
        print("Product retired.")

        # 6. List all products
        print("\n--- Listing all products ---")
        all_products = plm_tool.execute(operation="list_products", product_id="any") # product_id is not used for list_products
        print(json.dumps(all_products, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")