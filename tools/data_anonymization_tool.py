import logging
import json
import hashlib
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataAnonymizationTool(BaseTool):
    """
    A tool for anonymizing sensitive data within a list of dictionaries (records).
    """

    def __init__(self, tool_name: str = "data_anonymization_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Anonymizes sensitive data in a list of records using techniques like pseudonymization, suppression, and masking."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "A list of dictionaries representing the data records."
                },
                "anonymization_strategies": {
                    "type": "object",
                    "description": "A dictionary where keys are column names and values specify the anonymization technique and its parameters."
                }
            },
            "required": ["data", "anonymization_strategies"]
        }

    def _ensure_data_is_list_of_dicts(self, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

    def _pseudonymize_column(self, data: List[Dict[str, Any]], column: str, hash_algorithm: str = 'sha256') -> List[Dict[str, Any]]:
        if hash_algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported hash algorithm: '{hash_algorithm}'.")
        
        for record in data:
            if column in record and record[column] is not None:
                original_value = str(record[column]).encode('utf-8')
                record[column] = hashlib.new(hash_algorithm, original_value).hexdigest()
        return data

    def _suppress_column(self, data: List[Dict[str, Any]], column: str, replacement_value: Any = '[REDACTED]') -> List[Dict[str, Any]]:
        for record in data:
            if column in record:
                record[column] = replacement_value
        return data

    def _mask_column(self, data: List[Dict[str, Any]], column: str, char: str = '*', reveal_last_n: int = 4) -> List[Dict[str, Any]]:
        for record in data:
            if column in record and isinstance(record[column], str):
                original_value = record[column]
                if len(original_value) > reveal_last_n:
                    masked_part = char * (len(original_value) - reveal_last_n)
                    revealed_part = original_value[-reveal_last_n:]
                    record[column] = masked_part + revealed_part
                else:
                    record[column] = char * len(original_value)
        return data

    def execute(self, data: List[Dict[str, Any]], anonymization_strategies: Dict[str, Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        processed_data = [rec.copy() for rec in data] # Work on a copy

        for column, strategy in anonymization_strategies.items():
            technique = strategy.get("technique")
            params = {k: v for k, v in strategy.items() if k != "technique"}

            if technique == "pseudonymize":
                self._pseudonymize_column(processed_data, column, **params)
            elif technique == "suppress":
                self._suppress_column(processed_data, column, **params)
            elif technique == "mask":
                self._mask_column(processed_data, column, **params)
            else:
                logger.warning(f"Unknown anonymization technique '{technique}' for column '{column}'. Skipping.")
        
        return processed_data

if __name__ == '__main__':
    print("Demonstrating DataAnonymizationTool functionality...")
    tool = DataAnonymizationTool()
    sample_data = [
        {"id": 1, "name": "Alice Smith", "email": "alice.smith@example.com", "credit_card": "1234-5678-9012-3456"},
        {"id": 2, "name": "Bob Johnson", "email": "bob.j@example.com", "credit_card": "9876-5432-1098-7654"}
    ]
    strategies = {
        "email": {"technique": "pseudonymize"},
        "credit_card": {"technique": "mask", "reveal_last_n": 4}
    }
    anonymized_data = tool.execute(data=sample_data, anonymization_strategies=strategies)
    print(json.dumps(anonymized_data, indent=2))
