import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MetadataCatalogTool(BaseTool):
    """
    A tool for managing a data catalog by creating, updating, versioning,
    and searching for metadata assets.
    """

    def __init__(self, tool_name: str = "MetadataCatalog", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.catalog_file = os.path.join(self.data_dir, "metadata_catalog.json")
        # Catalog structure: {metadata_type: {metadata_id: content}}
        self.catalog: Dict[str, Dict[str, Any]] = self._load_data(self.catalog_file, default={})

    @property
    def description(self) -> str:
        return "Manages a data catalog, allowing creation, versioning, and searching of metadata."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create", "get", "update", "delete", "search"]},
                "metadata_type": {"type": "string", "description": "e.g., 'table', 'report', 'column'"},
                "metadata_id": {"type": "string"},
                "metadata_content": {"type": "object", "description": "The actual metadata attributes."},
                "search_query": {"type": "string"}
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

    def _save_data(self):
        with open(self.catalog_file, 'w') as f: json.dump(self.catalog, f, indent=2)

    def _create(self, metadata_type: str, metadata_id: str, metadata_content: Dict) -> Dict:
        if metadata_type not in self.catalog: self.catalog[metadata_type] = {}
        if metadata_id in self.catalog[metadata_type]:
            raise ValueError(f"Metadata asset '{metadata_id}' of type '{metadata_type}' already exists.")
        
        metadata_content.update({
            "_createdAt": datetime.now().isoformat(),
            "_version": 1
        })
        self.catalog[metadata_type][metadata_id] = metadata_content
        self._save_data()
        return self.catalog[metadata_type][metadata_id]

    def _get(self, metadata_type: str, metadata_id: str) -> Dict:
        return self.catalog.get(metadata_type, {}).get(metadata_id)

    def _update(self, metadata_type: str, metadata_id: str, metadata_content: Dict) -> Dict:
        asset = self._get(metadata_type, metadata_id)
        if not asset: raise ValueError(f"Metadata asset '{metadata_id}' not found.")
        
        asset.update(metadata_content)
        asset["_lastUpdatedAt"] = datetime.now().isoformat()
        asset["_version"] = asset.get("_version", 1) + 1
        self._save_data()
        return asset

    def _delete(self, metadata_type: str, metadata_id: str) -> Dict:
        if self._get(metadata_type, metadata_id):
            del self.catalog[metadata_type][metadata_id]
            self._save_data()
            return {"status": "success", "deleted_id": metadata_id}
        raise ValueError(f"Metadata asset '{metadata_id}' not found.")

    def _search(self, search_query: str) -> List[Dict]:
        results = []
        query = search_query.lower()
        for m_type, assets in self.catalog.items():
            for m_id, content in assets.items():
                # Simple keyword search across the JSON string of the content
                if query in json.dumps(content).lower():
                    results.append({"metadata_type": m_type, "metadata_id": m_id, "content": content})
        return results

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create": self._create, "get": self._get, "update": self._update,
            "delete": self._delete, "search": self._search
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        # Filter kwargs for the specific operation
        import inspect
        sig = inspect.signature(op_map[operation])
        op_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        return op_map[operation](**op_kwargs)

if __name__ == '__main__':
    print("Demonstrating MetadataCatalogTool functionality...")
    temp_dir = "temp_metadata_catalog"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    catalog_tool = MetadataCatalogTool(data_dir=temp_dir)
    
    try:
        # 1. Create some metadata assets
        print("\n--- Creating metadata assets ---")
        catalog_tool.execute(operation="create", metadata_type="table", metadata_id="customers",
                             metadata_content={"description": "Table containing customer data.", "owner": "sales_team"})
        catalog_tool.execute(operation="create", metadata_type="report", metadata_id="q3_sales",
                             metadata_content={"description": "Quarterly sales report for Q3.", "source_table": "customers"})
        print("Assets 'customers' and 'q3_sales' created.")

        # 2. Update an asset (triggers versioning)
        print("\n--- Updating an asset ---")
        updated_asset = catalog_tool.execute(operation="update", metadata_type="table", metadata_id="customers",
                                             metadata_content={"columns": ["id", "name", "email"]})
        print(f"Asset 'customers' updated to version {updated_asset['_version']}.")

        # 3. Search the catalog
        print("\n--- Searching for 'customer' ---")
        search_results = catalog_tool.execute(operation="search", search_query="customer")
        print(f"Found {len(search_results)} results:")
        print(json.dumps(search_results, indent=2))

        # 4. Get a specific asset
        print("\n--- Getting asset 'customers' ---")
        customer_table = catalog_tool.execute(operation="get", metadata_type="table", metadata_id="customers")
        print(json.dumps(customer_table, indent=2))

        # 5. Delete an asset
        print("\n--- Deleting asset 'q3_sales' ---")
        delete_status = catalog_tool.execute(operation="delete", metadata_type="report", metadata_id="q3_sales")
        print(f"Delete status: {delete_status['status']}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")