import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataQualityManagementTool(BaseTool):
    """
    A tool for managing data quality, allowing for the definition of rules,
    checking data quality against those rules, and simulating data cleaning.
    """

    def __init__(self, tool_name: str = "data_quality_management"):
        super().__init__(tool_name)
        self.rules_file = "dq_rules.json"
        self.reports_file = "dq_reports.json"
        self.rules: Dict[str, Dict[str, Any]] = self._load_state(self.rules_file)
        self.reports: List[Dict[str, Any]] = self._load_state(self.reports_file, is_list=True)

    @property
    def description(self) -> str:
        return "Manages data quality: defines rules, checks data against rules, and simulates data cleaning."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data quality operation to perform.",
                    "enum": ["define_rule", "check_data_quality", "clean_data", "list_rules", "get_rule_details", "list_reports"]
                },
                "rule_id": {"type": "string"},
                "rule_name": {"type": "string"},
                "rule_type": {"type": "string", "enum": ["completeness", "uniqueness", "validity", "consistency"]},
                "definition": {"type": "object"},
                "description": {"type": "string"},
                "data": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["operation"]
        }

    def _load_state(self, file_path: str, is_list: bool = False) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted state file '{file_path}'. Starting fresh.")
                    return [] if is_list else {}
        return [] if is_list else {}

    def _save_state(self, state: Union[Dict[str, Any], List[Dict[str, Any]]], file_path: str) -> None:
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=4)

    def _define_rule(self, rule_id: str, rule_name: str, rule_type: str, definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([rule_id, rule_name, rule_type, definition]):
            raise ValueError("Rule ID, name, type, and definition cannot be empty.")
        if rule_id in self.rules:
            raise ValueError(f"Rule '{rule_id}' already exists.")

        new_rule = {
            "rule_id": rule_id, "rule_name": rule_name, "rule_type": rule_type,
            "definition": definition, "description": description, "defined_at": datetime.now().isoformat()
        }
        self.rules[rule_id] = new_rule
        self._save_state(self.rules, self.rules_file)
        return new_rule

    def _check_data_quality(self, data: List[Dict[str, Any]], rule_id: str) -> Dict[str, Any]:
        if rule_id not in self.rules: raise ValueError(f"Rule '{rule_id}' not found.")
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

        rule = self.rules[rule_id]
        report_id = f"DQ_REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        
        overall_status = "pass"
        findings = []

        if rule["rule_type"] == "completeness":
            column = rule["definition"].get("column")
            if not column: raise ValueError("Completeness rule requires a 'column'.")
            missing_count = sum(1 for record in data if column not in record or record[column] is None or str(record[column]).strip() == '')
            if missing_count > 0: overall_status = "fail"; findings.append(f"{missing_count} records have missing or empty values in column '{column}'.")
        elif rule["rule_type"] == "uniqueness":
            column = rule["definition"].get("column")
            if not column: raise ValueError("Uniqueness rule requires a 'column'.")
            values = [record[column] for record in data if column in record and record[column] is not None]
            if len(values) != len(set(values)): overall_status = "fail"; findings.append(f"Duplicate values found in column '{column}'.")
        elif rule["rule_type"] == "validity":
            column = rule["definition"].get("column")
            pattern = rule["definition"].get("pattern")
            if not column or not pattern: raise ValueError("Validity rule requires 'column' and 'pattern'.")
            invalid_count = sum(1 for record in data if column in record and record[column] is not None and not re.fullmatch(pattern, str(record[column])))
            if invalid_count > 0: overall_status = "fail"; findings.append(f"{invalid_count} records have invalid values in column '{column}' based on pattern '{pattern}'.")
        else:
            findings.append(f"Unsupported rule type '{rule['rule_type']}'. Quality check simulated.")

        dq_report = {
            "report_id": report_id, "rule_id": rule_id, "rule_name": rule["rule_name"],
            "timestamp": datetime.now().isoformat(), "overall_status": overall_status,
            "total_records_checked": len(data), "findings": findings
        }
        self.reports.append(dq_report)
        self._save_state(self.reports, self.reports_file)
        return dq_report

    def _clean_data(self, data: List[Dict[str, Any]], rule_id: str) -> List[Dict[str, Any]]:
        if rule_id not in self.rules: raise ValueError(f"Rule '{rule_id}' not found.")
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

        rule = self.rules[rule_id]
        cleaned_data = [record.copy() for record in data]

        if rule["rule_type"] == "completeness":
            column = rule["definition"].get("column")
            if not column: raise ValueError("Completeness rule requires a 'column'.")
            cleaned_data = [record for record in cleaned_data if column in record and record[column] is not None and str(record[column]).strip() != '']
        elif rule["rule_type"] == "uniqueness":
            column = rule["definition"].get("column")
            if not column: raise ValueError("Uniqueness rule requires a 'column'.")
            seen_values = set()
            unique_records = []
            for record in cleaned_data:
                if column in record and record[column] is not None:
                    if record[column] not in seen_values:
                        unique_records.append(record)
                        seen_values.add(record[column])
                else: unique_records.append(record)
            cleaned_data = unique_records
        elif rule["rule_type"] == "validity":
            column = rule["definition"].get("column")
            pattern = rule["definition"].get("pattern")
            if not column or not pattern: raise ValueError("Validity rule requires 'column' and 'pattern'.")
            cleaned_data = [record for record in cleaned_data if column not in record or record[column] is None or re.fullmatch(pattern, str(record[column]))]
        else:
            logger.warning(f"Unsupported rule type '{rule['rule_type']}' for cleaning. No cleaning performed.")
        
        return cleaned_data

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_rule":
            return self._define_rule(kwargs.get("rule_id"), kwargs.get("rule_name"), kwargs.get("rule_type"), kwargs.get("definition"), kwargs.get("description"))
        elif operation == "check_data_quality":
            return self._check_data_quality(kwargs.get("data"), kwargs.get("rule_id"))
        elif operation == "clean_data":
            return self._clean_data(kwargs.get("data"), kwargs.get("rule_id"))
        elif operation == "list_rules":
            return list(self.rules.values())
        elif operation == "get_rule_details":
            return self.rules.get(kwargs.get("rule_id"))
        elif operation == "list_reports":
            return self.reports
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataQualityManagementTool functionality...")
    tool = DataQualityManagementTool()
    
    sample_data = [
        {"user_id": "u1", "email": "alice@example.com"},
        {"user_id": "u2", "email": None},
        {"user_id": "u3", "email": "charlie@example.com"},
        {"user_id": "u1", "email": "alice@example.com"},
        {"user_id": "u4", "email": "invalid-email"},
    ]

    try:
        print("\n--- Defining Rules ---")
        tool.execute(operation="define_rule", rule_id="email_completeness", rule_name="Email Completeness", rule_type="completeness", definition={"column": "email"})
        tool.execute(operation="define_rule", rule_id="user_id_uniqueness", rule_name="User ID Uniqueness", rule_type="uniqueness", definition={"column": "user_id"})
        tool.execute(operation="define_rule", rule_id="email_format_validity", rule_name="Email Format", rule_type="validity", definition={"column": "email", "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"})

        print("\n--- Checking Data Quality (email_completeness) ---")
        report = tool.execute(operation="check_data_quality", data=sample_data, rule_id="email_completeness")
        print(json.dumps(report, indent=2))

        print("\n--- Cleaning Data (email_completeness) ---")
        cleaned_data = tool.execute(operation="clean_data", data=sample_data, rule_id="email_completeness")
        print(json.dumps(cleaned_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.rules_file): os.remove(tool.rules_file)
        if os.path.exists(tool.reports_file): os.remove(tool.reports_file)
        print("\nCleanup complete.")