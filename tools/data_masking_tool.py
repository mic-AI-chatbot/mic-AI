import logging
import random
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataMaskingTool(BaseTool):
    """
    A tool for applying various data masking techniques to in-memory structured data
    (lists of dictionaries).
    """

    def __init__(self, tool_name: str = "data_masking_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Applies data masking techniques like redaction, partial masking, or shuffling to specified fields in structured data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The masking operation to perform.",
                    "enum": ["mask_data", "get_masked_data_sample"]
                },
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "A list of dictionaries representing the data records."
                },
                "fields_to_mask": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of field names to apply masking to."
                },
                "masking_method": {
                    "type": "string",
                    "enum": ["redaction", "partial_masking", "shuffling"],
                    "description": "The masking technique to use."
                },
                "mask_char": {
                    "type": "string",
                    "description": "The character to use for masking (for 'partial_masking').",
                    "default": "*"
                },
                "reveal_last_n": {
                    "type": "integer",
                    "description": "The number of characters to reveal at the end of the string (for 'partial_masking').",
                    "default": 0
                },
                "sample_size": {
                    "type": "integer",
                    "description": "The number of records to include in the sample.",
                    "default": 5
                }
            },
            "required": ["operation", "data"]
        }

    def _ensure_data_is_list_of_dicts(self, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

    def _ensure_field_exists(self, data: List[Dict[str, Any]], field: str) -> None:
        if not any(field in record for record in data):
            raise KeyError(f"Field '{field}' not found in any record of the provided data.")

    def _mask_data(self, data: List[Dict[str, Any]], fields_to_mask: List[str], masking_method: str = 'redaction', mask_char: str = '*', reveal_last_n: int = 0) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        if not fields_to_mask: return data

        processed_data = [record.copy() for record in data]

        for field in fields_to_mask:
            self._ensure_field_exists(data, field)

            if masking_method == 'redaction':
                for record in processed_data:
                    if field in record: record[field] = '[REDACTED]'
            elif masking_method == 'partial_masking':
                for record in processed_data:
                    if field in record and isinstance(record[field], str) and record[field] is not None:
                        original_value = record[field]
                        if len(original_value) > reveal_last_n:
                            masked_part = mask_char * (len(original_value) - reveal_last_n)
                            revealed_part = original_value[-reveal_last_n:]
                            record[field] = masked_part + revealed_part
                        else:
                            record[field] = mask_char * len(original_value)
            elif masking_method == 'shuffling':
                field_values = [record.get(field) for record in processed_data]
                random.shuffle(field_values)
                for i, record in enumerate(processed_data):
                    if field in record: record[field] = field_values[i]
            else:
                logger.warning(f"Unsupported masking method '{masking_method}' for field '{field}'. Skipping.")
        return processed_data

    def _get_masked_data_sample(self, data: List[Dict[str, Any]], sample_size: int = 5) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        if not data: return []
        if sample_size <= 0: raise ValueError("Sample size must be a positive integer.")
        return random.sample(data, min(sample_size, len(data)))  # nosec B311

    def execute(self, operation: str, data: List[Dict[str, Any]], **kwargs: Any) -> Union[List[Dict[str, Any]], List[Dict[str, Any]]]:
        if operation == "mask_data":
            fields_to_mask = kwargs.get("fields_to_mask")
            if not fields_to_mask: raise ValueError("'fields_to_mask' is required for mask_data operation.")
            return self._mask_data(data, fields_to_mask, kwargs.get("masking_method", "redaction"), kwargs.get("mask_char", "*"), kwargs.get("reveal_last_n", 0))
        elif operation == "get_masked_data_sample":
            return self._get_masked_data_sample(data, kwargs.get("sample_size", 5))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataMaskingTool functionality...")
    tool = DataMaskingTool()
    
    sample_data = [
        {"id": 1, "name": "Alice Smith", "email": "alice.smith@example.com", "credit_card": "1234-5678-9012-3456", "user_id": "user_A"},
        {"id": 2, "name": "Bob Johnson", "email": "bob.j@example.com", "credit_card": "9876-5432-1098-7654", "user_id": "user_B"},
    ]

    try:
        print("\n--- Masking 'email' with Redaction ---")
        redacted_data = tool.execute(operation="mask_data", data=sample_data, fields_to_mask=["email"], masking_method="redaction")
        print(json.dumps(redacted_data, indent=2))

        print("\n--- Masking 'credit_card' with Partial Masking ---")
        partially_masked_data = tool.execute(operation="mask_data", data=sample_data, fields_to_mask=["credit_card"], masking_method="partial_masking", reveal_last_n=4)
        print(json.dumps(partially_masked_data, indent=2))

        print("\n--- Getting Masked Data Sample ---")
        sample = tool.execute(operation="get_masked_data_sample", data=partially_masked_data, sample_size=1)
        print(json.dumps(sample, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
