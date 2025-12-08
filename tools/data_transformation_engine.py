import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataTransformationEngineTool(BaseTool):
    """
    A tool for defining and executing data transformation pipelines.
    """

    def __init__(self, tool_name: str = "data_transformation_engine"):
        super().__init__(tool_name)
        self.pipelines_file = "transformation_pipelines.json"
        self.pipelines: Dict[str, Dict[str, Any]] = self._load_pipelines()

    @property
    def description(self) -> str:
        return "Defines and executes data transformation pipelines, including filtering, deriving, renaming, and aggregating data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The transformation operation to perform.",
                    "enum": ["define_pipeline", "transform_data", "list_pipelines", "get_pipeline_details"]
                },
                "pipeline_id": {"type": "string"},
                "pipeline_name": {"type": "string"},
                "steps": {"type": "array", "items": {"type": "object"}},
                "description": {"type": "string"},
                "input_data": {"type": "array", "items": {"type": "object"}}
            },
            "required": ["operation"]
        }

    def _load_pipelines(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.pipelines_file):
            with open(self.pipelines_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted pipelines file '{self.pipelines_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_pipelines(self) -> None:
        with open(self.pipelines_file, 'w') as f:
            json.dump(self.pipelines, f, indent=4)

    def _define_pipeline(self, pipeline_id: str, pipeline_name: str, steps: List[Dict[str, Any]], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([pipeline_id, pipeline_name, steps]):
            raise ValueError("Pipeline ID, name, and steps cannot be empty.")
        if pipeline_id in self.pipelines:
            raise ValueError(f"Data transformation pipeline '{pipeline_id}' already exists.")

        new_pipeline = {
            "pipeline_id": pipeline_id, "pipeline_name": pipeline_name, "steps": steps,
            "description": description, "defined_at": datetime.now().isoformat()
        }
        self.pipelines[pipeline_id] = new_pipeline
        self._save_pipelines()
        return new_pipeline

    def _execute_step(self, data: List[Dict[str, Any]], step: Dict[str, Any]) -> List[Dict[str, Any]]:
        step_type = step.get("type")
        
        if step_type == "filter":
            column = step.get("column")
            condition_str = step.get("condition") # Renamed to avoid conflict with built-in
            if not column or not condition_str: raise ValueError("Filter step requires 'column' and 'condition'.")
            
            # Safely parse and apply condition without eval()
            # Supports simple operators: ==, !=, >, <, >=, <=
            import operator
            ops = {
                '==': operator.eq, '!=': operator.ne,
                '>': operator.gt, '<': operator.lt,
                '>=': operator.ge, '<=': operator.le
            }
            
            op_found = None
            value_str = None
            for op_symbol, op_func in ops.items():
                if condition_str.startswith(op_symbol):
                    op_found = op_func
                    value_str = condition_str[len(op_symbol):].strip()
                    break
            
            if not op_found:
                raise ValueError(f"Unsupported filter condition operator: {condition_str}. Only {list(ops.keys())} are supported.")

            filtered_data = []
            for record in data:
                if column in record and record[column] is not None:
                    try:
                        # Attempt to convert value_str to the type of record[column]
                        target_value = record[column]
                        if isinstance(target_value, (int, float)):
                            compare_value = type(target_value)(value_str)
                        else:
                            compare_value = value_str # Compare as string if not numeric
                        
                        if op_found(target_value, compare_value):
                            filtered_data.append(record)
                    except ValueError:
                        logger.warning(f"Type conversion error for filter condition '{condition_str}' on record {record}. Skipping.")
                    except Exception as e:
                        logger.warning(f"Could not evaluate filter condition '{condition_str}' for record {record}. Error: {e}")
                # else: pass # Record does not have column or value is None, so it's filtered out
            return filtered_data

        elif step_type == "derive":
            new_column = step.get("new_column")
            # Removed 'expression' due to security concerns with eval().
            # For now, derive will just set a default value or copy an existing column.
            source_column = step.get("source_column")
            default_value = step.get("default_value")

            if not new_column: raise ValueError("Derive step requires 'new_column'.")
            
            derived_data = []
            for record in data:
                new_record = record.copy()
                if source_column and source_column in record:
                    new_record[new_column] = record[source_column]
                elif default_value is not None:
                    new_record[new_column] = default_value
                else:
                    new_record[new_column] = None # Or raise error if no default/source
                derived_data.append(new_record)
            return derived_data

        elif step_type == "rename":
            old_column = step.get("old_column")
            new_column = step.get("new_column")
            if not old_column or not new_column: raise ValueError("Rename step requires 'old_column' and 'new_column'.")
            renamed_data = []
            for record in data:
                new_record = record.copy()
                if old_column in new_record: new_record[new_column] = new_record.pop(old_column)
                renamed_data.append(new_record)
            return renamed_data

        elif step_type == "aggregate":
            group_by_column = step.get("group_by_column")
            agg_column = step.get("agg_column")
            agg_func = step.get("agg_func")
            if not all([group_by_column, agg_column, agg_func]): raise ValueError("Aggregate step requires 'group_by_column', 'agg_column', and 'agg_func'.")
            
            aggregated_results = {}
            for record in data:
                group_key = record.get(group_by_column)
                value = record.get(agg_column)
                if group_key is not None and value is not None:
                    if group_key not in aggregated_results: aggregated_results[group_key] = []
                    aggregated_results[group_key].append(value)
            
            final_aggregated_data = []
            for key, values in aggregated_results.items():
                result_value = None
                if agg_func == "sum": result_value = sum(values)
                elif agg_func == "count": result_value = len(values)
                elif agg_func == "mean": result_value = sum(values) / len(values) if values else 0
                final_aggregated_data.append({group_by_column: key, f"{agg_column}_{agg_func}": result_value})
            return final_aggregated_data

        else:
            logger.warning(f"Unsupported transformation step type: '{step_type}'. Skipping step.")
            return data

    def _transform_data(self, pipeline_id: str, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline: raise ValueError(f"Data transformation pipeline '{pipeline_id}' not found.")
        if not isinstance(input_data, list) or not all(isinstance(item, dict) for item in input_data):
            raise ValueError("Input data must be a list of dictionaries.")

        transformed_data = list(input_data)
        for i, step in enumerate(pipeline["steps"]):
            try: transformed_data = self._execute_step(transformed_data, step)
            except Exception as e: raise RuntimeError(f"Pipeline execution failed at step {i+1}: {e}")
        
        return transformed_data

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_pipeline":
            return self._define_pipeline(kwargs.get("pipeline_id"), kwargs.get("pipeline_name"), kwargs.get("steps"), kwargs.get("description"))
        elif operation == "transform_data":
            return self._transform_data(kwargs.get("pipeline_id"), kwargs.get("input_data"))
        elif operation == "list_pipelines":
            return [{k: v for k, v in pipeline.items() if k != "steps"} for pipeline in self.pipelines.values()]
        elif operation == "get_pipeline_details":
            return self.pipelines.get(kwargs.get("pipeline_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataTransformationEngineTool functionality...")
    tool = DataTransformationEngineTool()
    
    sample_data = [
        {"id": 1, "first_name": "Alice", "last_name": "Smith", "age": 30, "email": "alice@example.com", "product": "A", "sales_amount": 100},
        {"id": 2, "first_name": "Bob", "last_name": "Johnson", "age": 22, "email": "bob@example.com", "product": "B", "sales_amount": 150},
    ]

    try:
        print("\n--- Defining Pipeline ---")
        tool.execute(operation="define_pipeline", pipeline_id="customer_etl", pipeline_name="Customer Data ETL", steps=[{"type": "filter", "column": "age", "condition": ">25"}], description="Filters customers by age.")
        
        print("\n--- Transforming Data ---")
        transformed_data = tool.execute(operation="transform_data", pipeline_id="customer_etl", input_data=sample_data)
        print(json.dumps(transformed_data, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.pipelines_file): os.remove(tool.pipelines_file)
        print("\nCleanup complete.")
