import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PolicyAsCodeEnforcerSimulatorTool(BaseTool):
    """
    A tool that simulates policy-as-code enforcement, allowing for defining
    policies, configuring resources, auditing compliance, and simulating enforcement.
    """

    def __init__(self, tool_name: str = "PolicyAsCodeEnforcerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.policies_file = os.path.join(self.data_dir, "policy_definitions.json")
        self.resources_file = os.path.join(self.data_dir, "resource_configurations.json")
        
        # Policy definitions: {policy_id: {name: ..., rules: []}}
        self.policy_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.policies_file, default={})
        # Resource configurations: {resource_id: {type: ..., config: {}}}
        self.resource_configurations: Dict[str, Dict[str, Any]] = self._load_data(self.resources_file, default={})

    @property
    def description(self) -> str:
        return "Simulates policy-as-code enforcement: define policies, configure resources, audit, and enforce."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_policy", "configure_resource", "audit_compliance", "enforce_policy", "list_policies", "list_resources"]},
                "policy_id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "rules": {"type": "array", "items": {"type": "object"}, "description": "e.g., [{'resource_type': 's3_bucket', 'attribute': 'public_access', 'must_be': False}]"},
                "resource_id": {"type": "string"},
                "resource_type": {"type": "string"},
                "configuration": {"type": "object", "description": "The configuration of the resource."}
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
        with open(self.policies_file, 'w') as f: json.dump(self.policy_definitions, f, indent=2)

    def _save_resources(self):
        with open(self.resources_file, 'w') as f: json.dump(self.resource_configurations, f, indent=2)

    def define_policy(self, policy_id: str, name: str, description: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new policy with its rules."""
        if policy_id in self.policy_definitions: raise ValueError(f"Policy '{policy_id}' already exists.")
        
        new_policy = {
            "id": policy_id, "name": name, "description": description,
            "rules": rules, "created_at": datetime.now().isoformat()
        }
        self.policy_definitions[policy_id] = new_policy
        self._save_policies()
        return new_policy

    def configure_resource(self, resource_id: str, resource_type: str, configuration: Dict[str, Any]) -> Dict[str, Any]:
        """Configures a simulated resource."""
        if resource_id in self.resource_configurations: raise ValueError(f"Resource '{resource_id}' already exists.")
        
        new_resource = {
            "id": resource_id, "type": resource_type, "configuration": configuration,
            "created_at": datetime.now().isoformat()
        }
        self.resource_configurations[resource_id] = new_resource
        self._save_resources()
        return new_resource

    def audit_compliance(self, policy_id: str, resource_id: str) -> Dict[str, Any]:
        """Audits a resource's compliance against a specific policy."""
        policy = self.policy_definitions.get(policy_id)
        if not policy: raise ValueError(f"Policy '{policy_id}' not found.")
        resource = self.resource_configurations.get(resource_id)
        if not resource: raise ValueError(f"Resource '{resource_id}' not found.")
        
        violations = []
        for rule in policy["rules"]:
            if rule.get("resource_type") != resource["type"]: continue # Rule not applicable to this resource type
            
            attribute = rule["attribute"]
            must_be_value = rule.get("must_be")
            must_not_be_value = rule.get("must_not_be")
            
            resource_attr_value = resource["configuration"].get(attribute)
            
            if must_be_value is not None and resource_attr_value != must_be_value:
                violations.append(f"Violation: Attribute '{attribute}' is '{resource_attr_value}', but must be '{must_be_value}'.")
            if must_not_be_value is not None and resource_attr_value == must_not_be_value:
                violations.append(f"Violation: Attribute '{attribute}' is '{resource_attr_value}', but must NOT be '{must_not_be_value}'.")
        
        is_compliant = not violations
        return {
            "policy_id": policy_id, "resource_id": resource_id,
            "is_compliant": is_compliant, "violations": violations
        }

    def enforce_policy(self, policy_id: str, resource_id: str) -> Dict[str, Any]:
        """Simulates enforcing a policy on a resource."""
        compliance_report = self.audit_compliance(policy_id, resource_id)
        
        if compliance_report["is_compliant"]:
            return {"status": "success", "message": f"Resource '{resource_id}' is already compliant with policy '{policy_id}'."}
        
        # Simulate enforcement by updating the resource configuration to comply
        resource = self.resource_configurations[resource_id]
        policy = self.policy_definitions[policy_id]
        
        for rule in policy["rules"]:
            if rule.get("resource_type") == resource["type"]:
                attribute = rule["attribute"]
                must_be_value = rule.get("must_be")
                must_not_be_value = rule.get("must_not_be")
                
                if must_be_value is not None:
                    resource["configuration"][attribute] = must_be_value
                elif must_not_be_value is not None and resource["configuration"].get(attribute) == must_not_be_value:
                    resource["configuration"][attribute] = "compliant_value" # Generic compliant value
        
        self._save_resources()
        return {"status": "success", "message": f"Simulated: Policy '{policy_id}' enforced on resource '{resource_id}'. Configuration updated to comply.", "new_configuration": resource["configuration"]}

    def list_policies(self) -> List[Dict[str, Any]]:
        """Lists all defined policies."""
        return list(self.policy_definitions.values())

    def list_resources(self) -> List[Dict[str, Any]]:
        """Lists all configured resources."""
        return list(self.resource_configurations.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_policy":
            policy_id = kwargs.get('policy_id')
            name = kwargs.get('name')
            description = kwargs.get('description')
            rules = kwargs.get('rules')
            if not all([policy_id, name, description, rules]):
                raise ValueError("Missing 'policy_id', 'name', 'description', or 'rules' for 'define_policy' operation.")
            return self.define_policy(policy_id, name, description, rules)
        elif operation == "configure_resource":
            resource_id = kwargs.get('resource_id')
            resource_type = kwargs.get('resource_type')
            configuration = kwargs.get('configuration')
            if not all([resource_id, resource_type, configuration]):
                raise ValueError("Missing 'resource_id', 'resource_type', or 'configuration' for 'configure_resource' operation.")
            return self.configure_resource(resource_id, resource_type, configuration)
        elif operation == "audit_compliance":
            policy_id = kwargs.get('policy_id')
            resource_id = kwargs.get('resource_id')
            if not all([policy_id, resource_id]):
                raise ValueError("Missing 'policy_id' or 'resource_id' for 'audit_compliance' operation.")
            return self.audit_compliance(policy_id, resource_id)
        elif operation == "enforce_policy":
            policy_id = kwargs.get('policy_id')
            resource_id = kwargs.get('resource_id')
            if not all([policy_id, resource_id]):
                raise ValueError("Missing 'policy_id' or 'resource_id' for 'enforce_policy' operation.")
            return self.enforce_policy(policy_id, resource_id)
        elif operation == "list_policies":
            return self.list_policies()
        elif operation == "list_resources":
            return self.list_resources()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PolicyAsCodeEnforcerSimulatorTool functionality...")
    temp_dir = "temp_policy_as_code_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    policy_tool = PolicyAsCodeEnforcerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a security policy for S3 buckets
        print("\n--- Defining security policy 's3_security_policy' ---")
        policy_tool.execute(operation="define_policy", policy_id="s3_security_policy", name="S3 Public Access Policy",
                            description="Ensures S3 buckets do not have public access.",
                            rules=[{"resource_type": "s3_bucket", "attribute": "public_access", "must_be": False}])
        print("Policy defined.")

        # 2. Configure a compliant S3 bucket
        print("\n--- Configuring compliant S3 bucket 'my-private-bucket' ---")
        policy_tool.execute(operation="configure_resource", resource_id="my-private-bucket", resource_type="s3_bucket",
                            configuration={"public_access": False, "encryption": True})
        print("Compliant resource configured.")

        # 3. Configure a non-compliant S3 bucket
        print("\n--- Configuring non-compliant S3 bucket 'my-public-bucket' ---")
        policy_tool.execute(operation="configure_resource", resource_id="my-public-bucket", resource_type="s3_bucket",
                            configuration={"public_access": True, "encryption": False})
        print("Non-compliant resource configured.")

        # 4. Audit compliance for both resources
        print("\n--- Auditing compliance for 'my-private-bucket' ---")
        audit1 = policy_tool.execute(operation="audit_compliance", policy_id="s3_security_policy", resource_id="my-private-bucket")
        print(json.dumps(audit1, indent=2))

        print("\n--- Auditing compliance for 'my-public-bucket' ---")
        audit2 = policy_tool.execute(operation="audit_compliance", policy_id="s3_security_policy", resource_id="my-public-bucket")
        print(json.dumps(audit2, indent=2))

        # 5. Enforce policy on the non-compliant resource
        print("\n--- Enforcing policy on 'my-public-bucket' ---")
        enforce_result = policy_tool.execute(operation="enforce_policy", policy_id="s3_security_policy", resource_id="my-public-bucket")
        print(json.dumps(enforce_result, indent=2))

        # 6. Audit again to confirm enforcement
        print("\n--- Auditing compliance for 'my-public-bucket' after enforcement ---")
        audit3 = policy_tool.execute(operation="audit_compliance", policy_id="s3_security_policy", resource_id="my-public-bucket")
        print(json.dumps(audit3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")