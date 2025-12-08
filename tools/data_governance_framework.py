import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataGovernanceFrameworkTool(BaseTool):
    """
    A tool for simulating a data governance framework, managing policies,
    user roles, and data domains with persistent storage.
    """

    def __init__(self, tool_name: str = "data_governance_framework"):
        super().__init__(tool_name)
        self.policies_file = "dg_policies.json"
        self.roles_file = "dg_roles.json"
        self.data_domains_file = "dg_data_domains.json"

        self.policies: Dict[str, Dict[str, Any]] = self._load_state(self.policies_file)
        self.roles: Dict[str, List[Dict[str, Any]]] = self._load_state(self.roles_file)
        self.data_domains: Dict[str, Dict[str, Any]] = self._load_state(self.data_domains_file)

    @property
    def description(self) -> str:
        return "Manages a data governance framework, including policies, user roles, and data domains."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The action to perform.",
                    "enum": ["define_policy", "assign_role", "define_data_domain", "check_access", "list_policies", "list_roles", "list_data_domains"]
                },
                "policy_id": {"type": "string"},
                "rules": {"type": "object"},
                "description": {"type": "string"},
                "user_id": {"type": "string"},
                "role": {"type": "string"},
                "data_domain_id": {"type": "string"},
                "owner_role": {"type": "string"},
                "action": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str) -> Dict[str, Any]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return {}
        return {}

    def _save_state(self, state: Dict[str, Any], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _define_policy(self, policy_id: str, rules: Dict[str, Any], description: str) -> Dict[str, Any]:
        if not all([policy_id, rules, description]):
            raise ValueError("Policy ID, rules, and description cannot be empty.")
        if policy_id in self.policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")

        new_policy = {
            "policy_id": policy_id, "description": description, "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.policies[policy_id] = new_policy
        self._save_state(self.policies, self.policies_file)
        return new_policy

    def _assign_role(self, user_id: str, role: str, data_domain_id: str) -> Dict[str, Any]:
        if not all([user_id, role, data_domain_id]):
            raise ValueError("User ID, role, and data domain ID cannot be empty.")
        if data_domain_id not in self.data_domains:
            raise ValueError(f"Data domain '{data_domain_id}' not found. Define it first.")

        assignment = {
            "user_id": user_id, "role": role, "data_domain_id": data_domain_id,
            "assigned_at": datetime.now().isoformat()
        }
        if user_id not in self.roles:
            self.roles[user_id] = []
        self.roles[user_id].append(assignment)
        self._save_state(self.roles, self.roles_file)
        return assignment

    def _define_data_domain(self, domain_id: str, description: str, owner_role: str) -> Dict[str, Any]:
        if not all([domain_id, description, owner_role]):
            raise ValueError("Domain ID, description, and owner role cannot be empty.")
        if domain_id in self.data_domains:
            raise ValueError(f"Data domain '{domain_id}' already exists.")

        new_domain = {
            "domain_id": domain_id, "description": description, "owner_role": owner_role,
            "defined_at": datetime.now().isoformat()
        }
        self.data_domains[domain_id] = new_domain
        self._save_state(self.data_domains, self.data_domains_file)
        return new_domain

    def _check_access(self, user_id: str, data_domain_id: str, action: str) -> bool:
        if user_id not in self.roles: return False
        if data_domain_id not in self.data_domains: return False

        user_roles = self.roles[user_id]
        for role_assignment in user_roles:
            if role_assignment["data_domain_id"] == data_domain_id:
                return True
        return False

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            return self._define_policy(kwargs.get("policy_id"), kwargs.get("rules"), kwargs.get("description"))
        elif operation == "assign_role":
            return self._assign_role(kwargs.get("user_id"), kwargs.get("role"), kwargs.get("data_domain_id"))
        elif operation == "define_data_domain":
            return self._define_data_domain(kwargs.get("domain_id"), kwargs.get("description"), kwargs.get("owner_role"))
        elif operation == "check_access":
            return self._check_access(kwargs.get("user_id"), kwargs.get("data_domain_id"), kwargs.get("action"))
        elif operation == "list_policies":
            return list(self.policies.values())
        elif operation == "list_roles":
            all_assignments = []
            for user_id, assignments in self.roles.items():
                all_assignments.extend(assignments)
            return all_assignments
        elif operation == "list_data_domains":
            return list(self.data_domains.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataGovernanceFrameworkTool functionality...")
    tool = DataGovernanceFrameworkTool()
    
    try:
        print("\n--- Defining Data Domains ---")
        tool.execute(operation="define_data_domain", domain_id="CustomerData", description="Sensitive customer information.", owner_role="data_owner")
        
        print("\n--- Defining Policies ---")
        tool.execute(operation="define_policy", policy_id="GDPR_Compliance", rules={"data_type": "PII", "retention": "7_years"}, description="Ensures compliance with GDPR for PII.")

        print("\n--- Assigning Roles ---")
        tool.execute(operation="assign_role", user_id="user_alice", role="data_owner", data_domain_id="CustomerData")

        print("\n--- Checking Access ---")
        access_granted = tool.execute(operation="check_access", user_id="user_alice", data_domain_id="CustomerData", action="read")
        print(f"Alice can read CustomerData: {access_granted}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.policies_file): os.remove(tool.policies_file)
        if os.path.exists(tool.roles_file): os.remove(tool.roles_file)
        if os.path.exists(tool.data_domains_file): os.remove(tool.data_domains_file)
        print("\nCleanup complete.")