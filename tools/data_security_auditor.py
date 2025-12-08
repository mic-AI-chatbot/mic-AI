import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataSecurityAuditorTool(BaseTool):
    """
    A tool for defining security standards and simulating data system audits
    against those standards.
    """

    def __init__(self, tool_name: str = "data_security_auditor"):
        super().__init__(tool_name)
        self.standards_file = "security_standards.json"
        self.audits_file = "security_audits.json"
        self.standards: Dict[str, Dict[str, Any]] = self._load_state(self.standards_file)
        self.audits: Dict[str, Dict[str, Any]] = self._load_state(self.audits_file)

    @property
    def description(self) -> str:
        return "Defines security standards and audits data systems against them, generating audit reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The security audit operation to perform.",
                    "enum": ["define_security_standard", "audit_data_system", "generate_audit_report", "list_audits", "list_standards"]
                },
                "standard_id": {"type": "string"},
                "standard_name": {"type": "string"},
                "controls": {"type": "object"},
                "description": {"type": "string"},
                "audit_id": {"type": "string"},
                "system_id": {"type": "string"},
                "system_config": {"type": "object"}
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

    def _define_security_standard(self, standard_id: str, standard_name: str, controls: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([standard_id, standard_name, controls]):
            raise ValueError("Standard ID, name, and controls cannot be empty.")
        if standard_id in self.standards:
            raise ValueError(f"Security standard '{standard_id}' already exists.")

        new_standard = {
            "standard_id": standard_id, "standard_name": standard_name, "description": description,
            "controls": controls, "defined_at": datetime.now().isoformat()
        }
        self.standards[standard_id] = new_standard
        self._save_state(self.standards, self.standards_file)
        return new_standard

    def _audit_data_system(self, audit_id: str, system_id: str, system_config: Dict[str, Any], standard_id: str) -> Dict[str, Any]:
        if audit_id in self.audits: raise ValueError(f"Audit '{audit_id}' already exists.")
        if standard_id not in self.standards: raise ValueError(f"Security standard '{standard_id}' not found.")

        standard = self.standards[standard_id]
        audit_status = "compliant"
        findings = []

        for control_name, control_rules in standard["controls"].items():
            if control_name == "access_control":
                if control_rules.get("rule") == "MFA_required" and not system_config.get("mfa_enabled", False):
                    findings.append({"control": control_name, "status": "fail", "issue": "MFA is required but not enabled."})
                    audit_status = "non-compliant"
            elif control_name == "encryption":
                if control_rules.get("rule") == "data_at_rest_encrypted" and not system_config.get("encryption_status", False):
                    findings.append({"control": control_name, "status": "fail", "issue": "Data at rest encryption is required but not enabled."})
                    audit_status = "non-compliant"
            elif control_name == "public_access":
                if control_rules.get("rule") == "no_public_access" and system_config.get("public_access", False):
                    findings.append({"control": control_name, "status": "fail", "issue": "Public access is enabled but prohibited by standard."})
                    audit_status = "non-compliant"

        audit_record = {
            "audit_id": audit_id, "system_id": system_id, "standard_id": standard_id,
            "audit_status": audit_status, "findings": findings, "audited_at": datetime.now().isoformat()
        }
        self.audits[audit_id] = audit_record
        self._save_state(self.audits, self.audits_file)
        return audit_record

    def _generate_audit_report(self, audit_id: str) -> Dict[str, Any]:
        audit = self.audits.get(audit_id)
        if not audit: raise ValueError(f"Audit '{audit_id}' not found.")
        
        standard = self.standards.get(audit["standard_id"])
        standard_name = standard["standard_name"] if standard else "Unknown Standard"

        report = {
            "report_id": f"REPORT-{audit_id}", "audit_id": audit_id, "system_id": audit["system_id"],
            "standard_name": standard_name, "overall_status": audit["audit_status"],
            "findings_summary": f"Found {len(audit['findings'])} non-compliant items.",
            "detailed_findings": audit["findings"], "generated_at": datetime.now().isoformat()
        }
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_security_standard":
            return self._define_security_standard(kwargs.get("standard_id"), kwargs.get("standard_name"), kwargs.get("controls"), kwargs.get("description"))
        elif operation == "audit_data_system":
            return self._audit_data_system(kwargs.get("audit_id"), kwargs.get("system_id"), kwargs.get("system_config"), kwargs.get("standard_id"))
        elif operation == "generate_audit_report":
            return self._generate_audit_report(kwargs.get("audit_id"))
        elif operation == "list_audits":
            return list(self.audits.values())
        elif operation == "list_standards":
            return list(self.standards.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataSecurityAuditorTool functionality...")
    tool = DataSecurityAuditorTool()
    
    try:
        print("\n--- Defining Security Standard ---")
        tool.execute(operation="define_security_standard", standard_id="PCI_DSS", standard_name="PCI DSS v4.0", controls={"encryption": {"rule": "data_at_rest_encrypted"}}, description="Payment Card Industry Data Security Standard.")
        
        print("\n--- Auditing Data System ---")
        system_config = {"encryption_status": False}
        audit_result = tool.execute(operation="audit_data_system", audit_id="audit_001", system_id="payment_gateway_db", system_config=system_config, standard_id="PCI_DSS")
        print(json.dumps(audit_result, indent=2))

        print("\n--- Generating Audit Report ---")
        report = tool.execute(operation="generate_audit_report", audit_id="audit_001")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.standards_file): os.remove(tool.standards_file)
        if os.path.exists(tool.audits_file): os.remove(tool.audits_file)
        print("\nCleanup complete.")