import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SASEManagerSimulatorTool(BaseTool):
    """
    A tool that simulates Secure Access Service Edge (SASE) management,
    allowing for defining security policies, applying them to users,
    and managing network access to resources.
    """

    def __init__(self, tool_name: str = "SASEManagerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.policies_file = os.path.join(self.data_dir, "sase_security_policies.json")
        self.access_file = os.path.join(self.data_dir, "sase_user_access_records.json")
        
        # Security policies: {policy_id: {name: ..., rules: []}}
        self.security_policies: Dict[str, Dict[str, Any]] = self._load_data(self.policies_file, default={})
        # User access records: {user_id: {resource_id: {policy_id: ..., status: 'allowed'|'denied'}}}
        self.user_access_records: Dict[str, Dict[str, Any]] = self._load_data(self.access_file, default={})

    @property
    def description(self) -> str:
        return "Simulates SASE management: configure security policies, manage network access, and get user access status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_security_policy", "apply_policy_to_user", "manage_network_access", "get_user_access_status"]},
                "policy_id": {"type": "string"},
                "name": {"type": "string"},
                "rules": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"user_group": {"type": "string"}, "resource_type": {"type": "string"}, "access": {"type": "string"}}},
                    "description": "e.g., [{'user_group': 'developers', 'resource_type': 'code_repo', 'access': 'read_only'}]"
                },
                "user_id": {"type": "string"},
                "resource_id": {"type": "string"},
                "action": {"type": "string", "enum": ["allow", "deny"]}
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

    def _save_policies(self):
        with open(self.policies_file, 'w') as f: json.dump(self.security_policies, f, indent=2)

    def _save_access_records(self):
        with open(self.access_file, 'w') as f: json.dump(self.user_access_records, f, indent=2)

    def define_security_policy(self, policy_id: str, name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new security policy."""
        if policy_id in self.security_policies: raise ValueError(f"Policy '{policy_id}' already exists.")
        
        new_policy = {
            "id": policy_id, "name": name, "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.security_policies[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def apply_policy_to_user(self, policy_id: str, user_id: str) -> Dict[str, Any]:
        """Simulates applying a security policy to a user."""
        policy = self.security_policies.get(policy_id)
        if not policy: raise ValueError(f"Policy '{policy_id}' not found. Define it first.")
        
        if user_id not in self.user_access_records: self.user_access_records[user_id] = {}
        
        # For simplicity, we'll just record that the policy is applied to the user
        # A real SASE would evaluate rules against user attributes and resource attributes
        self.user_access_records[user_id]["applied_policy"] = policy_id
        self._save_access_records()
        return {"status": "success", "message": f"Policy '{policy_id}' applied to user '{user_id}'."}

    def manage_network_access(self, user_id: str, resource_id: str, action: str) -> Dict[str, Any]:
        """Simulates managing network access for a user to a resource based on policies."""
        if user_id not in self.user_access_records: raise ValueError(f"User '{user_id}' has no policies applied.")
        
        applied_policy_id = self.user_access_records[user_id].get("applied_policy")
        if not applied_policy_id: raise ValueError(f"No policy applied to user '{user_id}'.")
        
        policy = self.security_policies.get(applied_policy_id)
        if not policy: raise ValueError(f"Applied policy '{applied_policy_id}' not found.")

        access_granted = False
        reason = "No matching rule found."
        
        for rule in policy["rules"]:
            # Simplified rule evaluation: check if resource_type matches and action is allowed
            if rule.get("resource_type") == resource_id.split('_')[0] and rule.get("access") == action:
                access_granted = True
                reason = f"Access {action}ed by policy rule."
                break
        
        self.user_access_records[user_id][resource_id] = {"status": "allowed" if access_granted else "denied", "timestamp": datetime.now().isoformat()}
        self._save_access_records()
        
        return {"status": "success", "user_id": user_id, "resource_id": resource_id, "access_granted": access_granted, "reason": reason}

    def get_user_access_status(self, user_id: str, resource_id: str) -> Dict[str, Any]:
        """Retrieves the access status for a user to a specific resource."""
        if user_id not in self.user_access_records: raise ValueError(f"User '{user_id}' not found.")
        
        access_status = self.user_access_records[user_id].get(resource_id)
        if not access_status: return {"status": "info", "message": f"No specific access record for user '{user_id}' to resource '{resource_id}'."}
        
        return {"status": "success", "user_id": user_id, "resource_id": resource_id, "access_status": access_status}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_security_policy":
            policy_id = kwargs.get('policy_id')
            name = kwargs.get('name')
            rules = kwargs.get('rules')
            if not all([policy_id, name, rules]):
                raise ValueError("Missing 'policy_id', 'name', or 'rules' for 'define_security_policy' operation.")
            return self.define_security_policy(policy_id, name, rules)
        elif operation == "apply_policy_to_user":
            policy_id = kwargs.get('policy_id')
            user_id = kwargs.get('user_id')
            if not all([policy_id, user_id]):
                raise ValueError("Missing 'policy_id' or 'user_id' for 'apply_policy_to_user' operation.")
            return self.apply_policy_to_user(policy_id, user_id)
        elif operation == "manage_network_access":
            user_id = kwargs.get('user_id')
            resource_id = kwargs.get('resource_id')
            action = kwargs.get('action')
            if not all([user_id, resource_id, action]):
                raise ValueError("Missing 'user_id', 'resource_id', or 'action' for 'manage_network_access' operation.")
            return self.manage_network_access(user_id, resource_id, action)
        elif operation == "get_user_access_status":
            user_id = kwargs.get('user_id')
            resource_id = kwargs.get('resource_id')
            if not all([user_id, resource_id]):
                raise ValueError("Missing 'user_id' or 'resource_id' for 'get_user_access_status' operation.")
            return self.get_user_access_status(user_id, resource_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SASEManagerSimulatorTool functionality...")
    temp_dir = "temp_sase_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sase_tool = SASEManagerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a security policy
        print("\n--- Defining security policy 'dev_access_policy' ---")
        rules = [
            {"user_group": "developers", "resource_type": "code_repo", "access": "allow"},
            {"user_group": "developers", "resource_type": "prod_db", "access": "deny"}
        ]
        sase_tool.execute(operation="define_security_policy", policy_id="dev_access_policy", name="Developer Access Policy", rules=rules)
        print("Policy defined.")

        # 2. Apply policy to a user
        print("\n--- Applying 'dev_access_policy' to 'user_alice' ---")
        sase_tool.execute(operation="apply_policy_to_user", policy_id="dev_access_policy", user_id="user_alice")
        print("Policy applied.")

        # 3. Manage network access (allowed)
        print("\n--- Managing network access for 'user_alice' to 'code_repo_main' (allowed) ---")
        access_result1 = sase_tool.execute(operation="manage_network_access", user_id="user_alice", resource_id="code_repo_main", action="allow")
        print(json.dumps(access_result1, indent=2))

        # 4. Manage network access (denied)
        print("\n--- Managing network access for 'user_alice' to 'prod_db_main' (denied) ---")
        access_result2 = sase_tool.execute(operation="manage_network_access", user_id="user_alice", resource_id="prod_db_main", action="allow") # Attempt to allow
        print(json.dumps(access_result2, indent=2))

        # 5. Get user access status
        print("\n--- Getting user access status for 'user_alice' to 'code_repo_main' ---")
        status = sase_tool.execute(operation="get_user_access_status", user_id="user_alice", resource_id="code_repo_main")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")