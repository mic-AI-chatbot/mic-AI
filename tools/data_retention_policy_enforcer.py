import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataRetentionPolicyEnforcerTool(BaseTool):
    """
    A tool for defining and simulating the enforcement of data retention policies.
    """

    def __init__(self, tool_name: str = "data_retention_policy_enforcer"):
        super().__init__(tool_name)
        self.policies_file = "data_retention_policies.json"
        self.policies: Dict[str, Dict[str, Any]] = self._load_policies()

    @property
    def description(self) -> str:
        return "Defines and enforces data retention policies, checking data for expiry and applying actions like deletion or archiving."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data retention operation to perform.",
                    "enum": ["define_policy", "check_data_for_retention", "enforce_policy", "list_policies", "get_policy_details"]
                },
                "policy_id": {"type": "string"},
                "policy_name": {"type": "string"},
                "retention_period_days": {"type": "integer", "minimum": 1},
                "data_type": {"type": "string"},
                "action_on_expiry": {"type": "string", "enum": ["delete", "archive", "anonymize"]},
                "description": {"type": "string"},
                "data_records": {"type": "array", "items": {"type": "object"}}
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

    def _define_policy(self, policy_id: str, policy_name: str, retention_period_days: int, data_type: str, action_on_expiry: str, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([policy_id, policy_name, retention_period_days, data_type, action_on_expiry]):
            raise ValueError("Policy ID, name, retention period, data type, and action on expiry cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")
        if action_on_expiry not in ["delete", "archive", "anonymize"]:
            raise ValueError(f"Unsupported action_on_expiry: '{action_on_expiry}'.")

        new_policy = {
            "policy_id": policy_id, "policy_name": policy_name, "retention_period_days": retention_period_days,
            "data_type": data_type, "action_on_expiry": action_on_expiry, "description": description,
            "defined_at": datetime.now().isoformat()
        }
        self.policies[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def _check_data_for_retention(self, policy_id: str, data_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        if policy_id not in self.policies: raise ValueError(f"Policy '{policy_id}' not found.")
        if not isinstance(data_records, list) or not all(isinstance(item, dict) for item in data_records):
            raise ValueError("Input data_records must be a list of dictionaries.")

        policy = self.policies[policy_id]
        retention_period = timedelta(days=policy["retention_period_days"])
        current_date = datetime.now()

        expired_records = []
        nearing_expiry_records = []

        for record in data_records:
            record_date_str = record.get("created_at") or record.get("last_modified_at")
            if not record_date_str: continue
            
            try:
                record_date = datetime.fromisoformat(record_date_str)
                expiry_date = record_date + retention_period
                
                if current_date > expiry_date: expired_records.append(record)
                elif current_date + timedelta(days=7) > expiry_date: nearing_expiry_records.append(record)
            except ValueError: pass

        check_result = {
            "policy_id": policy_id, "timestamp": datetime.now().isoformat(),
            "total_records_checked": len(data_records), "expired_records_count": len(expired_records),
            "nearing_expiry_records_count": len(nearing_expiry_records),
            "expired_records": expired_records, "nearing_expiry_records": nearing_expiry_records
        }
        return check_result

    def _enforce_policy(self, policy_id: str, data_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if policy_id not in self.policies: raise ValueError(f"Policy '{policy_id}' not found.")
        if not isinstance(data_records, list) or not all(isinstance(item, dict) for item in data_records):
            raise ValueError("Input data_records must be a list of dictionaries.")

        policy = self.policies[policy_id]
        action_on_expiry = policy["action_on_expiry"]
        
        check_results = self._check_data_for_retention(policy_id, data_records)
        expired_records = check_results["expired_records"]
        
        processed_records = []

        for record in data_records:
            if record in expired_records:
                if action_on_expiry == "delete": pass # Simulate deletion by not adding to processed_records
                elif action_on_expiry == "archive": processed_records.append({**record, "status": "archived"})
                elif action_on_expiry == "anonymize": processed_records.append({**record, "status": "anonymized", "data": "[ANONYMIZED]"})
            else:
                processed_records.append(record)
        return processed_records

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            return self._define_policy(kwargs.get("policy_id"), kwargs.get("policy_name"), kwargs.get("retention_period_days"), kwargs.get("data_type"), kwargs.get("action_on_expiry"), kwargs.get("description"))
        elif operation == "check_data_for_retention":
            return self._check_data_for_retention(kwargs.get("policy_id"), kwargs.get("data_records"))
        elif operation == "enforce_policy":
            return self._enforce_policy(kwargs.get("policy_id"), kwargs.get("data_records"))
        elif operation == "list_policies":
            return list(self.policies.values())
        elif operation == "get_policy_details":
            return self.policies.get(kwargs.get("policy_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataRetentionPolicyEnforcerTool functionality...")
    tool = DataRetentionPolicyEnforcerTool()
    
    today = datetime.now()
    one_year_ago = today - timedelta(days=365)
    one_year_and_one_day_ago = today - timedelta(days=366)

    sample_data = [
        {"id": "cust_001", "data_type": "PII", "created_at": one_year_ago.isoformat(), "value": "sensitive_data_1"},
        {"id": "cust_002", "data_type": "PII", "created_at": one_year_and_one_day_ago.isoformat(), "value": "sensitive_data_2"},
    ]

    try:
        print("\n--- Defining Policy ---")
        tool.execute(operation="define_policy", policy_id="Customer_PII_Policy", policy_name="Customer PII Retention", retention_period_days=365, data_type="PII", action_on_expiry="delete", description="Delete customer PII after 1 year.")
        
        print("\n--- Checking Data for Retention ---")
        check_result = tool.execute(operation="check_data_for_retention", policy_id="Customer_PII_Policy", data_records=sample_data)
        print(json.dumps(check_result, indent=2))

        print("\n--- Enforcing Policy ---")
        enforced_data = tool.execute(operation="enforce_policy", policy_id="Customer_PII_Policy", data_records=sample_data)
        print(json.dumps(enforced_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.policies_file): os.remove(tool.policies_file)
        print("\nCleanup complete.")