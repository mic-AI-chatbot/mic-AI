import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

logger = logging.getLogger(__name__)

class AdvancedDataAnonymizerTool(BaseTool):
    """
    A tool for applying advanced data anonymization techniques like k-anonymity and
    basic differential privacy to a list of dictionaries (records).
    """

    def __init__(self, tool_name: str = "advanced_data_anonymizer"):
        super().__init__(tool_name)
        if not PANDAS_AVAILABLE:
            logger.warning("The 'pandas' library is not installed. K-anonymity will not be available.")
        if not NUMPY_AVAILABLE:
            logger.warning("The 'numpy' library is not installed. Differential privacy will not be available.")

    @property
    def description(self) -> str:
        return "Applies advanced anonymization like k-anonymity or differential privacy to datasets."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The anonymization technique to apply.",
                    "enum": ["k_anonymize", "add_differential_privacy_noise"]
                },
                "data": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "A list of dictionaries representing the data records."
                },
                "quasi_identifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names that are quasi-identifiers for k-anonymity."
                },
                "k": {
                    "type": "integer",
                    "description": "The k-anonymity parameter.",
                    "minimum": 2
                },
                "column": {
                    "type": "string",
                    "description": "The numerical column to add noise to for differential privacy."
                },
                "epsilon": {
                    "type": "number",
                    "description": "The privacy budget for differential privacy (smaller is more private)."
                },
                "sensitivity": {
                    "type": "number",
                    "description": "The sensitivity of the query for differential privacy."
                }
            },
            "required": ["operation", "data"]
        }

    def _ensure_data_is_list_of_dicts(self, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

    def _k_anonymize(self, data: List[Dict[str, Any]], quasi_identifiers: List[str], k: int) -> List[Dict[str, Any]]:
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' library is required for k-anonymity.")
        self._ensure_data_is_list_of_dicts(data)
        if not quasi_identifiers:
            raise ValueError("At least one quasi-identifier must be provided for k-anonymity.")
        if k < 2:
            raise ValueError("k must be an integer greater than or equal to 2.")

        df = pd.DataFrame(data)
        missing_qis = [qi for qi in quasi_identifiers if qi not in df.columns]
        if missing_qis:
            raise KeyError(f"Quasi-identifier(s) not found in data: {', '.join(missing_qis)}")

        grouped = df.groupby(quasi_identifiers)
        small_groups = grouped.filter(lambda x: len(x) < k)

        if small_groups.empty:
            logger.info(f"Data already satisfies {k}-anonymity.")
            return data.copy()

        anonymized_data = df.copy()
        for index, row in small_groups.iterrows():
            for qi in quasi_identifiers:
                anonymized_data.loc[index, qi] = '[GENERALIZED]'
        
        return anonymized_data.to_dict(orient='records')

    def _add_differential_privacy_noise(self, data: List[Dict[str, Any]], column: str, epsilon: float, sensitivity: float) -> List[Dict[str, Any]]:
        if not NUMPY_AVAILABLE:
            raise ImportError("The 'numpy' library is required for differential privacy.")
        self._ensure_data_is_list_of_dicts(data)
        
        if not any(column in record and isinstance(record[column], (int, float)) for record in data):
            raise ValueError(f"Column '{column}' not found or is not numerical.")

        if epsilon <= 0: raise ValueError("Epsilon must be greater than 0.")
        if sensitivity <= 0: raise ValueError("Sensitivity must be greater than 0.")

        scale = sensitivity / epsilon
        anonymized_data = []
        for record in data:
            new_record = record.copy()
            if column in new_record and isinstance(new_record[column], (int, float)):
                noise = np.random.laplace(loc=0, scale=scale)
                new_record[column] += noise
            anonymized_data.append(new_record)
        return anonymized_data

    def execute(self, operation: str, data: List[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
        if operation == "k_anonymize":
            quasi_identifiers = kwargs.get("quasi_identifiers")
            k = kwargs.get("k")
            if not all([quasi_identifiers, k]):
                raise ValueError("Missing 'quasi_identifiers' or 'k' for k-anonymity.")
            return self._k_anonymize(data, quasi_identifiers, k)
        elif operation == "add_differential_privacy_noise":
            column = kwargs.get("column")
            epsilon = kwargs.get("epsilon")
            sensitivity = kwargs.get("sensitivity")
            if not all([column, epsilon, sensitivity]):
                raise ValueError("Missing 'column', 'epsilon', or 'sensitivity' for differential privacy.")
            return self._add_differential_privacy_noise(data, column, epsilon, sensitivity)
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating AdvancedDataAnonymizerTool functionality...")
    tool = AdvancedDataAnonymizerTool()
    sample_data = [
        {"id": 1, "name": "Alice", "age": 25, "zip": "90210"},
        {"id": 2, "name": "Bob", "age": 25, "zip": "90210"},
        {"id": 3, "name": "Charlie", "age": 30, "zip": "10001"},
        {"id": 4, "name": "David", "age": 30, "zip": "10001"},
        {"id": 5, "name": "Eve", "age": 35, "zip": "90210"},
        {"id": 6, "name": "Frank", "age": 35, "zip": "90210"},
        {"id": 7, "name": "Grace", "age": 40, "zip": "10001"}
    ]
    print("\nOriginal Data:")
    print(json.dumps(sample_data, indent=2))

    print("\n--- K-Anonymity (k=3) ---")
    try:
        k_anonymized_data = tool.execute(operation="k_anonymize", data=sample_data, quasi_identifiers=["age", "zip"], k=3)
        print(json.dumps(k_anonymized_data, indent=2))
    except Exception as e:
        print(f"K-anonymity demo failed: {e}")

    print("\n--- Differential Privacy (adding noise to 'age') ---")
    try:
        dp_anonymized_data = tool.execute(operation="add_differential_privacy_noise", data=sample_data, column="age", epsilon=1.0, sensitivity=1.0)
        print(json.dumps(dp_anonymized_data, indent=2))
    except Exception as e:
        print(f"Differential privacy demo failed: {e}")