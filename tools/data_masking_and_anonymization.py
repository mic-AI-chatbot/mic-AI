import logging
import random
import hashlib
from typing import List, Dict, Any, Union, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataMaskingAndAnonymizationTool(BaseTool):
    """
    A tool for applying various data masking and anonymization techniques
    to structured data (lists of dictionaries).
    """

    def __init__(self, tool_name: str = "data_masking_and_anonymization"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Applies data masking and anonymization techniques like masking, shuffling, tokenization, and redaction to structured data."

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
                "strategies": {
                    "type": "object",
                    "description": "A dictionary where keys are field names and values are dictionaries specifying the technique and its parameters."
                }
            },
            "required": ["data", "strategies"]
        }

    def _ensure_data_is_list_of_dicts(self, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

    def _ensure_field_exists(self, data: List[Dict[str, Any]], field: str) -> None:
        if not any(field in record for record in data):
            raise KeyError(f"Field '{field}' not found in any record of the provided data.")

    def _mask_field(self, data: List[Dict[str, Any]], field: str, mask_char: str = '*', reveal_last_n: int = 0) -> List[Dict[str, Any]]:
        self._ensure_field_exists(data, field)
        for record in data:
            if field in record and isinstance(record[field], str) and record[field] is not None:
                original_value = record[field]
                if len(original_value) > reveal_last_n:
                    masked_part = mask_char * (len(original_value) - reveal_last_n)
                    revealed_part = original_value[-reveal_last_n:]
                    record[field] = masked_part + revealed_part
                else:
                    record[field] = mask_char * len(original_value)
        return data

    def _shuffle_field(self, data: List[Dict[str, Any]], field: str) -> List[Dict[str, Any]]:
        self._ensure_field_exists(data, field)
        field_values = [record.get(field) for record in data]
        random.shuffle(field_values)
        for i, record in enumerate(data):
            if field in record:
                record[field] = field_values[i]
        return data

    def _tokenize_field(self, data: List[Dict[str, Any]], field: str, hash_algorithm: str = 'sha256') -> List[Dict[str, Any]]:
        self._ensure_field_exists(data, field)
        if hash_algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported hash algorithm: '{hash_algorithm}'.")
        for record in data:
            if field in record and record[field] is not None:
                original_value = str(record[field]).encode('utf-8')
                record[field] = hashlib.new(hash_algorithm, original_value).hexdigest()
        return data

    def _redact_field(self, data: List[Dict[str, Any]], field: str, replacement_value: Any = '[REDACTED]') -> List[Dict[str, Any]]:
        self._ensure_field_exists(data, field)
        for record in data:
            if field in record:
                record[field] = replacement_value
        return data

    def execute(self, data: List[Dict[str, Any]], strategies: Dict[str, Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        processed_data = [rec.copy() for rec in data] # Work on a copy

        for field, strategy in strategies.items():
            technique = strategy.get("technique")
            params = {k: v for k, v in strategy.items() if k != "technique"}

            if technique == "mask":
                self._mask_field(processed_data, field, **params)
            elif technique == "shuffle":
                self._shuffle_field(processed_data, field)
            elif technique == "tokenize":
                self._tokenize_field(processed_data, field, **params)
            elif technique == "redact":
                self._redact_field(processed_data, field, **params)
            else:
                logger.warning(f"Unknown masking/anonymization technique '{technique}' for field '{field}'. Skipping.")
        
        return processed_data

if __name__ == '__main__':
    print("Demonstrating DataMaskingAndAnonymizationTool functionality...")
    tool = DataMaskingAndAnonymizationTool()
    
    sample_data = [
        {"id": 1, "name": "Alice Smith", "email": "alice.smith@example.com", "credit_card": "1234-5678-9012-3456", "user_id": "user_A"},
        {"id": 2, "name": "Bob Johnson", "email": "bob.j@example.com", "credit_card": "9876-5432-1098-7654", "user_id": "user_B"},
    ]

    masking_strategies = {
        "email": {"technique": "tokenize", "hash_algorithm": "md5"},
        "credit_card": {"technique": "mask", "reveal_last_n": 4},
        "name": {"technique": "redact", "replacement_value": "[REDACTED_NAME]"},
        "user_id": {"technique": "shuffle"}
    }

    try:
        processed_data = tool.execute(data=sample_data, strategies=masking_strategies)
        print("\nProcessed Data:")
        print(json.dumps(processed_data, indent=2))
    except Exception as e:
        print(f"An error occurred: {e}")
