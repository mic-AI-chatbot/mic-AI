import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RegulatoryComplianceMonitorSimulatorTool(BaseTool):
    """
    A tool that simulates regulatory compliance monitoring, allowing for
    defining regulations, checking systems against them, and generating reports.
    """

    def __init__(self, tool_name: str = "RegulatoryComplianceMonitorSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.regulations_file = os.path.join(self.data_dir, "regulation_definitions.json")
        self.compliance_file = os.path.join(self.data_dir, "compliance_records.json")
        
        # Regulation definitions: {regulation_id: {name: ..., rules: []}}
        self.regulation_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.regulations_file, default={})
        # Compliance records: {record_id: {regulation_id: ..., system_id: ..., violations: [], status: ...}}
        self.compliance_records: Dict[str, Dict[str, Any]] = self._load_data(self.compliance_file, default={})

    @property
    def description(self) -> str:
        return "Simulates regulatory compliance monitoring: check systems against regulations and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_regulation", "check_compliance", "generate_report", "list_regulations"]},
                "regulation_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "compliance_rules": {"type": "array", "items": {"type": "object"}, "description": "e.g., [{'system_attribute': 'data_encryption', 'must_be': True}]"},
                "system_id": {"type": "string"},
                "system_configuration": {"type": "object", "description": "Simulated configuration of the system being checked."}
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

    def _save_regulations(self):
        with open(self.regulations_file, 'w') as f: json.dump(self.regulation_definitions, f, indent=2)

    def _save_compliance_records(self):
        with open(self.compliance_file, 'w') as f: json.dump(self.compliance_records, f, indent=2)

    def define_regulation(self, regulation_id: str, name: str, description: str, compliance_rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new regulation with its compliance rules."""
        if regulation_id in self.regulation_definitions: raise ValueError(f"Regulation '{regulation_id}' already exists.")
        
        new_regulation = {
            "id": regulation_id, "name": name, "description": description,
            "compliance_rules": compliance_rules, "defined_at": datetime.now().isoformat()
        }
        self.regulation_definitions[regulation_id] = new_regulation
        self._save_regulations()
        return new_regulation

    def check_compliance(self, regulation_id: str, system_id: str, system_configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Checks a system's compliance against a specific regulation."""
        regulation = self.regulation_definitions.get(regulation_id)
        if not regulation: raise ValueError(f"Regulation '{regulation_id}' not found. Define it first.")
        
        violations = []
        for rule in regulation["compliance_rules"]:
            attribute = rule["system_attribute"]
            must_be_value = rule.get("must_be")
            must_not_be_value = rule.get("must_not_be")
            
            system_attr_value = system_configuration.get(attribute)
            
            if must_be_value is not None and system_attr_value != must_be_value:
                violations.append(f"Violation: Attribute '{attribute}' is '{system_attr_value}', but must be '{must_be_value}'.")
            if must_not_be_value is not None and system_attr_value == must_not_be_value:
                violations.append(f"Violation: Attribute '{attribute}' is '{system_attr_value}', but must NOT be '{must_not_be_value}'.")
        
        is_compliant = not violations
        record_id = f"comp_rec_{regulation_id}_{system_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_record = {
            "id": record_id, "regulation_id": regulation_id, "system_id": system_id,
            "is_compliant": is_compliant, "violations": violations,
            "checked_at": datetime.now().isoformat()
        }
        self.compliance_records[record_id] = new_record
        self._save_compliance_records()
        return new_record

    def generate_report(self, regulation_id: str) -> Dict[str, Any]:
        """Generates a compliance report for a specific regulation."""
        regulation = self.regulation_definitions.get(regulation_id)
        if not regulation: raise ValueError(f"Regulation '{regulation_id}' not found.")
        
        related_records = [rec for rec in self.compliance_records.values() if rec["regulation_id"] == regulation_id]
        
        compliant_systems = [rec["system_id"] for rec in related_records if rec["is_compliant"]]
        non_compliant_systems = [rec["system_id"] for rec in related_records if not rec["is_compliant"]]
        
        report = {
            "regulation_id": regulation_id, "regulation_name": regulation["name"],
            "total_systems_checked": len(related_records),
            "compliant_systems_count": len(compliant_systems),
            "non_compliant_systems_count": len(non_compliant_systems),
            "compliant_systems": compliant_systems,
            "non_compliant_systems": non_compliant_systems,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def list_regulations(self) -> List[Dict[str, Any]]:
        """Lists all defined regulations."""
        return list(self.regulation_definitions.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_regulation":
            regulation_id = kwargs.get('regulation_id')
            name = kwargs.get('name')
            description = kwargs.get('description')
            compliance_rules = kwargs.get('compliance_rules')
            if not all([regulation_id, name, description, compliance_rules]):
                raise ValueError("Missing 'regulation_id', 'name', 'description', or 'compliance_rules' for 'define_regulation' operation.")
            return self.define_regulation(regulation_id, name, description, compliance_rules)
        elif operation == "check_compliance":
            regulation_id = kwargs.get('regulation_id')
            system_id = kwargs.get('system_id')
            system_configuration = kwargs.get('system_configuration')
            if not all([regulation_id, system_id, system_configuration]):
                raise ValueError("Missing 'regulation_id', 'system_id', or 'system_configuration' for 'check_compliance' operation.")
            return self.check_compliance(regulation_id, system_id, system_configuration)
        elif operation == "generate_report":
            regulation_id = kwargs.get('regulation_id')
            if not regulation_id:
                raise ValueError("Missing 'regulation_id' for 'generate_report' operation.")
            return self.generate_report(regulation_id)
        elif operation == "list_regulations":
            # No additional kwargs required for list_regulations
            return self.list_regulations()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RegulatoryComplianceMonitorSimulatorTool functionality...")
    temp_dir = "temp_compliance_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    compliance_tool = RegulatoryComplianceMonitorSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a data privacy regulation
        print("\n--- Defining regulation 'GDPR_Compliance' ---")
        compliance_tool.execute(operation="define_regulation", regulation_id="GDPR_Compliance", name="GDPR Data Privacy",
                                description="Ensures personal data is handled according to GDPR.",
                                compliance_rules=[
                                    {"system_attribute": "data_encryption", "must_be": True},
                                    {"system_attribute": "data_retention_policy", "must_not_be": "indefinite"}
                                ])
        print("Regulation defined.")

        # 2. Simulate a compliant system
        print("\n--- Checking compliance for 'CRM_System_01' (compliant) ---")
        compliant_config = {"data_encryption": True, "data_retention_policy": "7_years", "data_location": "EU"}
        compliance_tool.execute(operation="check_compliance", regulation_id="GDPR_Compliance", system_id="CRM_System_01", system_configuration=compliant_config)
        print("Compliance check for CRM_System_01 completed.")

        # 3. Simulate a non-compliant system
        print("\n--- Checking compliance for 'Marketing_DB_01' (non-compliant) ---")
        non_compliant_config = {"data_encryption": False, "data_retention_policy": "indefinite", "data_location": "US"}
        compliance_tool.execute(operation="check_compliance", regulation_id="GDPR_Compliance", system_id="Marketing_DB_01", system_configuration=non_compliant_config)
        print("Compliance check for Marketing_DB_01 completed.")

        # 4. Generate a report
        print("\n--- Generating compliance report for 'GDPR_Compliance' ---")
        report = compliance_tool.execute(operation="generate_report", regulation_id="GDPR_Compliance")
        print(json.dumps(report, indent=2))

        # 5. List all regulations
        print("\n--- Listing all defined regulations ---")
        all_regs = compliance_tool.execute(operation="list_regulations")
        print(json.dumps(all_regs, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")