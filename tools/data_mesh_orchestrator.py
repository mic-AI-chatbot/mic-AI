import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataMeshOrchestratorTool(BaseTool):
    """
    A tool for orchestrating a data mesh, allowing for the definition,
    discovery, and management of data products.
    """

    def __init__(self, tool_name: str = "data_mesh_orchestrator"):
        super().__init__(tool_name)
        self.data_products_file = "data_products.json"
        self.data_products: Dict[str, Dict[str, Any]] = self._load_data_products()

    @property
    def description(self) -> str:
        return "Orchestrates a data mesh, enabling definition, discovery, and management of data products."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data mesh operation to perform.",
                    "enum": ["define_data_product", "discover_data_products", "get_data_product_details", "list_all_data_products"]
                },
                "product_id": {"type": "string"},
                "product_name": {"type": "string"},
                "domain": {"type": "string"},
                "data_assets": {"type": "array", "items": {"type": "string"}},
                "owner": {"type": "string"},
                "description": {"type": "string"},
                "query": {"type": "string"},
                "search_fields": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["operation"]
        }

    def _load_data_products(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.data_products_file):
            with open(self.data_products_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted data products file '{self.data_products_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_data_products(self) -> None:
        with open(self.data_products_file, 'w') as f:
            json.dump(self.data_products, f, indent=4)

    def _define_data_product(self, product_id: str, product_name: str, domain: str, data_assets: List[str], owner: Optional[str] = None, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([product_id, product_name, domain, data_assets]):
            raise ValueError("Product ID, name, domain, and data assets cannot be empty.")
        if product_id in self.data_products:
            raise ValueError(f"Data product '{product_id}' already exists.")

        new_product = {
            "product_id": product_id, "product_name": product_name, "domain": domain,
            "data_assets": data_assets, "owner": owner, "description": description,
            "defined_at": datetime.now().isoformat()
        }
        self.data_products[product_id] = new_product
        self._save_data_products()
        return new_product

    def _discover_data_products(self, query: str, search_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        if not query: return []
        query_lower = query.lower()
        results = []
        search_fields = search_fields or ['product_name', 'domain', 'description', 'data_assets']

        for product_details in self.data_products.values():
            for field in search_fields:
                if field == 'data_assets':
                    if any(query_lower in asset.lower() for asset in product_details.get('data_assets', [])):
                        results.append(product_details)
                        break
                elif field in product_details and isinstance(product_details[field], str):
                    if query_lower in product_details[field].lower():
                        results.append(product_details)
                        break
        return results

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_data_product":
            return self._define_data_product(kwargs.get("product_id"), kwargs.get("product_name"), kwargs.get("domain"), kwargs.get("data_assets"), kwargs.get("owner"), kwargs.get("description"))
        elif operation == "discover_data_products":
            query = kwargs.get("query")
            if not query: raise ValueError("'query' is required for discovery.")
            return self._discover_data_products(query, kwargs.get("search_fields"))
        elif operation == "get_data_product_details":
            product_id = kwargs.get("product_id")
            if not product_id: raise ValueError("'product_id' is required.")
            return self.data_products.get(product_id)
        elif operation == "list_all_data_products":
            return list(self.data_products.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataMeshOrchestratorTool functionality...")
    tool = DataMeshOrchestratorTool()
    
    try:
        print("\n--- Defining Data Products ---")
        tool.execute(operation="define_data_product", product_id="customer_360", product_name="Customer 360 View", domain="sales", data_assets=["customer_db_table"])
        
        print("\n--- Discovering Data Products ---")
        discovered_products = tool.execute(operation="discover_data_products", query="customer", search_fields=["product_name"])
        print(json.dumps(discovered_products, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.data_products_file):
            os.remove(tool.data_products_file)
        print("\nCleanup complete.")