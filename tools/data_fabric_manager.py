import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataFabricManagerTool(BaseTool):
    """
    A tool for managing a data fabric.
    """

    def __init__(self, tool_name: str = "data_fabric_manager"):
        super().__init__(tool_name)
        self.state_file = "data_fabric_state.json"
        self.state: Dict[str, Any] = self._load_state()
        if "data_sources" not in self.state:
            self.state["data_sources"] = {}
        if "data_policies" not in self.state:
            self.state["data_policies"] = {}

    @property
    def description(self) -> str:
        return "Manages a data fabric, allowing for registration of data sources, application of policies, and simulated querying."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform.",
                    "enum": ["register_data_source", "apply_data_policy", "query_data_fabric", "list_data_sources", "list_data_policies"]
                },
                "source_id": {"type": "string"},
                "source_type": {"type": "string"},
                "connection_details": {"type": "object"},
                "policy_id": {"type": "string"},
                "data_source_id": {"type": "string"},
                "policy_rules": {"type": "object"},
                "query": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_state(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{self.state_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_state(self) -> None:
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=4)

    def _register_data_source(self, source_id: str, source_type: str, connection_details: Dict[str, Any]) -> Dict[str, Any]:
        if source_id in self.state["data_sources"]:
            raise ValueError(f"Data source '{source_id}' already registered.")

        new_source = {
            "source_id": source_id, "source_type": source_type, "connection_details": connection_details,
            "status": "active", "registered_at": datetime.now().isoformat()
        }
        self.state["data_sources"][source_id] = new_source
        self._save_state()
        return new_source

    def _apply_data_policy(self, policy_id: str, data_source_id: str, policy_rules: Dict[str, Any]) -> Dict[str, Any]:
        if data_source_id not in self.state["data_sources"]:
            raise ValueError(f"Data source '{data_source_id}' not found.")
        if policy_id in self.state["data_policies"]:
            raise ValueError(f"Data policy '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id, "data_source_id": data_source_id, "policy_rules": policy_rules,
            "status": "applied", "applied_at": datetime.now().isoformat()
        }
        self.state["data_policies"][policy_id] = new_policy
        self._save_state()
        return new_policy

    def _query_data_fabric(self, query: str) -> List[Dict[str, Any]]:
        logger.info(f"Simulating query across data fabric: '{query}'")
        num_results = random.randint(1, 3)  # nosec B311
        simulated_results = []
        for i in range(num_results):
            simulated_results.append({
                "result_id": f"res_{datetime.now().strftime('%f')}_{i}",
                "query_echo": query,
                "simulated_data": f"Data item {i+1} from simulated fabric for query '{query[:20]}...'"
            })
        return simulated_results

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "register_data_source":
            return self._register_data_source(kwargs.get("source_id"), kwargs.get("source_type"), kwargs.get("connection_details"))
        elif operation == "apply_data_policy":
            return self._apply_data_policy(kwargs.get("policy_id"), kwargs.get("data_source_id"), kwargs.get("policy_rules"))
        elif operation == "query_data_fabric":
            return self._query_data_fabric(kwargs.get("query"))
        elif operation == "list_data_sources":
            return list(self.state["data_sources"].values())
        elif operation == "list_data_policies":
            return list(self.state["data_policies"].values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataFabricManagerTool functionality...")
    tool = DataFabricManagerTool()
    
    try:
        print("\n--- Registering Data Sources ---")
        tool.execute(operation="register_data_source", source_id="customer_db", source_type="database", connection_details={"host": "db.example.com"})
        
        print("\n--- Applying Data Policy ---")
        tool.execute(operation="apply_data_policy", policy_id="gdpr_policy", data_source_id="customer_db", policy_rules={"mask_pii": True})

        print("\n--- Querying Data Fabric ---")
        query_results = tool.execute(operation="query_data_fabric", query="SELECT * FROM customer_data")
        print(json.dumps(query_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.state_file):
            os.remove(tool.state_file)
        print("\nCleanup complete.")
