import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataGovernanceEnforcerTool(BaseTool):
    """
    A tool for defining and simulating the enforcement of data governance policies.
    """

    def __init__(self, tool_name: str = "data_governance_enforcer"):
        super().__init__(tool_name)
        self.policies_file = "data_governance_policies.json"
        self.policies: Dict[str, Dict[str, Any]] = self._load_policies()

    @property
    def description(self) -> str:
        return "Defines and enforces data governance policies on data assets, simulating compliance checks and actions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform.",
                    "enum": ["define_policy", "enforce_policy", "list_policies", "get_policy_details"]
                },
                "policy_id": {"type": "string"},
                "policy_rules": {"type": "object"},
                "description": {"type": "string"},
                "data_asset_details": {"type": "object"}
            },
            "required": ["operation"]
        }

    def _load_policies(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.policies_file):
            with open(self.policies_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted policies file '{self.policies_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_policies(self) -> None:
        with open(self.policies_file, 'w') as f:
            json.dump(self.policies, f, indent=4)

    def _define_policy(self, policy_id: str, policy_rules: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([policy_id, policy_rules]):
            raise ValueError("Policy ID and rules cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id, "description": description, "rules": policy_rules,
            "defined_at": datetime.now().isoformat()
        }
        self.policies[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def _enforce_policy(self, policy_id: str, data_asset_details: Dict[str, Any]) -> Dict[str, Any]:
        if policy_id not in self.policies:
            raise ValueError(f"Policy '{policy_id}' not found.")

        policy = self.policies[policy_id]
        rules = policy["rules"]
        
        compliance_status = "compliant"
        actions_taken = []
        violations = []

        if "data_type" in rules and rules["data_type"] == "PII":
            if data_asset_details.get("data_type") != "PII":
                violations.append("Data asset not classified as PII but policy requires it.")
                compliance_status = "non-compliant"
            
            if "action" in rules and rules["action"] == "mask":
                if "sensitive_fields" in data_asset_details:
                    actions_taken.append(f"Masked sensitive fields: {data_asset_details['sensitive_fields']}")
                else:
                    violations.append("Policy requires masking, but no sensitive fields specified in asset details.")
                    compliance_status = "non-compliant"

        if "min_age" in rules and data_asset_details.get("age") is not None:
            if data_asset_details["age"] < rules["min_age"]:
                violations.append(f"Age ({data_asset_details['age']}) is below minimum required age ({rules['min_age']}).")
                compliance_status = "non-compliant"

        enforcement_result = {
            "policy_id": policy_id, "data_asset_name": data_asset_details.get("asset_name", "N/A"),
            "compliance_status": compliance_status, "violations": violations,
            "actions_taken": actions_taken, "enforced_at": datetime.now().isoformat()
        }
        return enforcement_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            return self._define_policy(kwargs.get("policy_id"), kwargs.get("policy_rules"), kwargs.get("description"))
        elif operation == "enforce_policy":
            return self._enforce_policy(kwargs.get("policy_id"), kwargs.get("data_asset_details"))
        elif operation == "list_policies":
            return list(self.policies.values())
        elif operation == "get_policy_details":
            return self.policies.get(kwargs.get("policy_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataGovernanceEnforcerTool functionality...")
    tool = DataGovernanceEnforcerTool()
    
    try:
        print("\n--- Defining Policies ---")
        tool.execute(operation="define_policy", policy_id="PII_Masking", policy_rules={"data_type": "PII", "action": "mask"}, description="Masks PII data.")
        tool.execute(operation="define_policy", policy_id="Age_Restriction", policy_rules={"min_age": 18}, description="Restricts access to users under 18.")

        print("\n--- Enforcing PII_Masking Policy ---")
        asset_details = {"asset_name": "customer_record_1", "data_type": "PII", "sensitive_fields": ["email"]}
        enforcement_result = tool.execute(operation="enforce_policy", policy_id="PII_Masking", data_asset_details=asset_details)
        print(json.dumps(enforcement_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.policies_file):
            os.remove(tool.policies_file)
        print("\nCleanup complete.")