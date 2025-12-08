import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataPrivacyManagementTool(BaseTool):
    """
    A tool for managing data privacy, allowing for the definition of policies,
    recording and checking user consents, and simulating policy enforcement.
    """

    def __init__(self, tool_name: str = "data_privacy_management"):
        super().__init__(tool_name)
        self.policies_file = "data_privacy_policies.json"
        self.consents_file = "user_consents.json"
        self.policies: Dict[str, Dict[str, Any]] = self._load_policies()
        self.consents: Dict[str, List[Dict[str, Any]]] = self._load_consents()

    @property
    def description(self) -> str:
        return "Manages data privacy policies and user consents, including defining policies, recording/checking consents, and enforcing policies."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data privacy operation to perform.",
                    "enum": ["define_policy", "record_consent", "check_consent", "enforce_policy", "list_policies", "list_consents"]
                },
                "policy_id": {"type": "string"},
                "rules": {"type": "object"},
                "description": {"type": "string"},
                "user_id": {"type": "string"},
                "consent_type": {"type": "string"},
                "status": {"type": "boolean"},
                "timestamp": {"type": "string"},
                "data_subject_details": {"type": "object"}
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

    def _load_consents(self) -> Dict[str, List[Dict[str, Any]]]:
        if os.path.exists(self.consents_file):
            with open(self.consents_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted consents file '{self.consents_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_consents(self) -> None:
        with open(self.consents_file, 'w') as f:
            json.dump(self.consents, f, indent=4)

    def _define_policy(self, policy_id: str, rules: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([policy_id, rules]):
            raise ValueError("Policy ID and rules cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id, "description": description, "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.policies[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def _record_consent(self, user_id: str, consent_type: str, status: bool, timestamp: Optional[str] = None) -> Dict[str, Any]:
        if not all([user_id, consent_type]):
            raise ValueError("User ID and consent type cannot be empty.")

        consent_record = {
            "user_id": user_id, "consent_type": consent_type, "status": status,
            "timestamp": timestamp if timestamp else datetime.now().isoformat()
        }
        if user_id not in self.consents:
            self.consents[user_id] = []
        
        found = False
        for i, c in enumerate(self.consents[user_id]):
            if c["consent_type"] == consent_type:
                self.consents[user_id][i] = consent_record
                found = True
                break
        if not found:
            self.consents[user_id].append(consent_record)
        
        self._save_consents()
        return consent_record

    def _check_consent(self, user_id: str, consent_type: str) -> bool:
        if user_id not in self.consents: return False
        for consent in self.consents[user_id]:
            if consent["consent_type"] == consent_type and consent["status"] is True:
                return True
        return False

    def _enforce_policy(self, policy_id: str, data_subject_details: Dict[str, Any]) -> Dict[str, Any]:
        if policy_id not in self.policies: raise ValueError(f"Policy '{policy_id}' not found.")

        policy = self.policies[policy_id]
        rules = policy["rules"]
        
        compliance_status = "compliant"
        actions_taken = []
        violations = []

        user_id = data_subject_details.get("user_id")

        if "data_collection" in rules and rules["data_collection"] == "explicit_consent":
            if user_id and not self._check_consent(user_id, "data_collection"):
                violations.append("Policy requires explicit consent for data collection, but not found.")
                compliance_status = "non-compliant"
                actions_taken.append("Blocked data collection for user.")

        if "data_minimization" in rules and rules["data_minimization"] is True:
            if len(data_subject_details.keys()) > 5:
                violations.append("Policy requires data minimization, but too many data fields present.")
                compliance_status = "non-compliant"
                actions_taken.append("Suggested data reduction for data subject.")

        enforcement_result = {
            "policy_id": policy_id, "data_subject_id": user_id, "compliance_status": compliance_status,
            "violations": violations, "actions_taken": actions_taken, "enforced_at": datetime.now().isoformat()
        }
        return enforcement_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            return self._define_policy(kwargs.get("policy_id"), kwargs.get("rules"), kwargs.get("description"))
        elif operation == "record_consent":
            return self._record_consent(kwargs.get("user_id"), kwargs.get("consent_type"), kwargs.get("status"), kwargs.get("timestamp"))
        elif operation == "check_consent":
            return self._check_consent(kwargs.get("user_id"), kwargs.get("consent_type"))
        elif operation == "enforce_policy":
            return self._enforce_policy(kwargs.get("policy_id"), kwargs.get("data_subject_details"))
        elif operation == "list_policies":
            return list(self.policies.values())
        elif operation == "list_consents":
            user_id = kwargs.get("user_id")
            if user_id: return self.consents.get(user_id, [])
            all_consents = []
            for user_consents in self.consents.values(): all_consents.extend(user_consents)
            return all_consents
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataPrivacyManagementTool functionality...")
    tool = DataPrivacyManagementTool()
    
    try:
        print("\n--- Defining Policy ---")
        tool.execute(operation="define_policy", policy_id="GDPR_Collection", rules={"data_collection": "explicit_consent"}, description="Requires explicit consent for data collection.")
        
        print("\n--- Recording Consent ---")
        tool.execute(operation="record_consent", user_id="user_alice", consent_type="data_collection", status=True)

        print("\n--- Enforcing Policy ---")
        data_subject = {"user_id": "user_alice", "name": "Alice", "email": "alice@example.com"}
        enforcement_result = tool.execute(operation="enforce_policy", policy_id="GDPR_Collection", data_subject_details=data_subject)
        print(json.dumps(enforcement_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.policies_file): os.remove(tool.policies_file)
        if os.path.exists(tool.consents_file): os.remove(tool.consents_file)
        print("\nCleanup complete.")