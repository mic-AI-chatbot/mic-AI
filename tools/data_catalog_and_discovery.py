import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataCatalogAndDiscoveryTool(BaseTool):
    """
    A tool for managing a data catalog.
    """

    def __init__(self, tool_name: str = "data_catalog_and_discovery"):
        super().__init__(tool_name)
        self.catalog_file = "data_catalog.json"
        self.catalog: Dict[str, Dict[str, Any]] = self._load_catalog()

    @property
    def description(self) -> str:
        return "Manages a data catalog, allowing for cataloging, searching, and retrieving details of data assets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform.",
                    "enum": ["catalog_asset", "search_assets", "get_asset_details", "list_all_assets"]
                },
                "asset_name": {"type": "string"},
                "asset_type": {"type": "string"},
                "description": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "query": {"type": "string"},
                "search_fields": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["operation"]
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

    def _catalog_asset(self, asset_name: str, asset_type: str, description: str, tags: Optional[List[str]] = None, owner: Optional[str] = None) -> Dict[str, Any]:
        if not all([asset_name, asset_type, description]):
            raise ValueError("Asset name, type, and description are required.")
        if asset_name in self.catalog:
            raise ValueError(f"Asset '{asset_name}' already exists.")

        asset_id = f"ASSET-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_asset = {
            "asset_id": asset_id, "asset_name": asset_name, "asset_type": asset_type,
            "description": description, "tags": tags or [], "owner": owner,
            "cataloged_date": datetime.now().isoformat()
        }
        self.catalog[asset_name] = new_asset
        self._save_catalog()
        return new_asset

    def _search_assets(self, query: str, search_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not query: return []
        query_lower = query.lower()
        results = []
        search_fields = search_fields or ['asset_name', 'description', 'tags']

        for asset_details in self.catalog.values():
            for field in search_fields:
                if field == 'tags':
                    if any(query_lower in tag.lower() for tag in asset_details.get('tags', [])):
                        results.append(asset_details)
                        break
                elif field in asset_details and isinstance(asset_details[field], str):
                    if query_lower in asset_details[field].lower():
                        results.append(asset_details)
                        break
        return results

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "catalog_asset":
            return self._catalog_asset(kwargs.get("asset_name"), kwargs.get("asset_type"), kwargs.get("description"), kwargs.get("tags"), kwargs.get("owner"))
        elif operation == "search_assets":
            query = kwargs.get("query")
            if not query: raise ValueError("'query' is required for search.")
            return self._search_assets(query, kwargs.get("search_fields"))
        elif operation == "get_asset_details":
            asset_name = kwargs.get("asset_name")
            if not asset_name: raise ValueError("'asset_name' is required.")
            return self.catalog.get(asset_name)
        elif operation == "list_all_assets":
            return list(self.catalog.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataCatalogAndDiscoveryTool functionality...")
    tool = DataCatalogAndDiscoveryTool()
    
    try:
        print("\n--- Cataloging Assets ---")
        tool.execute(operation="catalog_asset", asset_name="Customer_Table", asset_type="db_table", description="Customer demographic data.", tags=["pii", "customer"])
        tool.execute(operation="catalog_asset", asset_name="Sales_API", asset_type="api", description="Endpoint for sales data.", tags=["finance", "api"])
        
        print("\n--- Listing All Assets ---")
        all_assets = tool.execute(operation="list_all_assets")
        print(json.dumps(all_assets, indent=2))

        print("\n--- Searching for 'customer' ---")
        customer_assets = tool.execute(operation="search_assets", query="customer")
        print(json.dumps(customer_assets, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.catalog_file):
            os.remove(tool.catalog_file)
        print("\nCleanup complete.")