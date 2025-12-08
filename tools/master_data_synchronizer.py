

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from deepdiff import DeepDiff

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataReconciliationTool(BaseTool):
    """
    A tool to find and resolve inconsistencies between different versions of a
    data record stored across multiple systems.
    """

    def __init__(self, tool_name: str = "DataReconciler", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "reconciliation_data.json")
        # Data is stored as {record_id: {system_name: attributes}}
        self.records: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={})

    @property
    def description(self) -> str:
        return "Finds and resolves data discrepancies between systems."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_system_record", "find_discrepancies", "resolve_conflicts"]},
                "record_id": {"type": "string"}, "system_name": {"type": "string"}, "attributes": {"type": "object"},
                "source_system": {"type": "string"}, "target_system": {"type": "string"},
                "strategy": {"type": "string", "enum": ["source_wins", "target_wins"], "description": "Merge strategy."}
            },
            "required": ["operation", "record_id"]
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
        with open(self.data_file, 'w') as f: json.dump(self.records, f, indent=4)

    def add_system_record(self, record_id: str, system_name: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Adds a version of a record from a specific system."""
        if record_id not in self.records:
            self.records[record_id] = {}
        
        self.records[record_id][system_name] = {"attributes": attributes, "last_updated": datetime.now().isoformat()}
        self._save_data()
        return self.records[record_id]

    def find_discrepancies(self, record_id: str) -> Dict[str, Any]:
        """Compares all versions of a record and reports differences."""
        record_versions = self.records.get(record_id)
        if not record_versions or len(record_versions) < 2:
            return {"message": "At least two system records are needed to find discrepancies."}

        systems = list(record_versions.keys())
        base_system = systems[0]
        comparison = {}
        
        for i in range(1, len(systems)):
            compare_system = systems[i]
            diff = DeepDiff(record_versions[base_system]['attributes'], record_versions[compare_system]['attributes'], ignore_order=True)
            if diff:
                comparison[f"{base_system}_vs_{compare_system}"] = json.loads(diff.to_json())

        return {"record_id": record_id, "discrepancies": comparison}

    def resolve_conflicts(self, record_id: str, source_system: str, target_system: str, strategy: str) -> Dict[str, Any]:
        """Resolves conflicts between two system records using a strategy."""
        record_versions = self.records.get(record_id)
        if not record_versions or source_system not in record_versions or target_system not in record_versions:
            raise ValueError("Both source and target system records must exist.")

        if strategy == "source_wins":
            # Update target with source's data
            self.records[record_id][target_system]['attributes'] = self.records[record_id][source_system]['attributes']
        elif strategy == "target_wins":
            # Update source with target's data
            self.records[record_id][source_system]['attributes'] = self.records[record_id][target_system]['attributes']
        else:
            raise ValueError(f"Unsupported strategy: {strategy}")
            
        self.records[record_id][target_system]['last_updated'] = datetime.now().isoformat()
        self.records[record_id][source_system]['last_updated'] = datetime.now().isoformat()
        self._save_data()
        
        return {"record_id": record_id, "resolved_record": self.records[record_id][target_system]}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_system_record": self.add_system_record,
            "find_discrepancies": self.find_discrepancies,
            "resolve_conflicts": self.resolve_conflicts
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating DataReconciliationTool functionality...")
    temp_dir = "temp_reconciliation_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    reconciler_tool = DataReconciliationTool(data_dir=temp_dir)
    
    try:
        # 1. Add two conflicting versions of the same record
        print("\n--- Adding conflicting records for 'cust123' ---")
        reconciler_tool.execute(
            operation="add_system_record", record_id="cust123", system_name="CRM",
            attributes={"name": "John Doe", "email": "j.doe@example.com", "status": "active"}
        )
        reconciler_tool.execute(
            operation="add_system_record", record_id="cust123", system_name="ERP",
            attributes={"name": "John Doe", "email": "johndoe@example.com", "status": "inactive"}
        )
        print("Conflicting records added.")

        # 2. Find the discrepancies
        print("\n--- Finding discrepancies ---")
        discrepancies = reconciler_tool.execute(operation="find_discrepancies", record_id="cust123")
        print(json.dumps(discrepancies, indent=2))

        # 3. Resolve the conflict using a 'source_wins' strategy
        print("\n--- Resolving conflicts (CRM wins) ---")
        resolved = reconciler_tool.execute(
            operation="resolve_conflicts", record_id="cust123", 
            source_system="CRM", target_system="ERP", strategy="source_wins"
        )
        print("Resolved record in ERP:")
        print(json.dumps(resolved['resolved_record'], indent=2))

        # 4. Verify that discrepancies are gone
        print("\n--- Verifying resolution ---")
        discrepancies_after = reconciler_tool.execute(operation="find_discrepancies", record_id="cust123")
        print(json.dumps(discrepancies_after, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
