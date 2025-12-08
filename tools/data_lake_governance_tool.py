import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataLakeGovernanceTool(BaseTool):
    """
    A tool for defining and simulating the enforcement of data governance policies
    within a data lake context.
    """

    def __init__(self, tool_name: str = "data_lake_governance_tool"):
        super().__init__(tool_name)
        self.policies_file = "data_lake_policies.json"
        self.policies: Dict[str, Dict[str, Any]] = self._load_policies()

    @property
    def description(self) -> str:
        return "Manages data lake governance policies, including defining, enforcing, and listing policies for data assets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The governance operation to perform.",
                    "enum": ["define_policy", "enforce_policy", "list_policies", "get_policy_details"]
                },
                "policy_id": {"type": "string"},
                "data_lake_name": {"type": "string"},
                "rules": {"type": "object"},
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

    def _define_policy(self, policy_id: str, data_lake_name: str, rules: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([policy_id, data_lake_name, rules]):
            raise ValueError("Policy ID, data lake name, and rules cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id, "data_lake_name": data_lake_name, "description": description,
            "rules": rules, "defined_at": datetime.now().isoformat()
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

        if policy["data_lake_name"] != data_asset_details.get("data_lake"):
            violations.append(f"Policy '{policy_id}' is for data lake '{policy['data_lake_name']}', but asset is in '{data_asset_details.get('data_lake', 'N/A')}'.")
            compliance_status = "non-compliant"
            
        if "encryption_required" in rules and rules["encryption_required"]:
            if not data_asset_details.get("is_encrypted", False):
                violations.append("Encryption required by policy, but asset is not encrypted.")
                compliance_status = "non-compliant"
                actions_taken.append("Initiated encryption process for asset.")

        if "access_level" in rules and rules["access_level"] == "restricted":
            if data_asset_details.get("public_access", False):
                violations.append("Public access detected, but policy requires restricted access.")
                compliance_status = "non-compliant"
                actions_taken.append("Revoked public access for asset.")

        enforcement_result = {
            "policy_id": policy_id, "data_asset_name": data_asset_details.get("asset_name", "N/A"),
            "compliance_status": compliance_status, "violations": violations,
            "actions_taken": actions_taken, "enforced_at": datetime.now().isoformat()
        }
        return enforcement_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            return self._define_policy(kwargs.get("policy_id"), kwargs.get("data_lake_name"), kwargs.get("rules"), kwargs.get("description"))
        elif operation == "enforce_policy":
            return self._enforce_policy(kwargs.get("policy_id"), kwargs.get("data_asset_details"))
        elif operation == "list_policies":
            return list(self.policies.values())
        elif operation == "get_policy_details":
            return self.policies.get(kwargs.get("policy_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataLakeGovernanceTool functionality...")
    tool = DataLakeGovernanceTool()
    
    try:
        print("\n--- Defining Policies ---")
        tool.execute(operation="define_policy", policy_id="Encryption_Policy", data_lake_name="main_lake", rules={"encryption_required": True}, description="Ensures data is encrypted.")
        
        print("\n--- Enforcing Policy ---")
        asset_details = {"asset_name": "customer_data_blob", "data_lake": "main_lake", "is_encrypted": False}
        enforcement_result = tool.execute(operation="enforce_policy", policy_id="Encryption_Policy", data_asset_details=asset_details)
        print(json.dumps(enforcement_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.policies_file):
            os.remove(tool.policies_file)
        print("\nCleanup complete.")