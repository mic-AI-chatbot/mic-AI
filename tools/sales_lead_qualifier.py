import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SalesLeadQualifierSimulatorTool(BaseTool):
    """
    A tool that simulates sales lead qualification, allowing for defining
    qualification rules, qualifying leads, and generating reports.
    """

    def __init__(self, tool_name: str = "SalesLeadQualifierSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.rules_file = os.path.join(self.data_dir, "qualification_rules.json")
        self.leads_file = os.path.join(self.data_dir, "lead_records.json")
        self.reports_file = os.path.join(self.data_dir, "qualification_reports.json")
        
        # Qualification rules: {rule_set_id: {name: ..., rules: []}}
        self.qualification_rules: Dict[str, Dict[str, Any]] = self._load_data(self.rules_file, default={})
        # Lead records: {lead_id: {data: ..., score: ..., status: ...}}
        self.lead_records: Dict[str, Dict[str, Any]] = self._load_data(self.leads_file, default={})
        # Qualification reports: {report_id: {lead_id: ..., score: ..., status: ...}}
        self.qualification_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sales lead qualification: define rules, qualify leads, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_qualification_rules", "qualify_lead", "get_qualification_report"]},
                "rule_set_id": {"type": "string"},
                "name": {"type": "string"},
                "rules": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"attribute": {"type": "string"}, "operator": {"type": "string"}, "value": {"type": "string"}, "score_impact": {"type": "integer"}}},
                    "description": "e.g., [{'attribute': 'company_size', 'operator': '>=', 'value': 'medium', 'score_impact': 20}]"
                },
                "lead_id": {"type": "string"},
                "lead_data": {"type": "object", "description": "Data related to the sales lead (e.g., {'company_size': 'medium', 'industry': 'tech'})."},
                "report_id": {"type": "string", "description": "ID of the qualification report to retrieve."}
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

    def _save_rules(self):
        with open(self.rules_file, 'w') as f: json.dump(self.qualification_rules, f, indent=2)

    def _save_leads(self):
        with open(self.leads_file, 'w') as f: json.dump(self.lead_records, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.qualification_reports, f, indent=2)

    def define_qualification_rules(self, rule_set_id: str, name: str, rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Defines a new set of lead qualification rules."""
        if rule_set_id in self.qualification_rules: raise ValueError(f"Rule set '{rule_set_id}' already exists.")
        
        new_rule_set = {
            "id": rule_set_id, "name": name, "rules": rules,
            "defined_at": datetime.now().isoformat()
        }
        self.qualification_rules[rule_set_id] = new_rule_set
        self._save_rules()
        return new_rule_set

    def _evaluate_condition(self, attribute: str, operator: str, value: Any, lead_data: Dict[str, Any]) -> bool:
        """Evaluates a single condition against lead data."""
        lead_value = lead_data.get(attribute)
        if lead_value is None: return False
        
        # Try to convert value to appropriate type
        try:
            if isinstance(lead_value, (int, float)):
                value = float(value)
            elif isinstance(lead_value, str):
                value = str(value)
        except (ValueError, TypeError):
            return False # Cannot compare
        
        if operator == "==": return lead_value == value
        if operator == "!=": return lead_value != value
        if operator == ">": return lead_value > value
        if operator == "<": return lead_value < value
        if operator == ">=": return lead_value >= value
        if operator == "<=": return lead_value <= value
        
        return False

    def qualify_lead(self, lead_id: str, lead_data: Dict[str, Any], rule_set_id: str) -> Dict[str, Any]:
        """Qualifies a sales lead based on defined rules."""
        rule_set = self.qualification_rules.get(rule_set_id)
        if not rule_set: raise ValueError(f"Rule set '{rule_set_id}' not found. Define it first.")
        
        lead_score = 0
        triggered_rules = []
        
        for rule in rule_set["rules"]:
            if self._evaluate_condition(rule["attribute"], rule["operator"], rule["value"], lead_data):
                lead_score += rule.get("score_impact", 0)
                triggered_rules.append(rule["name"] if "name" in rule else f"Rule on {rule['attribute']}")
        
        qualification_status = "unqualified"
        if lead_score >= 50: qualification_status = "qualified"
        elif lead_score >= 20: qualification_status = "warm"
        
        new_lead_record = {
            "id": lead_id, "data": lead_data, "score": lead_score, "status": qualification_status,
            "qualified_at": datetime.now().isoformat()
        }
        self.lead_records[lead_id] = new_lead_record
        self._save_leads()

        report_id = f"qual_report_{lead_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "lead_id": lead_id, "lead_score": lead_score, "qualification_status": qualification_status,
            "triggered_rules": triggered_rules, "lead_data": lead_data,
            "generated_at": datetime.now().isoformat()
        }
        self.qualification_reports[report_id] = report
        self._save_reports()
        return report

    def get_qualification_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated qualification report."""
        report = self.qualification_reports.get(report_id)
        if not report: raise ValueError(f"Qualification report '{report_id}' not found.")
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_qualification_rules":
            rule_set_id = kwargs.get('rule_set_id')
            name = kwargs.get('name')
            rules = kwargs.get('rules')
            if not all([rule_set_id, name, rules]):
                raise ValueError("Missing 'rule_set_id', 'name', or 'rules' for 'define_qualification_rules' operation.")
            return self.define_qualification_rules(rule_set_id, name, rules)
        elif operation == "qualify_lead":
            lead_id = kwargs.get('lead_id')
            lead_data = kwargs.get('lead_data')
            rule_set_id = kwargs.get('rule_set_id')
            if not all([lead_id, lead_data, rule_set_id]):
                raise ValueError("Missing 'lead_id', 'lead_data', or 'rule_set_id' for 'qualify_lead' operation.")
            return self.qualify_lead(lead_id, lead_data, rule_set_id)
        elif operation == "get_qualification_report":
            report_id = kwargs.get('report_id')
            if not report_id:
                raise ValueError("Missing 'report_id' for 'get_qualification_report' operation.")
            return self.get_qualification_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SalesLeadQualifierSimulatorTool functionality...")
    temp_dir = "temp_lead_qualifier_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    qualifier_tool = SalesLeadQualifierSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define qualification rules
        print("\n--- Defining qualification rules 'b2b_rules' ---")
        rules = [
            {"attribute": "company_size", "operator": ">=", "value": 50, "score_impact": 30, "name": "Large Company"},
            {"attribute": "industry", "operator": "==", "value": "tech", "score_impact": 25, "name": "Tech Industry"},
            {"attribute": "budget", "operator": ">", "value": 10000, "score_impact": 40, "name": "High Budget"}
        ]
        qualifier_tool.execute(operation="define_qualification_rules", rule_set_id="b2b_rules", name="B2B Qualification Rules", rules=rules)
        print("Qualification rules defined.")

        # 2. Qualify a lead (qualified)
        print("\n--- Qualifying lead 'lead_001' (qualified) ---")
        lead_data1 = {"company_size": 120, "industry": "tech", "budget": 15000}
        qualification_report1 = qualifier_tool.execute(operation="qualify_lead", lead_id="lead_001", lead_data=lead_data1, rule_set_id="b2b_rules")
        print(json.dumps(qualification_report1, indent=2))

        # 3. Qualify another lead (warm)
        print("\n--- Qualifying lead 'lead_002' (warm) ---")
        lead_data2 = {"company_size": 30, "industry": "retail", "budget": 5000}
        qualification_report2 = qualifier_tool.execute(operation="qualify_lead", lead_id="lead_002", lead_data=lead_data2, rule_set_id="b2b_rules")
        print(json.dumps(qualification_report2, indent=2))

        # 4. Get qualification report
        print(f"\n--- Getting qualification report for '{qualification_report1['id']}' ---")
        report_details = qualifier_tool.execute(operation="get_qualification_report", report_id=qualification_report1["id"])
        print(json.dumps(report_details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")