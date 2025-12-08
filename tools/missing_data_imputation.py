import logging
import numpy as np
from collections import Counter
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MissingDataImputationTool(BaseTool):
    """
    A tool for imputing missing values in datasets using various methods
    like mean, median, or mode.
    """
    def __init__(self, tool_name: str = "MissingDataImputation", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Intelligently fills in missing values (None) in datasets using mean, median, or mode imputation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_with_missing_values": {
                    "type": "object",
                    "description": "The dataset as a dictionary of lists, e.g., {'col_A': [1, 2, None], 'col_B': ['X', None, 'Y']}.",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"type": ["string", "number", "null"]}
                    }
                },
                "imputation_method": {
                    "type": "string",
                    "enum": ["mean", "median", "mode"],
                    "default": "mean",
                    "description": "The method for imputation ('mean', 'median', 'mode')."
                }
            },
            "required": ["data_with_missing_values"]
        }

    def execute(self, data_with_missing_values: Dict[str, List[Union[int, float, str, None]]], imputation_method: str = "mean", **kwargs: Any) -> Dict[str, Any]:
        """
        Imputes missing values in the provided dataset using the specified method.
        """
        if not data_with_missing_values:
            return {"imputed_data": {}, "summary": "No data provided for imputation."}

        imputed_data = {col: list(values) for col, values in data_with_missing_values.items()}
        imputation_summary = {}

        for column, values in imputed_data.items():
            missing_indices = [i for i, x in enumerate(values) if x is None]
            if not missing_indices:
                imputation_summary[column] = "No missing values."
                continue

            non_missing_values = [x for x in values if x is not None]
            if not non_missing_values:
                imputation_summary[column] = "All values are missing; cannot impute."
                continue

            imputed_value: Union[int, float, str, None] = None
            
            if imputation_method == "mean":
                if all(isinstance(x, (int, float)) for x in non_missing_values):
                    imputed_value = np.mean(non_missing_values)
                else:
                    imputation_summary[column] = f"Skipped (mean): Column '{column}' contains non-numeric data."
                    continue
            elif imputation_method == "median":
                if all(isinstance(x, (int, float)) for x in non_missing_values):
                    imputed_value = np.median(non_missing_values)
                else:
                    imputation_summary[column] = f"Skipped (median): Column '{column}' contains non-numeric data."
                    continue
            elif imputation_method == "mode":
                imputed_value = Counter(non_missing_values).most_common(1)[0][0]
            else:
                raise ValueError(f"Unsupported imputation method: {imputation_method}")

            for idx in missing_indices:
                imputed_data[column][idx] = imputed_value
            
            imputation_summary[column] = f"{len(missing_indices)} missing values imputed with {imputation_method} ({imputed_value})."

        return {
            "imputed_data": imputed_data,
            "summary": imputation_summary
        }

if __name__ == '__main__':
    print("Demonstrating MissingDataImputationTool functionality...")
    
    imputation_tool = MissingDataImputationTool()
    
    sample_data = {
        "age": [25, 30, None, 40, 22, None, 35],
        "income": [50000, None, 60000, 75000, 48000, 90000, None],
        "city": ["NY", "LA", "NY", None, "SF", "LA", "NY"],
        "experience": [5, 8, 3, None, 2, 10, 7]
    }
    
    try:
        print("\n--- Original Data ---")
        print(json.dumps(sample_data, indent=2))

        # 1. Impute with 'mean'
        print("\n--- Imputing with 'mean' method ---")
        mean_imputed_result = imputation_tool.execute(data_with_missing_values=sample_data, imputation_method="mean")
        print("Imputed Data:")
        print(json.dumps(mean_imputed_result["imputed_data"], indent=2))
        print("Summary:")
        print(json.dumps(mean_imputed_result["summary"], indent=2))

        # 2. Impute with 'median'
        print("\n--- Imputing with 'median' method ---")
        median_imputed_result = imputation_tool.execute(data_with_missing_values=sample_data, imputation_method="median")
        print("Imputed Data:")
        print(json.dumps(median_imputed_result["imputed_data"], indent=2))
        print("Summary:")
        print(json.dumps(median_imputed_result["summary"], indent=2))

        # 3. Impute with 'mode'
        print("\n--- Imputing with 'mode' method ---")
        mode_imputed_result = imputation_tool.execute(data_with_missing_values=sample_data, imputation_method="mode")
        print("Imputed Data:")
        print(json.dumps(mode_imputed_result["imputed_data"], indent=2))
        print("Summary:")
        print(json.dumps(mode_imputed_result["summary"], indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")