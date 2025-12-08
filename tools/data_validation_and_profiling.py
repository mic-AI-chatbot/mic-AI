import logging
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataValidationAndProfilingTool(BaseTool):
    """
    A tool for defining data validation rules, validating data against them,
    and profiling data to understand its characteristics.
    """

    def __init__(self, tool_name: str = "data_validation_and_profiling"):
        super().__init__(tool_name)
        self.rules_file = "validation_rules.json"
        self.rules: Dict[str, Dict[str, Any]] = self._load_rules()

    @property
    def description(self) -> str:
        return "Defines data validation rules, validates data against them, and profiles data to understand its characteristics."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data validation/profiling operation to perform.",
                    "enum": ["define_validation_rule", "validate_data", "profile_data", "list_validation_rules", "get_rule_details"]
                },
                "rule_id": {"type": "string"},
                "rule_name": {"type": "string"},
                "definition": {"type": "object"},
                "description": {"type": "string"},
                "data": {"type": "array", "items": {"type": "object"}},
                "columns": {"type": "array", "items": {"type": "string"}}
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

    def _define_validation_rule(self, rule_id: str, rule_name: str, definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
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
        
        validation_status = "pass"
        violations = []
        
        for i, record in enumerate(data):
            record_id = record.get("id", f"record_{i}")
            value = record.get(column)

            if check == "not_null":
                if value is None or (isinstance(value, str) and not value.strip()):
                    violations.append({"record_id": record_id, "column": column, "issue": "Value is null or empty."})
                    validation_status = "fail"
            elif check == "unique": pass # Handled separately
            elif check == "regex":
                pattern = rule["definition"].get("pattern")
                if not pattern: raise ValueError("Regex check requires a 'pattern'.")
                if value is not None and not re.fullmatch(pattern, str(value)):
                    violations.append({"record_id": record_id, "column": column, "issue": f"Value '{value}' does not match regex pattern '{pattern}'."})
                    validation_status = "fail"
            elif check == "min_value":
                min_val = rule["definition"].get("value")
                if value is not None and isinstance(value, (int, float)) and value < min_val:
                    violations.append({"record_id": record_id, "column": column, "issue": f"Value '{value}' is less than minimum '{min_val}'."})
                    validation_status = "fail"
            elif check == "max_value":
                max_val = rule["definition"].get("value")
                if value is not None and isinstance(value, (int, float)) and value > max_val:
                    violations.append({"record_id": record_id, "column": column, "issue": f"Value '{value}' is greater than maximum '{max_val}'."})
                    validation_status = "fail"
            elif check == "allowed_values":
                allowed_values = rule["definition"].get("values")
                if value is not None and value not in allowed_values:
                    violations.append({"record_id": record_id, "column": column, "issue": f"Value '{value}' is not in allowed values {allowed_values}."})
                    validation_status = "fail"
            else:
                logger.warning(f"Unsupported validation check '{check}' for rule '{rule_id}'. Skipping.")

        if check == "unique":
            column_values = [record.get(column) for record in data if column in record and record.get(column) is not None]
            if len(column_values) != len(set(column_values)):
                violations.append({"record_id": "N/A", "column": column, "issue": "Duplicate values found in column."})
                validation_status = "fail"

        validation_report = {
            "rule_id": rule_id, "rule_name": rule["rule_name"], "timestamp": datetime.now().isoformat(),
            "overall_status": validation_status, "total_records_checked": len(data),
            "violations_count": len(violations), "violations": violations
        }
        return validation_report

    def _profile_data(self, data: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> Dict[str, Any]:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")
        if not data: return {"message": "No data to profile."}

        profile_report: Dict[str, Any] = {
            "total_records": len(data), "profiled_at": datetime.now().isoformat(), "column_profiles": {}
        }

        all_columns = set()
        for record in data: all_columns.update(record.keys())
        columns_to_profile = columns if columns is not None else list(all_columns)

        for col in columns_to_profile:
            values = [record.get(col) for record in data]
            non_null_values = [v for v in values if v is not None and (isinstance(v, str) and v.strip() != '')]
            
            col_profile: Dict[str, Any] = {
                "column_name": col, "data_type_inferred": str(type(non_null_values[0])) if non_null_values else "unknown",
                "total_values": len(values), "non_null_count": len(non_null_values),
                "null_count": len(values) - len(non_null_values),
                "completeness_percent": round((len(non_null_values) / len(values)) * 100, 2) if values else 0,
                "uniqueness_percent": round((len(set(non_null_values)) / len(non_null_values)) * 100, 2) if non_null_values else 0,
            }
            col_profile["unique_count"] = len(set(non_null_values))

            numerical_values = [v for v in non_null_values if isinstance(v, (int, float))]
            if numerical_values:
                col_profile["min"] = min(numerical_values)
                col_profile["max"] = max(numerical_values)
                col_profile["avg"] = sum(numerical_values) / len(numerical_values)
            
            profile_report["column_profiles"][col] = col_profile
        return profile_report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_validation_rule":
            return self._define_validation_rule(kwargs.get("rule_id"), kwargs.get("rule_name"), kwargs.get("definition"), kwargs.get("description"))
        elif operation == "validate_data":
            return self._validate_data(kwargs.get("data"), kwargs.get("rule_id"))
        elif operation == "profile_data":
            return self._profile_data(kwargs.get("data"), kwargs.get("columns"))
        elif operation == "list_validation_rules":
            return list(self.rules.values())
        elif operation == "get_rule_details":
            return self.rules.get(kwargs.get("rule_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataValidationAndProfilingTool functionality...")
    tool = DataValidationAndProfilingTool()
    
    sample_data = [
        {"id": "u1", "user_id": "user_A", "name": "Alice", "email": "alice@example.com", "age": 25},
        {"id": "u2", "user_id": "user_B", "name": "Bob", "email": "bob@example.com", "age": 17},
    ]

    try:
        print("\n--- Defining Validation Rule ---")
        tool.execute(operation="define_validation_rule", rule_id="age_min", rule_name="Minimum Age", definition={"column": "age", "check": "min_value", "value": 18})
        
        print("\n--- Validating Data ---")
        validation_result = tool.execute(operation="validate_data", data=sample_data, rule_id="age_min")
        print(json.dumps(validation_result, indent=2))

        print("\n--- Profiling Data ---")
        profile_report = tool.execute(operation="profile_data", data=sample_data, columns=["age", "email"])
        print(json.dumps(profile_report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.rules_file): os.remove(tool.rules_file)
        print("\nCleanup complete.")