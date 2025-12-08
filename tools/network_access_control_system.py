import logging
import os
import json
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NetworkAccessControlSimulatorTool(BaseTool):
    """
    A tool that simulates network access control by managing an Access Control List (ACL)
    to grant, revoke, and check user access to network resources.
    """

    def __init__(self, tool_name: str = "NetworkAccessControlSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.acl_file = os.path.join(self.data_dir, "access_control_list.json")
        # ACL structure: {resource_name: [user_id1, user_id2, ...]}\n        self.acl: Dict[str, List[str]] = self._load_data(self.acl_file, default={})

    @property
    def description(self) -> str:
        return "Simulates network access control: grant, revoke, and check user access to resources."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["grant_access", "revoke_access", "check_access", "list_access"]},
                "user_id": {"type": "string", "description": "The ID of the user."},
                "resource_name": {"type": "string", "description": "The name of the network resource."},
                "list_by": {"type": "string", "enum": ["user", "resource"], "description": "List access by user or by resource."}
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

    def _save_data(self):
        with open(self.acl_file, 'w') as f: json.dump(self.acl, f, indent=2)

    def grant_access(self, user_id: str, resource_name: str) -> Dict[str, Any]:
        """Grants a user access to a specific network resource."""
        if resource_name not in self.acl:
            self.acl[resource_name] = []
        
        if user_id in self.acl[resource_name]:
            return {"status": "info", "message": f"User '{user_id}' already has access to '{resource_name}'."}
        
        self.acl[resource_name].append(user_id)
        self._save_data()
        return {"status": "success", "message": f"User '{user_id}' granted access to '{resource_name}'."}

    def revoke_access(self, user_id: str, resource_name: str) -> Dict[str, Any]:
        """Revokes a user's access to a specific network resource."""
        if resource_name not in self.acl or user_id not in self.acl[resource_name]:
            return {"status": "info", "message": f"User '{user_id}' does not have access to '{resource_name}'."}
        
        self.acl[resource_name].remove(user_id)
        self._save_data()
        return {"status": "success", "message": f"User '{user_id}' revoked access from '{resource_name}'."}

    def check_access(self, user_id: str, resource_name: str) -> Dict[str, Any]:
        """Checks if a user has access to a specific network resource."""
        has_access = resource_name in self.acl and user_id in self.acl[resource_name]
        return {"user_id": user_id, "resource_name": resource_name, "has_access": has_access}

    def list_access(self, list_by: str, user_id: Optional[str] = None, resource_name: Optional[str] = None) -> Dict[str, Any]:
        """Lists access permissions by user or by resource."""
        if list_by == "user":
            if not user_id: raise ValueError("user_id is required when listing by user.")
            resources_for_user = [res for res, users in self.acl.items() if user_id in users]
            return {"user_id": user_id, "resources_accessed": resources_for_user}
        elif list_by == "resource":
            if not resource_name: raise ValueError("resource_name is required when listing by resource.")
            users_for_resource = self.acl.get(resource_name, [])
            return {"resource_name": resource_name, "users_with_access": users_for_resource}
        else:
            raise ValueError("Invalid 'list_by' parameter. Must be 'user' or 'resource'.")

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "grant_access": self.grant_access,
            "revoke_access": self.revoke_access,
            "check_access": self.check_access,
            "list_access": self.list_access
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating NetworkAccessControlSimulatorTool functionality...")
    temp_dir = "temp_nac_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    nac_tool = NetworkAccessControlSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Grant access
        print("\n--- Granting access to 'user_alice' for 'server_A' ---")
        nac_tool.execute(operation="grant_access", user_id="user_alice", resource_name="server_A")
        print("Access granted.")

        # 2. Check access
        print("\n--- Checking access for 'user_alice' to 'server_A' ---")
        check1 = nac_tool.execute(operation="check_access", user_id="user_alice", resource_name="server_A")
        print(json.dumps(check1, indent=2))

        # 3. Grant access to another user for the same resource
        print("\n--- Granting access to 'user_bob' for 'server_A' ---")
        nac_tool.execute(operation="grant_access", user_id="user_bob", resource_name="server_A")
        print("Access granted.")

        # 4. List access for 'server_A'\n        print("\n--- Listing access for 'server_A' ---")
        list_res = nac_tool.execute(operation="list_access", list_by="resource", resource_name="server_A")
        print(json.dumps(list_res, indent=2))

        # 5. Revoke access
        print("\n--- Revoking access for 'user_alice' from 'server_A' ---")
        nac_tool.execute(operation="revoke_access", user_id="user_alice", resource_name="server_A")
        print("Access revoked.")

        # 6. Check access again for 'user_alice'\n        print("\n--- Checking access for 'user_alice' to 'server_A' after revocation ---")
        check2 = nac_tool.execute(operation="check_access", user_id="user_alice", resource_name="server_A")
        print(json.dumps(check2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")