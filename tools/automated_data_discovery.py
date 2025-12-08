import logging
import json
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ScanDataSourceTool(BaseTool):
    """Scans a mock data source to discover tables and columns."""
    def __init__(self, tool_name="scan_data_source"):
        super().__init__(tool_name=tool_name)
        # Define a static mock schema for demonstration purposes
        self.mock_schema = {
            "users": ["id", "name", "email", "phone_number", "address", "ssn"],
            "products": ["product_id", "product_name", "price", "description"],
            "orders": ["order_id", "user_id", "product_id", "order_date", "credit_card_last_four"]
        }

    @property
    def description(self) -> str:
        return "Scans a mock data source to discover its tables and columns, simulating data asset discovery without actual database interaction."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"data_source_name": {"type": "string", "description": "The name of the data source (e.g., 'mock_database')."}},
            "required": ["data_source_name"]
        }

    def execute(self, data_source_name: str, **kwargs: Any) -> str:
        # Simulate discovery by returning the predefined mock schema
        tables = list(self.mock_schema.keys())
        columns = self.mock_schema
        
        report = {
            "data_source_name": data_source_name,
            "discovered_tables": tables,
            "discovered_columns": columns
        }
        return json.dumps(report, indent=2)

class IdentifySensitiveDataTool(BaseTool):
    """Identifies sensitive data within discovered data assets using regex patterns and keywords."""
    def __init__(self, tool_name="identify_sensitive_data"):
        super().__init__(tool_name=tool_name)
        self.sensitive_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone_number": r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
            "address": r"\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|lane|ln|blvd|boulevard|drive|dr|court|ct|place|pl|square|sq)\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card_last_four": r"\b\d{4}\b" # Simplified for last four digits
        }
        self.sensitive_keywords = ["ssn", "credit_card", "email", "phone", "address", "pii", "personal_id"]

    @property
    def description(self) -> str:
        return "Identifies sensitive data (e.g., PII, financial data) within discovered tables and columns using keyword and regex pattern matching."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_source_name": {"type": "string", "description": "The name of the data source being analyzed."},
                "tables_and_columns_json": {
                    "type": "string",
                    "description": "JSON string of discovered tables and their columns (e.g., from ScanDataSourceTool)."
                }
            },
            "required": ["data_source_name", "tables_and_columns_json"]
        }

    def execute(self, data_source_name: str, tables_and_columns_json: str, **kwargs: Any) -> str:
        try:
            tables_and_columns = json.loads(tables_and_columns_json)
            if not isinstance(tables_and_columns, dict):
                raise ValueError("Expected a dictionary for tables_and_columns.")
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for tables_and_columns."})
        except ValueError as e:
            return json.dumps({"error": str(e)})

        sensitive_data_found = {}
        
        for table, columns in tables_and_columns.items():
            if not isinstance(columns, list):
                logger.warning(f"Skipping table '{table}' due to invalid columns format.")
                continue

            for column in columns:
                column_lower = column.lower()
                reasons = []

                # Check column name for sensitive keywords
                if any(keyword in column_lower for keyword in self.sensitive_keywords):
                    reasons.append("Keyword in column name.")
                
                # Check column name against sensitive patterns (simplified for this simulation)
                # In a real scenario, this would involve sampling data from the column.
                for pattern_name, pattern_regex in self.sensitive_patterns.items():
                    if re.search(pattern_regex, column_lower):
                        reasons.append(f"Pattern '{pattern_name}' detected in column name.")
                
                if reasons:
                    if table not in sensitive_data_found:
                        sensitive_data_found[table] = []
                    sensitive_data_found[table].append({"column": column, "reasons": list(set(reasons))})
        
        if not sensitive_data_found:
            return json.dumps({
                "data_source_name": data_source_name,
                "sensitive_data_identified": False,
                "details": "No sensitive data identified based on keywords or patterns in column names."
            }, indent=2)
        else:
            return json.dumps({
                "data_source_name": data_source_name,
                "sensitive_data_identified": True,
                "details": sensitive_data_found
            }, indent=2)
