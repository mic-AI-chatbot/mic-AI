import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataValidationTool(BaseTool):
    """
    A simplified tool for defining data validation rules and validating in-memory
    data (lists of dictionaries) against those rules.
    """

    def __init__(self, tool_name: str = "data_validation_tool"):
        super().__init__(tool_name)
        self.rules_file = "simple_validation_rules.json"
        self.reports_file = "simple_validation_reports.json"
        self.rules: Dict[str, Dict[str, Any]] = self._load_rules()
        self.reports: Dict[str, Dict[str, Any]] = self._load_reports()

    @property
    def description(self) -> str:
        return "Defines data validation rules and validates in-memory data against them, generating reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data validation operation to perform.",
                    "enum": ["define_rule", "validate_data", "get_validation_report", "list_rules", "list_reports"]
                },
                "rule_id": {"type": "string"},
                "rule_name": {"type": "string"},
                "definition": {"type": "object"},
                "description": {"type": "string"},
                "data": {"type": "array", "items": {"type": "object"}},
                "report_id": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_rules(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.rules_file):
            with open(self.rules_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted rules file '{self.rules_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_rules(self) -> None:
        with open(self.rules_file, 'w') as f:
            json.dump(self.rules, f, indent=4)

    def _load_reports(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.reports_file):
            with open(self.reports_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted reports file '{self.reports_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_reports(self) -> None:
        with open(self.reports_file, 'w') as f:
            json.dump(self.reports, f, indent=4)

    def _define_rule(self, rule_id: str, rule_name: str, definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([rule_id, rule_name, definition]):
            raise ValueError("Rule ID, name, and definition cannot be empty.")
        if rule_id in self.rules:
            raise ValueError(f"Validation rule '{rule_id}' already exists.")
        if "column" not in definition or "check" not in definition:
            raise ValueError("Rule definition must contain 'column' and 'check'.")

        new_rule = {
            "rule_id": rule_id, "rule_name": rule_name, "definition": definition,
            "description": description, "defined_at": datetime.now().isoformat()
        }
        self.rules[rule_id] = new_rule
        self._save_rules()
        return new_rule

    def _validate_data(self, data: List[Dict[str, Any]], rule_id: str) -> Dict[str, Any]:
        if rule_id not in self.rules: raise ValueError(f"Validation rule '{rule_id}' not found.")
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

        rule = self.rules[rule_id]
        column = rule["definition"]["column"]
        check = rule["definition"]["check"]
        
        report_id = f"REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        overall_status = "pass"
        violations = []
        
        column_values = [record.get(column) for record in data if column in record and record.get(column) is not None]

        for i, record in enumerate(data):
            record_identifier = record.get("id", f"record_{i}")
            value = record.get(column)

            if check == "not_null":
                if value is None or (isinstance(value, str) and not value.strip()):
                    violations.append({"record_identifier": record_identifier, "column": column, "issue": "Value is null or empty."})
                    overall_status = "fail"
            elif check == "regex":
                pattern = rule["definition"].get("pattern")
                if not pattern: raise ValueError("Regex check requires a 'pattern'.")
                if value is not None and not re.fullmatch(pattern, str(value)):
                    violations.append({"record_identifier": record_identifier, "column": column, "issue": f"Value '{value}' does not match regex pattern '{pattern}'."})
                    overall_status = "fail"
            elif check == "min_value":
                min_val = rule["definition"].get("value")
                if value is not None and isinstance(value, (int, float)) and value < min_val:
                    violations.append({"record_identifier": record_identifier, "column": column, "issue": f"Value '{value}' is less than minimum '{min_val}'."})
                    overall_status = "fail"
            elif check == "max_value":
                max_val = rule["definition"].get("value")
                if value is not None and isinstance(value, (int, float)) and value > max_val:
                    violations.append({"record_identifier": record_identifier, "column": column, "issue": f"Value '{value}' is greater than maximum '{max_val}'."})
                    overall_status = "fail"

        if check == "unique":
            if len(column_values) != len(set(column_values)):
                violations.append({"record_identifier": "N/A", "column": column, "issue": "Duplicate values found in column."})
                overall_status = "fail"

        validation_report = {
            "report_id": report_id, "rule_id": rule_id, "rule_name": rule["rule_name"],
            "timestamp": datetime.now().isoformat(), "overall_status": overall_status,
            "total_records_checked": len(data), "violations_count": len(violations), "violations": violations
        }
        self.reports[report_id] = validation_report
        self._save_reports()
        return validation_report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_rule":
            return self._define_rule(kwargs.get("rule_id"), kwargs.get("rule_name"), kwargs.get("definition"), kwargs.get("description"))
        elif operation == "validate_data":
            return self._validate_data(kwargs.get("data"), kwargs.get("rule_id"))
        elif operation == "get_validation_report":
            return self.reports.get(kwargs.get("report_id"))
        elif operation == "list_rules":
            return list(self.rules.values())
        elif operation == "list_reports":
            return list(self.reports.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataValidationTool functionality...")
    tool = DataValidationTool()
    
    sample_data = [
        {"id": "u1", "user_id": "user_A", "name": "Alice", "email": "alice@example.com", "age": 25},
        {"id": "u2", "user_id": "user_B", "name": "Bob", "email": "bob@example.com", "age": 17},
    ]

    try:
        print("\n--- Defining Validation Rule ---")
        tool.execute(operation="define_rule", rule_id="age_min", rule_name="Minimum Age", definition={"column": "age", "check": "min_value", "value": 18})
        
        print("\n--- Validating Data ---")
        validation_result = tool.execute(operation="validate_data", data=sample_data, rule_id="age_min")
        print(json.dumps(validation_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.rules_file): os.remove(tool.rules_file)
        if os.path.exists(tool.reports_file): os.remove(tool.reports_file)
        print("\nCleanup complete.")