import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# --- In-memory storage for AI Governance Simulation ---
class AIGovernanceState:
    def __init__(self):
        self.policies: Dict[str, Any] = {
            "data_privacy_v1": {
                "policy_name": "Data Privacy Policy",
                "active": True,
                "rules": [
                    {"rule_id": "DP-1", "description": "Prohibits use of Personally Identifiable Information (PII) in training data.", "keywords": ["pii", "personal data", "user data", "names", "addresses"]},
                    {"rule_id": "DP-2", "description": "Requires all data to be anonymized before use.", "keywords": ["anonymize", "pseudonymize"]},
                ]
            }
        }
        self.systems: Dict[str, str] = {
            "recommendation_engine_v2": "A recommendation engine trained on user interaction history.",
            "facial_recognition_alpha": "A facial recognition model trained on a public dataset of faces."
        }

governance_state = AIGovernanceState()

class DefineAIGovernancePolicyTool(BaseTool):
    """Tool to define a new, structured AI governance policy."""
    def __init__(self, tool_name="define_ai_governance_policy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a new AI governance policy with a structured set of rules, including descriptions and violation keywords."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "A unique identifier for the new policy."},
                "policy_name": {"type": "string", "description": "The name of the policy."},
                "rules": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "rule_id": {"type": "string"},
                            "description": {"type": "string"},
                            "keywords": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["rule_id", "description", "keywords"]
                    },
                    "description": "A list of structured rules for the policy."
                }
            },
            "required": ["policy_id", "policy_name", "rules"]
        }

    def execute(self, policy_id: str, policy_name: str, rules: List[Dict[str, Any]], **kwargs: Any) -> str:
        if policy_id in governance_state.policies:
            return json.dumps({"error": f"Policy with ID '{policy_id}' already exists."}, indent=2)
            
        governance_state.policies[policy_id] = {
            "policy_name": policy_name,
            "rules": rules,
            "active": True
        }
        report = {
            "message": f"AI Governance Policy '{policy_name}' defined successfully.",
            "policy_id": policy_id
        }
        return json.dumps(report, indent=2)

class EnforceAIPolicyTool(BaseTool):
    """Tool to enforce an AI governance policy against a system operation."""
    def __init__(self, tool_name="enforce_ai_policy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Enforces an AI governance policy by checking a system's operation description against the policy's rule keywords."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "The ID of the policy to enforce."},
                "ai_system_operation": {"type": "string", "description": "A description of the AI system or operation to check."}
            },
            "required": ["policy_id", "ai_system_operation"]
        }

    def execute(self, policy_id: str, ai_system_operation: str, **kwargs: Any) -> str:
        if policy_id not in governance_state.policies:
            return json.dumps({"error": f"Policy with ID '{policy_id}' not found."}, indent=2)
            
        policy = governance_state.policies[policy_id]
        operation_lower = ai_system_operation.lower()
        
        violations = []
        for rule in policy["rules"]:
            if any(keyword in operation_lower for keyword in rule["keywords"]):
                violations.append({
                    "rule_id": rule["rule_id"],
                    "description": rule["description"],
                    "triggered_keyword": [k for k in rule["keywords"] if k in operation_lower][0]
                })
        
        is_compliant = not violations
        report = {
            "policy_id": policy_id,
            "policy_name": policy["policy_name"],
            "ai_system_operation": ai_system_operation,
            "compliance_status": "Compliant" if is_compliant else "Non-Compliant",
            "violations": violations if violations else "No violations detected."
        }
        return json.dumps(report, indent=2)

class AuditAllSystemsForComplianceTool(BaseTool):
    """Tool to audit all registered AI systems against all active policies."""
    def __init__(self, tool_name="audit_all_systems_for_compliance"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Audits all registered AI systems against all active governance policies and provides a summary report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        audit_results = []
        for system_id, system_desc in governance_state.systems.items():
            system_report = {"system_id": system_id, "compliance_checks": []}
            for policy_id, policy in governance_state.policies.items():
                if not policy.get("active", True):
                    continue
                
                operation_lower = system_desc.lower()
                violations = []
                for rule in policy["rules"]:
                    if any(keyword in operation_lower for keyword in rule["keywords"]):
                        violations.append(rule["rule_id"])
                
                system_report["compliance_checks"].append({
                    "policy_id": policy_id,
                    "status": "Non-Compliant" if violations else "Compliant",
                    "violated_rules": violations
                })
            audit_results.append(system_report)
            
        return json.dumps({"audit_summary": audit_results}, indent=2)