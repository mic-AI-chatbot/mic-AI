import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated policies and access logs
policies: Dict[str, Dict[str, Any]] = {}
access_logs: List[Dict[str, Any]] = []

class ZeroTrustSecurityManagerTool(BaseTool):
    """
    A tool to simulate a Zero Trust Security Manager.
    """
    def __init__(self, tool_name: str = "zero_trust_security_manager_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates Zero Trust security: define policies, enforce, monitor access, and revoke."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'define_policy', 'enforce_policy', 'monitor_access', 'revoke_access', 'list_policies', 'get_access_logs'."
                },
                "policy_id": {"type": "string", "description": "The unique ID of the policy."},
                "resource_id": {"type": "string", "description": "The ID of the resource (e.g., 'server_A', 'database_X')."},
                "user_id": {"type": "string", "description": "The ID of the user."},
                "conditions": {
                    "type": "object",
                    "description": "Conditions for the policy (e.g., {'ip_range': '192.168.1.0/24', 'time_of_day': 'business_hours'})."
                },
                "effect": {
                    "type": "string",
                    "description": "The effect of the policy ('allow', 'deny')."
                },
                "access_type": {"type": "string", "description": "The type of access being monitored (e.g., 'read', 'write', 'login')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            policy_id = kwargs.get("policy_id")
            resource_id = kwargs.get("resource_id")
            user_id = kwargs.get("user_id")

            if action in ['define_policy', 'enforce_policy', 'revoke_access'] and not policy_id:
                raise ValueError(f"'policy_id' is required for the '{action}' action.")
            if action in ['enforce_policy', 'monitor_access', 'revoke_access'] and not resource_id:
                raise ValueError(f"'resource_id' is required for the '{action}' action.")
            if action in ['enforce_policy', 'monitor_access', 'revoke_access'] and not user_id:
                raise ValueError(f"'user_id' is required for the '{action}' action.")

            actions = {
                "define_policy": self._define_policy,
                "enforce_policy": self._enforce_policy,
                "monitor_access": self._monitor_access,
                "revoke_access": self._revoke_access,
                "list_policies": self._list_policies,
                "get_access_logs": self._get_access_logs,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in ZeroTrustSecurityManagerTool: {e}")
            return {"error": str(e)}

    def _define_policy(self, policy_id: str, resource_id: str, user_id: str, conditions: Dict[str, Any], effect: str, **kwargs) -> Dict:
        if not all([resource_id, user_id, conditions, effect]):
            raise ValueError("All policy details (resource_id, user_id, conditions, effect) are required.")
        if policy_id in policies:
            raise ValueError(f"Policy '{policy_id}' already exists.")
        if effect not in ["allow", "deny"]:
            raise ValueError("Policy effect must be 'allow' or 'deny'.")
            
        new_policy = {
            "id": policy_id,
            "resource_id": resource_id,
            "user_id": user_id,
            "conditions": conditions,
            "effect": effect,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        policies[policy_id] = new_policy
        logger.info(f"Policy '{policy_id}' defined.")
        return {"message": "Policy defined successfully.", "details": new_policy}

    def _enforce_policy(self, policy_id: str, resource_id: str, user_id: str, **kwargs) -> Dict:
        if policy_id not in policies:
            raise ValueError(f"Policy '{policy_id}' not found.")
            
        policy = policies[policy_id]
        
        # Simulate policy enforcement based on conditions
        access_granted = True
        if policy["effect"] == "deny":
            # Simple simulation: deny if policy is active and matches resource/user
            if policy["resource_id"] == resource_id and policy["user_id"] == user_id:
                access_granted = False
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "resource_id": resource_id,
            "policy_id": policy_id,
            "access_granted": access_granted,
            "reason": "Policy enforcement simulation."
        }
        access_logs.append(log_entry)
        
        return {"message": "Policy enforcement simulated.", "access_granted": access_granted, "log_entry": log_entry}

    def _monitor_access(self, resource_id: str, user_id: str, access_type: str, **kwargs) -> Dict:
        # Simulate access decision based on random chance and existing policies
        access_granted = random.choice([True, False])  # nosec B311
        
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "resource_id": resource_id,
            "access_type": access_type,
            "access_granted": access_granted,
            "reason": "Access monitoring simulation."
        }
        access_logs.append(log_entry)
        return {"message": "Access monitored.", "log_entry": log_entry}

    def _revoke_access(self, policy_id: str, resource_id: str, user_id: str, **kwargs) -> Dict:
        if policy_id not in policies:
            raise ValueError(f"Policy '{policy_id}' not found.")
            
        policy = policies[policy_id]
        if policy["resource_id"] != resource_id or policy["user_id"] != user_id:
            raise ValueError("Policy does not match resource/user for revocation.")
            
        policy["status"] = "inactive"
        policy["revoked_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Access revoked for user '{user_id}' on resource '{resource_id}' via policy '{policy_id}'.")
        return {"message": "Access revoked successfully.", "policy_id": policy_id, "status": "inactive"}

    def _list_policies(self, **kwargs) -> Dict:
        if not policies:
            return {"message": "No policies defined yet."}
        return {"policies": list(policies.values())}

    def _get_access_logs(self, **kwargs) -> Dict:
        if not access_logs:
            return {"message": "No access logs recorded yet."}
        return {"access_logs": access_logs}