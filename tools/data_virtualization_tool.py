import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataVirtualizationTool(BaseTool):
    """
    A tool for simulating data virtualization, allowing for the creation
    and querying of virtual views over simulated data sources.
    """

    def __init__(self, tool_name: str = "data_virtualization_tool"):
        super().__init__(tool_name)
        self.views_file = "virtual_views.json"
        self.virtual_views: Dict[str, Dict[str, Any]] = self._load_views()

    @property
    def description(self) -> str:
        return "Simulates data virtualization: creates and queries virtual views over simulated data sources."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data virtualization operation to perform.",
                    "enum": ["create_virtual_view", "query_virtual_view", "list_virtual_views", "get_virtual_view_details"]
                },
                "view_id": {"type": "string"},
                "view_name": {"type": "string"},
                "data_sources": {"type": "array", "items": {"type": "string"}},
                "query_definition": {"type": "object"},
                "description": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_views(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.views_file):
            with open(self.views_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted views file '{self.views_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_views(self) -> None:
        with open(self.views_file, 'w') as f:
            json.dump(self.virtual_views, f, indent=4)

    def _create_virtual_view(self, view_id: str, view_name: str, data_sources: List[str], query_definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([view_id, view_name, data_sources, query_definition]):
            raise ValueError("View ID, name, data sources, and query definition cannot be empty.")
        if view_id in self.virtual_views:
            raise ValueError(f"Virtual view '{view_id}' already exists.")

        new_view = {
            "view_id": view_id, "view_name": view_name, "data_sources": data_sources,
            "query_definition": query_definition, "description": description,
            "created_at": datetime.now().isoformat()
        }
        self.virtual_views[view_id] = new_view
        self._save_views()
        return new_view

    def _query_virtual_view(self, view_id: str) -> List[Dict[str, Any]]:
        view = self.virtual_views.get(view_id)
        if not view: raise ValueError(f"Virtual view '{view_id}' not found.")

        simulated_source_data: Dict[str, List[Dict[str, Any]]] = {
            "customers_db": [
                {"id": 1, "name": "Alice", "age": 30, "city": "NY"},
                {"id": 2, "name": "Bob", "age": 25, "city": "LA"},
                {"id": 3, "name": "Charlie", "age": 35, "city": "NY"}
            ],
            "orders_api": [
                {"order_id": 101, "customer_id": 1, "product": "Laptop", "price": 1200},
                {"order_id": 102, "customer_id": 3, "product": "Mouse", "price": 25},
                {"order_id": 103, "customer_id": 1, "product": "Keyboard", "price": 75}
            ]
        }

        query_def = view["query_definition"]
        result_data: List[Dict[str, Any]] = []

        if query_def.get("type") == "join" and len(view["data_sources"]) == 2:
            source1_name = view["data_sources"][0]
            source2_name = view["data_sources"][1]
            join_on_key = query_def.get("on")
            select_fields = query_def.get("select", [])

            if source1_name in simulated_source_data and source2_name in simulated_source_data:
                for record1 in simulated_source_data[source1_name]:
                    for record2 in simulated_source_data[source2_name]:
                        if record1.get(join_on_key) == record2.get(join_on_key):
                            combined_record = {**record1, **record2}
                            if select_fields:
                                selected_record = {f: combined_record.get(f) for f in select_fields if f in combined_record}
                            else:
                                selected_record = combined_record
                            result_data.append(selected_record)
        elif query_def.get("type") == "select" and len(view["data_sources"]) == 1:
            source_name = view["data_sources"][0]
            select_fields = query_def.get("select", [])
            if source_name in simulated_source_data:
                for record in simulated_source_data[source_name]:
                    if select_fields:
                        selected_record = {f: record.get(f) for f in select_fields if f in record}
                    else:
                        selected_record = record
                    result_data.append(selected_record)
        else:
            logger.warning(f"Unsupported query definition type '{query_def.get('type')}' or number of sources for view '{view_id}'. Returning empty results.")

        return result_data

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_virtual_view":
            return self._create_virtual_view(kwargs.get("view_id"), kwargs.get("view_name"), kwargs.get("data_sources"), kwargs.get("query_definition"), kwargs.get("description"))
        elif operation == "query_virtual_view":
            return self._query_virtual_view(kwargs.get("view_id"))
        elif operation == "list_virtual_views":
            return [{k: v for k, v in view.items() if k != "query_definition"} for view in self.virtual_views.values()]
        elif operation == "get_virtual_view_details":
            return self.virtual_views.get(kwargs.get("view_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataVirtualizationTool functionality...")
    tool = DataVirtualizationTool()
    
    try:
        print("\n--- Creating Virtual View ---")
        tool.execute(operation="create_virtual_view", view_id="customer_orders_view", view_name="Customer Orders Combined", data_sources=["customers_db", "orders_api"], query_definition={"type": "join", "on": "id", "select": ["name", "product"]})
        
        print("\n--- Querying Virtual View ---")
        query_results = tool.execute(operation="query_virtual_view", view_id="customer_orders_view")
        print(json.dumps(query_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.views_file): os.remove(tool.views_file)
        print("\nCleanup complete.")