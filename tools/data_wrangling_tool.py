import logging
import os
import json
import random
from typing import List, Dict, Any, Optional, Union
from .base_tool import BaseTool

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataWranglingTool(BaseTool):
    """
    A tool for performing various data wrangling operations such as cleaning,
    transforming, merging, and pivoting on structured data (lists of dictionaries).
    """

    def __init__(self, tool_name: str = "data_wrangling_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Performs data wrangling operations: cleaning, transforming, merging, and pivoting structured data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The wrangling operation to perform.",
                    "enum": ["clean_data", "transform_data", "merge_data", "pivot_data"]
                },
                "data": {"type": "array", "items": {"type": "object"}},
                "cleaning_rules": {"type": "array", "items": {"type": "object"}},
                "transformations": {"type": "array", "items": {"type": "object"}},
                "data2": {"type": "array", "items": {"type": "object"}},
                "on_key": {"type": "string"},
                "how": {"type": "string", "enum": ["inner", "left", "right", "outer"]},
                "index": {"type": "string"},
                "columns": {"type": "string"},
                "values": {"type": "string"},
                "aggfunc": {"type": "string", "enum": ["sum", "mean", "count"]}
            },
            "required": ["operation", "data"]
        }

    def _ensure_data_is_list_of_dicts(self, data: List[Dict[str, Any]]) -> None:
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Input data must be a list of dictionaries.")

    def _clean_data(self, data: List[Dict[str, Any]], cleaning_rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        cleaned_data = [record.copy() for record in data]

        for rule in cleaning_rules:
            rule_type = rule.get("type")
            column = rule.get("column")
            
            if rule_type == "fill_missing":
                if not column: raise ValueError("Fill missing rule requires 'column'.")
                fill_value = rule.get("value")
                for record in cleaned_data:
                    if column in record and (record[column] is None or (isinstance(record[column], str) and not record[column].strip())):
                        record[column] = fill_value
            elif rule_type == "remove_duplicates":
                subset = rule.get("subset")
                if PANDAS_AVAILABLE:
                    df = pd.DataFrame(cleaned_data)
                    cleaned_data = df.drop_duplicates(subset=subset).to_dict(orient='records')
                else:
                    seen = set()
                    unique_records = []
                    for record in cleaned_data:
                        key_tuple = tuple(record.get(col) for col in subset) if subset else tuple(sorted(record.items()))
                        if key_tuple not in seen: unique_records.append(record); seen.add(key_tuple)
                    cleaned_data = unique_records
            elif rule_type == "standardize_case":
                if not column: raise ValueError("Standardize case rule requires 'column'.")
                case_type = rule.get("case", "lower")
                for record in cleaned_data:
                    if column in record and isinstance(record[column], str):
                        if case_type == "lower": record[column] = record[column].lower()
                        elif case_type == "upper": record[column] = record[column].upper()
                        elif case_type == "title": record[column] = record[column].title()
            else:
                logger.warning(f"Unsupported cleaning rule type: '{rule_type}'. Skipping.")
        return cleaned_data

    def _transform_data(self, data: List[Dict[str, Any]], transformations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        transformed_data = [record.copy() for record in data]

        for transform in transformations:
            transform_type = transform.get("type")
            
            if transform_type == "rename_column":
                old_name = transform.get("old_name")
                new_name = transform.get("new_name")
                if not old_name or not new_name: raise ValueError("Rename column requires 'old_name' and 'new_name'.")
                for record in transformed_data:
                    if old_name in record: record[new_name] = record.pop(old_name)
            elif transform_type == "change_type":
                column = transform.get("column")
                new_type = transform.get("new_type")
                if not column or not new_type: raise ValueError("Change type requires 'column' and 'new_type'.")
                for record in transformed_data:
                    if column in record and record[column] is not None:
                        try:
                            if new_type == "int": record[column] = int(record[column])
                            elif new_type == "float": record[column] = float(record[column])
                            elif new_type == "str": record[column] = str(record[column])
                        except ValueError: logger.warning(f"Could not convert value '{record[column]}' in column '{column}' to type '{new_type}'.")
            elif transform_type == "create_feature":
                new_column = transform.get("new_column")
                expression = transform.get("expression")
                if not new_column or not expression: raise ValueError("Create feature requires 'new_column' and 'expression'.")
                for record in transformed_data:
                    try: record[new_column] = eval(expression, {"__builtins__": {}}, {"record": record})
                    except Exception as e: logger.warning(f"Could not create feature '{new_column}' with expression '{expression}' for record {record}. Error: {e}"); record[new_column] = None
            else:
                logger.warning(f"Unsupported transformation type: '{transform_type}'. Skipping.")
        return transformed_data

    def _merge_data(self, data1: List[Dict[str, Any]], data2: List[Dict[str, Any]], on_key: str, how: str = 'inner') -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data1); self._ensure_data_is_list_of_dicts(data2)
        if not on_key: raise ValueError("Merge requires an 'on_key'.")
        if how not in ['inner', 'left', 'right', 'outer']: raise ValueError(f"Unsupported merge type '{how}'.")

        if PANDAS_AVAILABLE:
            df1 = pd.DataFrame(data1); df2 = pd.DataFrame(data2)
            merged_df = pd.merge(df1, df2, on=on_key, how=how)
            return merged_df.to_dict(orient='records')
        else:
            if how != 'inner': logger.warning("Pandas not available. Only 'inner' merge is fully supported without pandas.")
            merged_results = []
            for rec1 in data1:
                for rec2 in data2:
                    if rec1.get(on_key) == rec2.get(on_key): merged_results.append({**rec1, **rec2})
            return merged_results

    def _pivot_data(self, data: List[Dict[str, Any]], index: str, columns: str, values: str, aggfunc: str = 'sum') -> List[Dict[str, Any]]:
        self._ensure_data_is_list_of_dicts(data)
        if not all([index, columns, values]): raise ValueError("Pivot requires 'index', 'columns', and 'values'.")
        if aggfunc not in ['sum', 'mean', 'count']: raise ValueError(f"Unsupported aggregation function '{aggfunc}'.")

        if PANDAS_AVAILABLE:
            df = pd.DataFrame(data)
            pivot_df = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc)
            pivot_df.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in pivot_df.columns]
            pivot_df = pivot_df.reset_index()
            return pivot_df.to_dict(orient='records')
        else:
            logger.warning("Pandas not available. Pivot operation is not fully supported without pandas.")
            return data

    def execute(self, operation: str, data: List[Dict[str, Any]], **kwargs: Any) -> List[Dict[str, Any]]:
        if operation == "clean_data":
            return self._clean_data(data, kwargs.get("cleaning_rules", []))
        elif operation == "transform_data":
            return self._transform_data(data, kwargs.get("transformations", []))
        elif operation == "merge_data":
            return self._merge_data(data, kwargs.get("data2"), kwargs.get("on_key"), kwargs.get("how", "inner"))
        elif operation == "pivot_data":
            return self._pivot_data(data, kwargs.get("index"), kwargs.get("columns"), kwargs.get("values"), kwargs.get("aggfunc", "sum"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataWranglingTool functionality...")
    tool = DataWranglingTool()
    
    sample_data = [
        {"id": 1, "name": "Alice", "age": 30, "email": "alice@example.com", "status": "active"},
        {"id": 2, "name": "Bob", "age": None, "email": "bob@example.com", "status": "pending"},
        {"id": 3, "name": "Charlie", "age": 35, "email": "charlie@example.com", "status": "active"},
        {"id": 2, "name": "Bob", "age": 22, "email": "bob@example.com", "status": "pending"}, # Duplicate
    ]

    try:
        print("\n--- Cleaning Data ---")
        cleaning_rules = [{"type": "fill_missing", "column": "age", "value": -1}, {"type": "remove_duplicates", "subset": ["id"]}]
        cleaned_data = tool.execute(operation="clean_data", data=sample_data, cleaning_rules=cleaning_rules)
        print(json.dumps(cleaned_data, indent=2))

        print("\n--- Transforming Data ---")
        transformations = [{"type": "rename_column", "old_name": "email", "new_name": "contact_email"}]
        transformed_data = tool.execute(operation="transform_data", data=cleaned_data, transformations=transformations)
        print(json.dumps(transformed_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
