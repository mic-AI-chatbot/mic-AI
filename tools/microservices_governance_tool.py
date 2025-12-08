import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Define governance policies as a dictionary of rules
POLICIES = {
    "security_policy": {
        "description": "Ensures services adhere to basic security standards.",
        "rules": [
            {"attribute": "https_only", "must_be": True, "message": "Service must enforce HTTPS."},
            {"attribute": "is_public", "must_be": False, "message": "Service should not be publicly exposed without an API gateway."}
        ]
    },
    "operations_policy": {
        "description": "Ensures services are operationally ready.",
        "rules": [
            {"attribute": "has_monitoring", "must_be": True, "message": "Service must have monitoring enabled."},
            {"attribute": "owner_team", "must_not_be": None, "message": "Service must have an owner team defined."}
        ]
    }
}

class MicroserviceGovernanceTool(BaseTool):
    """
    A tool to manage a microservice catalog and check for compliance
    against predefined governance policies.
    """

    def __init__(self, tool_name: str = "MicroserviceGovernance", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.catalog_file = os.path.join(self.data_dir, "service_catalog.json")
        self.catalog: Dict[str, Dict[str, Any]] = self._load_data(self.catalog_file, default={})

    @property
    def description(self) -> str:
        return "Manages a service catalog and checks compliance against governance policies."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["register_service", "check_compliance", "enforce_policy"]},
                "service_name": {"type": "string"},
                "metadata": {"type": "object", "description": "Attributes of the service, e.g., {'owner_team': 'backend'}"},
                "policy_name": {"type": "string", "enum": list(POLICIES.keys())}
            },
            "required": ["operation", "service_name"]
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
        with open(self.catalog_file, 'w') as f: json.dump(self.catalog, f, indent=2)

    def register_service(self, service_name: str, metadata: Dict) -> Dict:
        """Registers a new service and its metadata in the catalog."""
        if service_name in self.catalog:
            raise ValueError(f"Service '{service_name}' is already registered.")
        
        self.catalog[service_name] = {"metadata": metadata, "registered_at": datetime.now().isoformat()}
        self._save_data()
        return self.catalog[service_name]

    def check_compliance(self, service_name: str, policy_name: str) -> Dict:
        """Checks a service's compliance against a specific policy."""
        service = self.catalog.get(service_name)
        if not service: raise ValueError(f"Service '{service_name}' not found.")
        
        policy = POLICIES.get(policy_name)
        if not policy: raise ValueError(f"Policy '{policy_name}' not found.")

        failures = []
        for rule in policy["rules"]:
            attr = rule["attribute"]
            service_attr_value = service["metadata"].get(attr)
            
            if "must_be" in rule and service_attr_value != rule["must_be"]:
                failures.append(f"FAIL: Attribute '{attr}' is '{service_attr_value}', but must be '{rule['must_be']}'. ({rule['message']})")
            if "must_not_be" in rule and service_attr_value == rule["must_not_be"]:
                failures.append(f"FAIL: Attribute '{attr}' must not be '{rule['must_not_be']}'. ({rule['message']})")
        
        is_compliant = not failures
        return {
            "service_name": service_name, "policy_name": policy_name,
            "is_compliant": is_compliant, "failures": failures
        }

    def enforce_policy(self, service_name: str, policy_name: str) -> Dict:
        """Checks compliance and simulates an enforcement action if non-compliant."""
        compliance_report = self.check_compliance(service_name, policy_name)
        
        if compliance_report["is_compliant"]:
            return {"status": "success", "message": f"Service '{service_name}' is already compliant with '{policy_name}'."}
        
        owner = self.catalog.get(service_name, {}).get("metadata", {}).get("owner_team", "unassigned_team")
        message = f"Simulated Enforcement: Alert sent to team '{owner}' to fix {len(compliance_report['failures'])} compliance issues."
        
        return {"status": "enforcement_simulated", "message": message, "compliance_report": compliance_report}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "register_service": self.register_service,
            "check_compliance": self.check_compliance,
            "enforce_policy": self.enforce_policy
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MicroserviceGovernanceTool functionality...")
    temp_dir = "temp_governance_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    governance_tool = MicroserviceGovernanceTool(data_dir=temp_dir)
    
    try:
        # 1. Register two services, one compliant and one not
        print("\n--- Registering services ---")
        governance_tool.execute(operation="register_service", service_name="auth-service", metadata={
            "owner_team": "security-team", "https_only": True, "is_public": False, "has_monitoring": True
        })
        governance_tool.execute(operation="register_service", service_name="legacy-service", metadata={
            "owner_team": None, "https_only": False, "is_public": False, "has_monitoring": False
        })
        print("Services registered.")

        # 2. Check compliance for the compliant service
        print("\n--- Checking compliance for 'auth-service' against 'operations_policy' ---")
        compliant_report = governance_tool.execute(operation="check_compliance", service_name="auth-service", policy_name="operations_policy")
        print(json.dumps(compliant_report, indent=2))

        # 3. Check compliance for the non-compliant service
        print("\n--- Checking compliance for 'legacy-service' against 'operations_policy' ---")
        non_compliant_report = governance_tool.execute(operation="check_compliance", service_name="legacy-service", policy_name="operations_policy")
        print(json.dumps(non_compliant_report, indent=2))

        # 4. Enforce the policy on the non-compliant service
        print("\n--- Enforcing 'operations_policy' on 'legacy-service' ---")
        enforcement_result = governance_tool.execute(operation="enforce_policy", service_name="legacy-service", policy_name="operations_policy")
        print(json.dumps(enforcement_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")