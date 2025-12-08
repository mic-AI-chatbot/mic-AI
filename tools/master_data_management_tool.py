

import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MasterDataManagementTool(BaseTool):
    """
    A tool for managing master data, including running data quality checks
    and preparing data for synchronization with other systems.
    """

    def __init__(self, tool_name: str = "MDMTool", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "master_data.json")
        self.data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={"entities": {}, "reports": {}})

    @property
    def description(self) -> str:
        return "Manages master data, runs quality checks, and prepares sync payloads."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_entity", "update_entity", "run_quality_check", "generate_sync_payload"]},
                "entity_id": {"type": "string"}, "entity_type": {"type": "string", "enum": ["customer", "product"]},
                "attributes": {"type": "object"}, "new_attributes": {"type": "object"},
                "quality_rules": {"type": "array", "description": "Rules like [{'attribute': 'email', 'rule': 'not_empty'}]"},
                "field_mapping": {"type": "object", "description": "Mapping for target system, e.g., {'name': 'customerName'}"}
            },
            "required": ["operation", "entity_id"]
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
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=4)

    def create_entity(self, entity_id: str, entity_type: str, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new master data entity."""
        if entity_id in self.data["entities"]: raise ValueError(f"Entity '{entity_id}' already exists.")
        new_entity = {"entity_id": entity_id, "entity_type": entity_type, "attributes": attributes, "created_at": datetime.now().isoformat()}
        self.data["entities"][entity_id] = new_entity
        self._save_data()
        return new_entity

    def update_entity(self, entity_id: str, new_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Updates an existing master data entity."""
        entity = self.data["entities"].get(entity_id)
        if not entity: raise ValueError(f"Entity '{entity_id}' not found.")
        entity["attributes"].update(new_attributes)
        entity["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return entity

    def run_quality_check(self, entity_id: str, quality_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs a series of data quality rules against an entity."""
        entity = self.data["entities"].get(entity_id)
        if not entity: raise ValueError(f"Entity '{entity_id}' not found.")
        
        issues_found = []
        total_rules = len(quality_rules)
        passed_rules = 0

        for rule in quality_rules:
            attr = rule.get("attribute")
            value = entity["attributes"].get(attr)
            
            passed = True
            if rule["rule"] == "not_empty" and (value is None or value == ""):
                passed = False
                issues_found.append(f"Attribute '{attr}' is empty.")
            elif rule["rule"] == "format" and not re.match(rule.get("pattern", ""), str(value)):
                passed = False
                issues_found.append(f"Attribute '{attr}' has incorrect format.")
            
            if passed: passed_rules += 1
        
        score = (passed_rules / total_rules) * 100 if total_rules > 0 else 100
        report = {"entity_id": entity_id, "quality_score": score, "issues": issues_found, "rules_checked": total_rules}
        self.data["reports"][f"QC-{entity_id}-{datetime.now().strftime('%s')}"] = report
        self._save_data()
        return report

    def generate_sync_payload(self, entity_id: str, field_mapping: Dict[str, str]) -> Dict[str, Any]:
        """Generates a transformed data payload for a target system."""
        entity = self.data["entities"].get(entity_id)
        if not entity: raise ValueError(f"Entity '{entity_id}' not found.")
        
        payload = {}
        for source_field, target_field in field_mapping.items():
            if source_field in entity["attributes"]:
                payload[target_field] = entity["attributes"][source_field]
        
        return {"entity_id": entity_id, "sync_payload": payload}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_entity": self.create_entity, "update_entity": self.update_entity,
            "run_quality_check": self.run_quality_check, "generate_sync_payload": self.generate_sync_payload
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MasterDataManagementTool functionality...")
    temp_dir = "temp_mdm_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    mdm_tool = MasterDataManagementTool(data_dir=temp_dir)
    
    try:
        # 1. Create a customer entity
        print("\n--- Creating a customer entity ---")
        mdm_tool.execute(
            operation="create_entity", entity_id="cust123", entity_type="customer",
            attributes={"name": "John Doe", "email": "johndoe@example.com", "phone": ""}
        )
        print("Entity 'cust123' created.")

        # 2. Run a data quality check with specific rules
        print("\n--- Running a data quality check ---")
        rules = [
            {"attribute": "email", "rule": "format", "pattern": r"^\S+@\S+\.\S+$"},
            {"attribute": "phone", "rule": "not_empty"},
            {"attribute": "address", "rule": "not_empty"}
        ]
        qc_report = mdm_tool.execute(operation="run_quality_check", entity_id="cust123", quality_rules=rules)
        print(json.dumps(qc_report, indent=2))

        # 3. Update the entity to fix issues
        print("\n--- Updating entity to fix quality issues ---")
        mdm_tool.execute(operation="update_entity", entity_id="cust123", new_attributes={"phone": "555-1234", "address": "123 Main St"})
        
        # 4. Re-run the quality check
        print("\n--- Re-running quality check after fixes ---")
        qc_report_fixed = mdm_tool.execute(operation="run_quality_check", entity_id="cust123", quality_rules=rules)
        print(json.dumps(qc_report_fixed, indent=2))

        # 5. Generate a sync payload for a CRM system
        print("\n--- Generating sync payload for CRM ---")
        mapping = {"name": "customerName", "email": "emailAddress", "address": "streetAddress"}
        payload = mdm_tool.execute(operation="generate_sync_payload", entity_id="cust123", field_mapping=mapping)
        print(json.dumps(payload, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
