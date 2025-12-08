import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DevEnvironmentProvisionerTool(BaseTool):
    """
    A tool for simulating the provisioning and management of development environments.
    """

    def __init__(self, tool_name: str = "dev_environment_provisioner"):
        super().__init__(tool_name)
        self.environments_file = "dev_environments.json"
        self.environments: Dict[str, Dict[str, Any]] = self._load_environments()

    @property
    def description(self) -> str:
        return "Simulates provisioning and managing development environments: provisions, deprovisions, and lists environments."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The environment provisioning operation to perform.",
                    "enum": ["provision_environment", "deprovision_environment", "get_environment_status", "list_environments"]
                },
                "env_id": {"type": "string"},
                "env_name": {"type": "string"},
                "config_template": {"type": "string"},
                "owner": {"type": "string"},
                "resources": {"type": "object"},
                "description": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_environments(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.environments_file):
            with open(self.environments_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted environments file '{self.environments_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_environments(self) -> None:
        with open(self.environments_file, 'w') as f:
            json.dump(self.environments, f, indent=4)

    def _provision_environment(self, env_id: str, env_name: str, config_template: str, owner: str, resources: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([env_id, env_name, config_template, owner, resources]):
            raise ValueError("Environment ID, name, config template, owner, and resources cannot be empty.")
        if env_id in self.environments: raise ValueError(f"Environment '{env_id}' already exists.")

        new_env = {
            "env_id": env_id, "env_name": env_name, "description": description,
            "config_template": config_template, "owner": owner, "resources": resources,
            "status": "provisioned", "provisioned_at": datetime.now().isoformat()
        }
        self.environments[env_id] = new_env
        self._save_environments()
        return new_env

    def _deprovision_environment(self, env_id: str) -> Dict[str, Any]:
        env = self.environments.get(env_id)
        if not env: raise ValueError(f"Environment '{env_id}' not found.")
        if env["status"] == "deprovisioned": raise ValueError(f"Environment '{env_id}' is already deprovisioned.")

        env["status"] = "deprovisioned"
        env["deprovisioned_at"] = datetime.now().isoformat()
        self._save_environments()
        return env

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "provision_environment":
            return self._provision_environment(kwargs.get("env_id"), kwargs.get("env_name"), kwargs.get("config_template"), kwargs.get("owner"), kwargs.get("resources"), kwargs.get("description"))
        elif operation == "deprovision_environment":
            return self._deprovision_environment(kwargs.get("env_id"))
        elif operation == "get_environment_status":
            return self.environments.get(kwargs.get("env_id"))
        elif operation == "list_environments":
            return list(self.environments.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DevEnvironmentProvisionerTool functionality...")
    tool = DevEnvironmentProvisionerTool()
    
    try:
        print("\n--- Provisioning Environment ---")
        tool.execute(operation="provision_environment", env_id="web_dev_alice", env_name="Alice's Web Dev Env", config_template="frontend_stack", owner="Alice", resources={"cpu": "2_cores", "ram": "8GB"})
        
        print("\n--- Deprovisioning Environment ---")
        deprovision_result = tool.execute(operation="deprovision_environment", env_id="web_dev_alice")
        print(json.dumps(deprovision_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.environments_file): os.remove(tool.environments_file)
        print("\nCleanup complete.")