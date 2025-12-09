import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ServiceMeshSimulatorTool(BaseTool):
    """
    A tool that simulates service mesh management, allowing for defining
    services, deploying them, updating policies, and monitoring their status.
    """

    def __init__(self, tool_name: str = "ServiceMeshSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.services_file = os.path.join(self.data_dir, "service_definitions.json")
        self.policies_file = os.path.join(self.data_dir, "service_policies.json")
        
        # Service definitions: {service_id: {name: ..., version: ..., status: ..., policies: {}}}
        self.service_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.services_file, default={})
        # Policy configurations: {service_id: {policy_name: {rules: {}}}}
        self.policy_configurations: Dict[str, Dict[str, Any]] = self._load_data(self.policies_file, default={})

    @property
    def description(self) -> str:
        return "Simulates service mesh management: deploy services, update policies, and get status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_service", "deploy_service", "update_policy", "get_service_status", "list_services"]},
                "service_id": {"type": "string"},
                "name": {"type": "string"},
                "version": {"type": "string"},
                "traffic_routing_rules": {"type": "object", "description": "e.g., {'weight': 90, 'destination': 'v1'}"},
                "policy_name": {"type": "string"},
                "policy_rules": {"type": "object", "description": "e.g., {'retry_attempts': 3, 'timeout_ms': 5000}"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_services(self):
        with open(self.services_file, 'w') as f: json.dump(self.service_definitions, f, indent=2)

    def _save_policies(self):
        with open(self.policies_file, 'w') as f: json.dump(self.policy_configurations, f, indent=2)

    def define_service(self, service_id: str, name: str, version: str, traffic_routing_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Defines a new service within the mesh."""
        if service_id in self.service_definitions: raise ValueError(f"Service '{service_id}' already exists.")
        
        new_service = {
            "id": service_id, "name": name, "version": version,
            "traffic_routing_rules": traffic_routing_rules or {}, "status": "defined",
            "created_at": datetime.now().isoformat()
        }
        self.service_definitions[service_id] = new_service
        self._save_services()
        return new_service

    def deploy_service(self, service_id: str) -> Dict[str, Any]:
        """Simulates deploying a service to the mesh."""
        service = self.service_definitions.get(service_id)
        if not service: raise ValueError(f"Service '{service_id}' not found. Define it first.")
        
        service["status"] = "deployed"
        service["deployed_at"] = datetime.now().isoformat()
        self._save_services()
        return {"status": "success", "message": f"Service '{service_id}' deployed."}

    def update_policy(self, service_id: str, policy_name: str, policy_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Simulates updating a policy for a service."""
        service = self.service_definitions.get(service_id)
        if not service: raise ValueError(f"Service '{service_id}' not found.")
        
        if service_id not in self.policy_configurations: self.policy_configurations[service_id] = {}
        self.policy_configurations[service_id][policy_name] = policy_rules
        self._save_policies()
        return {"status": "success", "message": f"Policy '{policy_name}' updated for service '{service_id}'."}

    def get_service_status(self, service_id: str) -> Dict[str, Any]:
        """Retrieves the current status and policies applied to a service."""
        service = self.service_definitions.get(service_id)
        if not service: raise ValueError(f"Service '{service_id}' not found.")
        
        policies_applied = self.policy_configurations.get(service_id, {})
        
        return {"status": "success", "service_id": service_id, "service_details": service, "applied_policies": policies_applied}

    def list_services(self) -> List[Dict[str, Any]]:
        """Lists all defined services."""
        return list(self.service_definitions.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_service":
            service_id = kwargs.get('service_id')
            name = kwargs.get('name')
            version = kwargs.get('version')
            if not all([service_id, name, version]):
                raise ValueError("Missing 'service_id', 'name', or 'version' for 'define_service' operation.")
            return self.define_service(service_id, name, version, kwargs.get('traffic_routing_rules'))
        elif operation == "deploy_service":
            service_id = kwargs.get('service_id')
            if not service_id:
                raise ValueError("Missing 'service_id' for 'deploy_service' operation.")
            return self.deploy_service(service_id)
        elif operation == "update_policy":
            service_id = kwargs.get('service_id')
            policy_name = kwargs.get('policy_name')
            policy_rules = kwargs.get('policy_rules')
            if not all([service_id, policy_name, policy_rules]):
                raise ValueError("Missing 'service_id', 'policy_name', or 'policy_rules' for 'update_policy' operation.")
            return self.update_policy(service_id, policy_name, policy_rules)
        elif operation == "get_service_status":
            service_id = kwargs.get('service_id')
            if not service_id:
                raise ValueError("Missing 'service_id' for 'get_service_status' operation.")
            return self.get_service_status(service_id)
        elif operation == "list_services":
            # No additional kwargs required for list_services
            return self.list_services()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ServiceMeshSimulatorTool functionality...")
    temp_dir = "temp_service_mesh_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    mesh_tool = ServiceMeshSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a service
        print("\n--- Defining service 'auth-service' ---")
        mesh_tool.execute(operation="define_service", service_id="auth-service", name="Authentication Service", version="v1.0", traffic_routing_rules={"weight": 100, "destination": "v1.0"})
        print("Service defined.")

        # 2. Deploy the service
        print("\n--- Deploying 'auth-service' ---")
        mesh_tool.execute(operation="deploy_service", service_id="auth-service")
        print("Service deployed.")

        # 3. Update a policy for the service
        print("\n--- Updating 'retry_policy' for 'auth-service' ---")
        mesh_tool.execute(operation="update_policy", service_id="auth-service", policy_name="retry_policy", policy_rules={"retry_attempts": 3, "timeout_ms": 5000})
        print("Policy updated.")

        # 4. Get service status
        print("\n--- Getting status for 'auth-service' ---")
        status = mesh_tool.execute(operation="get_service_status", service_id="auth-service")
        print(json.dumps(status, indent=2))

        # 5. List all services
        print("\n--- Listing all services ---")
        all_services = mesh_tool.execute(operation="list_services", service_id="any") # service_id is not used for list_services
        print(json.dumps(all_services, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")