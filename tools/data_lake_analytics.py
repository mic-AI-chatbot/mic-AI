import logging
import os
import json
from typing import List, Dict, Any, Optional, Union
from tools.base_tool import BaseTool

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DataLakeAnalyticsTool(BaseTool):
    """
    A tool for simulating data lake analytics operations on local CSV files.
    """

    def __init__(self, tool_name: str = "data_lake_analytics"):
        super().__init__(tool_name)
        self._ensure_pandas_available()

    @property
    def description(self) -> str:
        return "Performs data lake analytics: loads data, runs SQL-like queries, generates summary reports, and lists contents."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The analytics operation to perform.",
                    "enum": ["load_data", "run_query", "generate_summary", "list_contents"]
                },
                "data_lake_path": {
                    "type": "string",
                    "description": "The path to the directory simulating the data lake."
                },
                "file_name": {
                    "type": "string",
                    "description": "The name of the CSV file to operate on."
                },
                "sql_query": {
                    "type": "string",
                    "description": "A simplified SQL-like query string (e.g., 'SELECT * WHERE age > 30')."
                },
                "group_by_column": {
                    "type": "string",
                    "description": "Optional column name to group the summary report by."
                }
            },
            "required": ["operation", "data_lake_path"]
        }

    def _ensure_pandas_available(self) -> None:
        if not PANDAS_AVAILABLE:
            raise ImportError("The 'pandas' library is required for DataLakeAnalyticsTool. Please install it with 'pip install pandas'.")

    def _load_data_from_lake(self, data_lake_path: str, file_name: str) -> pd.DataFrame:
        full_path = os.path.join(data_lake_path, file_name)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File '{file_name}' not found in data lake path '{data_lake_path}'.")
        if not full_path.lower().endswith('.csv'):
            raise ValueError(f"Only CSV files are supported. '{file_name}' is not a CSV.")
        
        try:
            df = pd.read_csv(full_path)
            logger.info(f"Loaded '{file_name}' from '{data_lake_path}'. Shape: {df.shape}")
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to load data from '{file_name}': {e}")

    def _run_sql_query(self, data_lake_path: str, file_name: str, sql_query: str) -> List[Dict[str, Any]]:
        df = self._load_data_from_lake(data_lake_path, file_name)
        query_parts = sql_query.upper().split("WHERE", 1)
        if len(query_parts) < 2:
            return df.to_dict(orient='records')

        where_clause = query_parts[1].strip()
        try:
            filtered_df = df.query(where_clause)
            logger.info(f"Query '{sql_query}' executed on '{file_name}'. Results shape: {filtered_df.shape}")
            return filtered_df.to_dict(orient='records')
        except Exception as e:
            raise ValueError(f"Invalid SQL-like query '{sql_query}': {e}")

    def _generate_summary_report(self, data_lake_path: str, file_name: str, group_by_column: Optional[str] = None) -> Dict[str, Any]:
        df = self._load_data_from_lake(data_lake_path, file_name)
        report: Dict[str, Any] = {
            "file_name": file_name, "total_records": len(df), "columns": df.columns.tolist(),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
        if group_by_column:
            if group_by_column not in df.columns:
                raise KeyError(f"Group by column '{group_by_column}' not found in '{file_name}'.")
            grouped_summary = df.groupby(group_by_column).describe(include='all').to_dict(orient='index')
            report["grouped_summary"] = grouped_summary
        else:
            report["overall_summary"] = df.describe(include='all').to_dict()
        return report

    def _list_data_lake_contents(self, data_lake_path: str) -> List[str]:
        if not os.path.exists(data_lake_path):
            raise FileNotFoundError(f"Data lake path '{data_lake_path}' does not exist.")
        if not os.path.isdir(data_lake_path):
            raise ValueError(f"Data lake path '{data_lake_path}' is not a directory.")
        return os.listdir(data_lake_path)

    def execute(self, operation: str, data_lake_path: str, **kwargs: Any) -> Union[pd.DataFrame, List[Dict[str, Any]], Dict[str, Any], List[str]]:
        if operation == "load_data":
            file_name = kwargs.get("file_name")
            if not file_name: raise ValueError("'file_name' is required for load_data operation.")
            return self._load_data_from_lake(data_lake_path, file_name)
        elif operation == "run_query":
            file_name = kwargs.get("file_name")
            sql_query = kwargs.get("sql_query")
            if not all([file_name, sql_query]): raise ValueError("'file_name' and 'sql_query' are required for run_query operation.")
            return self._run_sql_query(data_lake_path, file_name, sql_query)
        elif operation == "generate_summary":
            file_name = kwargs.get("file_name")
            if not file_name: raise ValueError("'file_name' is required for generate_summary operation.")
            return self._generate_summary_report(data_lake_path, file_name, kwargs.get("group_by_column"))
        elif operation == "list_contents":
            return self._list_data_lake_contents(data_lake_path)
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataLakeAnalyticsTool functionality...")
    tool = DataLakeAnalyticsTool()
    
    data_lake_dir = "my_data_lake"
    dummy_csv_path = os.path.join(data_lake_dir, "sales_data.csv")
    
    try:
        os.makedirs(data_lake_dir, exist_ok=True)
        dummy_data = pd.DataFrame({
            'product': ['A', 'B', 'A', 'C', 'B', 'A'],
            'region': ['East', 'West', 'East', 'North', 'West', 'South'],
            'sales': [100, 150, 120, 200, 180, 90],
            'units': [10, 15, 12, 20, 18, 9]
        })
        dummy_data.to_csv(dummy_csv_path, index=False)
        print(f"\nCreated dummy data lake at '{data_lake_dir}' with '{os.path.basename(dummy_csv_path)}'.")

        print("\n--- Listing Data Lake Contents ---")
        contents = tool.execute(operation="list_contents", data_lake_path=data_lake_dir)
        print(json.dumps(contents, indent=2))

        print("\n--- Running SQL-like Query (sales > 100) ---")
        query_results = tool.execute(operation="run_query", data_lake_path=data_lake_dir, file_name="sales_data.csv", sql_query="SELECT * WHERE sales > 100")
        print(json.dumps(query_results, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(data_lake_dir):
            shutil.rmtree(data_lake_dir)
        print("\nCleanup complete.")