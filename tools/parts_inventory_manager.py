import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PartsInventoryManagerTool(BaseTool):
    """
    A tool for managing parts inventory, allowing for adding parts, updating
    stock levels, and generating reorder reports.
    """

    def __init__(self, tool_name: str = "PartsInventoryManager", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.parts_file = os.path.join(self.data_dir, "parts_catalog.json")
        self.inventory_file = os.path.join(self.data_dir, "parts_inventory.json")
        
        # Parts catalog: {part_id: {name: ..., description: ..., reorder_level: ...}}
        self.parts_catalog: Dict[str, Dict[str, Any]] = self._load_data(self.parts_file, default={})
        # Inventory: {part_id: {stock_level: ..., last_updated: ...}}
        self.inventory: Dict[str, Dict[str, Any]] = self._load_data(self.inventory_file, default={})

    @property
    def description(self) -> str:
        return "Manages parts inventory: add parts, update stock, get levels, and generate reorder reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_part", "update_stock", "get_stock_level", "list_parts", "generate_reorder_report"]},
                "part_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "reorder_level": {"type": "integer", "minimum": 0},
                "quantity_change": {"type": "integer", "description": "Positive for receiving, negative for issuing."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_parts_catalog(self):
        with open(self.parts_file, 'w') as f: json.dump(self.parts_catalog, f, indent=2)

    def _save_inventory(self):
        with open(self.inventory_file, 'w') as f: json.dump(self.inventory, f, indent=2)

    def add_part(self, part_id: str, name: str, description: str, reorder_level: int) -> Dict[str, Any]:
        """Adds a new part definition to the catalog."""
        if part_id in self.parts_catalog: raise ValueError(f"Part '{part_id}' already exists.")
        
        new_part = {"id": part_id, "name": name, "description": description, "reorder_level": reorder_level}
        self.parts_catalog[part_id] = new_part
        self.inventory[part_id] = {"stock_level": 0, "last_updated": datetime.now().isoformat()}
        self._save_parts_catalog()
        self._save_inventory()
        return new_part

    def update_stock(self, part_id: str, quantity_change: int) -> Dict[str, Any]:
        """Updates the stock level for a part."""
        if part_id not in self.parts_catalog: raise ValueError(f"Part '{part_id}' not found in catalog.")
        
        current_stock = self.inventory.get(part_id, {}).get("stock_level", 0)
        new_stock = current_stock + quantity_change
        
        if new_stock < 0: raise ValueError(f"Cannot reduce stock below zero for part '{part_id}'.")

        self.inventory[part_id]["stock_level"] = new_stock
        self.inventory[part_id]["last_updated"] = datetime.now().isoformat()
        self._save_inventory()
        
        reorder_needed = False
        if new_stock <= self.parts_catalog[part_id]["reorder_level"]:
            reorder_needed = True
        
        return {"status": "success", "part_id": part_id, "new_stock_level": new_stock, "reorder_needed": reorder_needed}

    def get_stock_level(self, part_id: str) -> Dict[str, Any]:
        """Retrieves the current stock level for a part."""
        if part_id not in self.parts_catalog: raise ValueError(f"Part '{part_id}' not found in catalog.")
        
        stock_info = self.inventory.get(part_id, {"stock_level": 0, "last_updated": "N/A"})
        return {"part_id": part_id, "stock_level": stock_info["stock_level"]}

    def list_parts(self) -> List[Dict[str, Any]]:
        """Lists all defined parts with their current stock levels."""
        all_parts_info = []
        for part_id, part_data in self.parts_catalog.items():
            stock_level = self.inventory.get(part_id, {}).get("stock_level", 0)
            all_parts_info.append({**part_data, "stock_level": stock_level})
        return all_parts_info

    def generate_reorder_report(self) -> List[Dict[str, Any]]:
        """Generates a report of parts that need to be reordered."""
        reorder_list = []
        for part_id, part_data in self.parts_catalog.items():
            stock_level = self.inventory.get(part_id, {}).get("stock_level", 0)
            if stock_level <= part_data["reorder_level"]:
                reorder_list.append({"part_id": part_id, "name": part_data["name"], "current_stock": stock_level, "reorder_level": part_data["reorder_level"]})
        return reorder_list

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_part": self.add_part,
            "update_stock": self.update_stock,
            "get_stock_level": self.get_stock_level,
            "list_parts": self.list_parts,
            "generate_reorder_report": self.generate_reorder_report
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PartsInventoryManagerTool functionality...")
    temp_dir = "temp_inventory_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    inventory_tool = PartsInventoryManagerTool(data_dir=temp_dir)
    
    try:
        # 1. Add some parts
        print("\n--- Adding parts to inventory ---")
        inventory_tool.execute(operation="add_part", part_id="WIDGET-A", name="Widget A", description="Standard widget", reorder_level=10)
        inventory_tool.execute(operation="add_part", part_id="SCREW-B", name="Screw B", description="Small screw", reorder_level=50)
        print("Parts added.")

        # 2. Receive initial stock
        print("\n--- Receiving initial stock ---")
        inventory_tool.execute(operation="update_stock", part_id="WIDGET-A", quantity_change=25)
        inventory_tool.execute(operation="update_stock", part_id="SCREW-B", quantity_change=100)
        print("Initial stock received.")

        # 3. Issue some parts (use)
        print("\n--- Issuing parts ---")
        inventory_tool.execute(operation="update_stock", part_id="WIDGET-A", quantity_change=-18)
        inventory_tool.execute(operation="update_stock", part_id="SCREW-B", quantity_change=-60)
        print("Parts issued.")

        # 4. Check stock levels
        print("\n--- Checking stock levels ---")
        stock_widget_a = inventory_tool.execute(operation="get_stock_level", part_id="WIDGET-A")
        stock_screw_b = inventory_tool.execute(operation="get_stock_level", part_id="SCREW-B")
        print(json.dumps(stock_widget_a, indent=2))
        print(json.dumps(stock_screw_b, indent=2))

        # 5. Generate reorder report
        print("\n--- Generating reorder report ---")
        reorder_report = inventory_tool.execute(operation="generate_reorder_report")
        print(json.dumps(reorder_report, indent=2))

        # 6. Issue more parts to trigger reorder
        print("\n--- Issuing more parts to trigger reorder for WIDGET-A ---")
        inventory_tool.execute(operation="update_stock", part_id="WIDGET-A", quantity_change=-10)
        
        print("\n--- Generating reorder report again ---")
        reorder_report_2 = inventory_tool.execute(operation="generate_reorder_report")
        print(json.dumps(reorder_report_2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")