import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataCatalogManagerTool(BaseTool):
    """
    A tool for managing a data catalog.
    """

    def __init__(self, tool_name: str = "data_catalog_manager"):
        super().__init__(tool_name)
        self.catalog_file = "simple_data_catalog.json"
        self.catalog: Dict[str, Dict[str, Any]] = self._load_catalog()

    @property
    def description(self) -> str:
        return "Manages a simple data catalog, allowing for asset registration and retrieval of details."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform.",
                    "enum": ["register_asset", "get_asset_details"]
                },
                "asset_name": {"type": "string"},
                "asset_type": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["operation", "asset_name"]
        }

    def _load_catalog(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.catalog_file):
            with open(self.catalog_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted catalog file '{self.catalog_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_catalog(self) -> None:
        with open(self.catalog_file, 'w') as f:
            json.dump(self.catalog, f, indent=4)

    def _register_asset(self, asset_name: str, asset_type: str, description: str) -> Dict[str, Any]:
        if not all([asset_name, asset_type, description]):
            raise ValueError("Asset name, type, and description are required.")
        if asset_name in self.catalog:
            raise ValueError(f"Asset '{asset_name}' already exists.")

        asset_id = f"SIMPLE-ASSET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_asset = {
            "asset_id": asset_id, "asset_name": asset_name, "asset_type": asset_type,
            "description": description, "registered_date": datetime.now().isoformat()
        }
        self.catalog[asset_name] = new_asset
        self._save_catalog()
        return new_asset

    def execute(self, operation: str, asset_name: str, **kwargs: Any) -> Any:
        if operation == "register_asset":
            asset_type = kwargs.get("asset_type")
            description = kwargs.get("description")
            if not all([asset_type, description]):
                raise ValueError("'asset_type' and 'description' are required for registration.")
            return self._register_asset(asset_name, asset_type, description)
        elif operation == "get_asset_details":
            return self.catalog.get(asset_name)
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataCatalogManagerTool functionality...")
    tool = DataCatalogManagerTool()
    
    try:
        print("\n--- Registering Assets ---")
        tool.execute(operation="register_asset", asset_name="Customer_DB", asset_type="database", description="Customer demographic data.")
        
        print("\n--- Getting Asset Details ---")
        details = tool.execute(operation="get_asset_details", asset_name="Customer_DB")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.catalog_file):
            os.remove(tool.catalog_file)
        print("\nCleanup complete.")