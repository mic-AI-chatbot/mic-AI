import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DatabaseAuditingTool(BaseTool):
    """
    A tool for defining database audit rules and simulating audits against
    database configurations.
    """

    def __init__(self, tool_name: str = "database_auditing_tool"):
        super().__init__(tool_name)
        self.rules_file = "db_audit_rules.json"
        self.findings_file = "db_audit_findings.json"
        self.rules: Dict[str, Dict[str, Any]] = self._load_state(self.rules_file)
        self.findings: Dict[str, Dict[str, Any]] = self._load_state(self.findings_file)

    @property
    def description(self) -> str:
        return "Defines database audit rules and simulates audits against database configurations, generating findings and reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The database auditing operation to perform.",
                    "enum": ["define_audit_rules", "perform_audit", "generate_audit_report", "list_audits", "list_audit_rules"]
                },
                "rule_id": {"type": "string"},
                "rule_name": {"type": "string"},
                "definition": {"type": "object"},
                "description": {"type": "string"},
                "audit_id": {"type": "string"},
                "database_name": {"type": "string"},
                "db_config": {"type": "object"},
                "rules_to_apply": {"type": "array", "items": {"type": "string"}}
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

    def _define_audit_rules(self, rule_id: str, rule_name: str, definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([rule_id, rule_name, definition]):
            raise ValueError("Rule ID, name, and definition cannot be empty.")
        if rule_id in self.rules:
            raise ValueError(f"Audit rule '{rule_id}' already exists.")
        if "check_type" not in definition:
            raise ValueError("Rule definition must contain 'check_type'.")

        new_rule = {
            "rule_id": rule_id, "rule_name": rule_name, "definition": definition,
            "description": description, "defined_at": datetime.now().isoformat()
        }
        self.rules[rule_id] = new_rule
        self._save_state(self.rules, self.rules_file)
        return new_rule

    def _perform_audit(self, audit_id: str, database_name: str, db_config: Dict[str, Any], rules_to_apply: List[str]) -> Dict[str, Any]:
        if audit_id in self.findings: raise ValueError(f"Audit '{audit_id}' already exists.")
        if not rules_to_apply: raise ValueError("At least one rule must be specified to apply for the audit.")

        overall_status = "compliant"
        findings_list = []

        for rule_id in rules_to_apply:
            rule = self.rules.get(rule_id)
            if not rule:
                findings_list.append({"rule_id": rule_id, "status": "skipped", "issue": f"Rule '{rule_id}' not found."})
                continue
            
            check_type = rule["definition"]["check_type"]
            
            if check_type == "permission":
                user = rule["definition"].get("user")
                privilege = rule["definition"].get("privilege")
                if user and privilege:
                    user_found = False
                    for db_user in db_config.get("users", []):
                        if db_user["name"] == user:
                            user_found = True
                            if privilege in db_user.get("privileges", []):
                                findings_list.append({"rule_id": rule_id, "status": "fail", "issue": f"User '{user}' has '{privilege}' privilege."})
                                overall_status = "non-compliant"
                            else:
                                findings_list.append({"rule_id": rule_id, "status": "pass", "issue": f"User '{user}' does not have '{privilege}' privilege."})
                            break
                    if not user_found: findings_list.append({"rule_id": rule_id, "status": "pass", "issue": f"User '{user}' not found in DB config."})

            elif check_type == "vulnerability":
                vulnerability_name = rule["definition"].get("name")
                if vulnerability_name and vulnerability_name in db_config.get("vulnerabilities", []):
                    findings_list.append({"rule_id": rule_id, "status": "fail", "issue": f"Vulnerability '{vulnerability_name}' detected."})
                    overall_status = "non-compliant"
                else: findings_list.append({"rule_id": rule_id, "status": "pass", "issue": f"Vulnerability '{vulnerability_name}' not detected."})

            elif check_type == "log_pattern":
                pattern = rule["definition"].get("pattern")
                if pattern and any(re.search(pattern, log_entry) for log_entry in db_config.get("audit_logs", [])):
                    findings_list.append({"rule_id": rule_id, "status": "fail", "issue": f"Log pattern '{pattern}' detected in audit logs."})
                    overall_status = "non-compliant"
                else: findings_list.append({"rule_id": rule_id, "status": "pass", "issue": f"Log pattern '{pattern}' not detected."})
            
            else: findings_list.append({"rule_id": rule_id, "status": "skipped", "issue": f"Unsupported check type '{check_type}'."})

        audit_record = {
            "audit_id": audit_id, "database_name": database_name, "standard_id": "N/A",
            "overall_status": overall_status, "findings": findings_list, "audited_at": datetime.now().isoformat()
        }
        self.findings[audit_id] = audit_record
        self._save_state(self.findings, self.findings_file)
        return audit_record

    def _generate_audit_report(self, audit_id: str) -> Dict[str, Any]:
        audit = self.findings.get(audit_id)
        if not audit: raise ValueError(f"Audit '{audit_id}' not found.")
        
        standard = self.standards.get(audit["standard_id"])
        standard_name = standard["standard_name"] if standard else "Unknown Standard"

        report = {
            "report_id": f"REPORT-{audit_id}", "audit_id": audit_id, "database_name": audit["database_name"],
            "overall_status": audit["overall_status"],
            "findings_summary": f"Found {len([f for f in audit['findings'] if f['status'] == 'fail'])} non-compliant items.",
            "detailed_findings": audit["findings"], "generated_at": datetime.now().isoformat()
        }
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_audit_rules":
            return self._define_audit_rules(kwargs.get("rule_id"), kwargs.get("rule_name"), kwargs.get("definition"), kwargs.get("description"))
        elif operation == "perform_audit":
            return self._perform_audit(kwargs.get("audit_id"), kwargs.get("database_name"), kwargs.get("db_config"), kwargs.get("rules_to_apply"))
        elif operation == "generate_audit_report":
            return self._generate_audit_report(kwargs.get("audit_id"))
        elif operation == "list_audits":
            return list(self.findings.values())
        elif operation == "list_audit_rules":
            return list(self.rules.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DatabaseAuditingTool functionality...")
    tool = DatabaseAuditingTool()
    
    try:
        print("\n--- Defining Audit Rule ---")
        tool.execute(operation="define_audit_rules", rule_id="no_guest_admin", rule_name="No Guest Admin Access", definition={"check_type": "permission", "user": "guest", "privilege": "admin_access"}, description="Ensures 'guest' user does not have admin privileges.")
        
        print("\n--- Performing Audit ---")
        db_config = {"users": [{"name": "guest", "privileges": ["read"]}]}
        audit_result = tool.execute(operation="perform_audit", audit_id="audit_001", database_name="prod_db", db_config=db_config, rules_to_apply=["no_guest_admin"])
        print(json.dumps(audit_result, indent=2))

        print("\n--- Generating Audit Report ---")
        report = tool.execute(operation="generate_audit_report", audit_id="audit_001")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.rules_file): os.remove(tool.rules_file)
        if os.path.exists(tool.findings_file): os.remove(tool.findings_file)
        print("\nCleanup complete.")
