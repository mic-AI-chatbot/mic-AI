import logging
from typing import Dict, Any, List
from tools.base_tool import BaseTool
import random
import json

logger = logging.getLogger(__name__)

class DataDenoisingAndCleaningTool(BaseTool):
    """
    A tool for denoising and cleaning data.
    """

    def __init__(self, tool_name: str = "data_denoising_and_cleaning"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates denoising and cleaning of structured data by removing outliers or filling missing values."

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
                "operation": {
                    "type": "string",
                    "enum": ["remove_outliers", "fill_missing_values"],
                    "description": "The cleaning operation to perform."
                },
                "column": {
                    "type": "string",
                    "description": "The column to apply the operation on."
                },
                "threshold": {
                    "type": "number",
                    "description": "Threshold for outlier removal (e.g., Z-score)."
                },
                "fill_method": {
                    "type": "string",
                    "enum": ["mean", "median", "mode", "constant"],
                    "description": "Method to fill missing values."
                },
                "fill_value": {
                    "type": "string",
                    "description": "Constant value to fill missing values with, if 'constant' method is chosen."
                }
            },
            "required": ["data", "operation", "column"]
        }

    def _remove_outliers(self, data: List[Dict[str, Any]], column: str, threshold: float = 3.0) -> List[Dict[str, Any]]:
        """Simulates removing outliers based on a simple threshold."""
        self.logger.warning("Actual outlier detection is not implemented. This is a simulation.")
        cleaned_data = []
        for record in data:
            if column in record and isinstance(record[column], (int, float)):
                # Simulate outlier detection: e.g., remove if value > 100
                if record[column] < 100: # Simple rule for simulation
                    cleaned_data.append(record)
                else:
                    self.logger.info(f"Simulated: Removed outlier in column '{column}' with value {record[column]}.")
            else:
                cleaned_data.append(record)
        return cleaned_data

    def _fill_missing_values(self, data: List[Dict[str, Any]], column: str, fill_method: str = "mean", fill_value: Any = None) -> List[Dict[str, Any]]:
        """Simulates filling missing values."""
        self.logger.warning("Actual missing value imputation is not implemented. This is a simulation.")
        
        values = [record[column] for record in data if column in record and record[column] is not None]
        
        if fill_method == "mean" and values:
            impute_val = sum(values) / len(values)
        elif fill_method == "median" and values:
            values.sort()
            mid = len(values) // 2
            impute_val = (values[mid] + values[mid-1]) / 2 if len(values) % 2 == 0 else values[mid]
        elif fill_method == "mode" and values:
            from collections import Counter
            impute_val = Counter(values).most_common(1)[0][0]
        elif fill_method == "constant":
            impute_val = fill_value
        else:
            impute_val = None # Cannot impute

        if impute_val is None:
            self.logger.warning(f"Could not determine imputation value for column '{column}'. Skipping.")
            return data

        for record in data:
            if column in record and record[column] is None:
                record[column] = impute_val
                self.logger.info(f"Simulated: Filled missing value in column '{column}' with {impute_val}.")
        return data

    def execute(self, data: List[Dict[str, Any]], operation: str, column: str, **kwargs: Any) -> List[Dict[str, Any]]:
        if operation == "remove_outliers":
            return self._remove_outliers(data, column, kwargs.get("threshold", 3.0))
        elif operation == "fill_missing_values":
            return self._fill_missing_values(data, column, kwargs.get("fill_method", "mean"), kwargs.get("fill_value"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataDenoisingAndCleaningTool functionality...")
    tool = DataDenoisingAndCleaningTool()
    
    sample_data = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 12},
        {"id": 3, "value": 150}, # Outlier
        {"id": 4, "value": None}, # Missing
        {"id": 5, "value": 18}
    ]
    print("\nOriginal Data:")
    print(json.dumps(sample_data, indent=2))

    try:
        print("\n--- Removing Outliers ---")
        cleaned_data = tool.execute(data=sample_data, operation="remove_outliers", column="value", threshold=2.0)
        print(json.dumps(cleaned_data, indent=2))

        print("\n--- Filling Missing Values (mean) ---")
        filled_data = tool.execute(data=cleaned_data, operation="fill_missing_values", column="value", fill_method="mean")
        print(json.dumps(filled_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")