import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MarketTrendComparisonTool(BaseTool):
    """
    A specialized tool for comparing market data series, calculating volatility,
    and analyzing relative growth.
    """

    def __init__(self, tool_name: str = "MarketTrendComparer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "market_comparison_data.json")
        self.market_data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={})

    @property
    def description(self) -> str:
        return "Compares market data series by analyzing volatility and relative growth."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_market_data", "calculate_volatility", "compare_trends"]},
                "data_id": {"type": "string"}, "market_segment": {"type": "string"}, "metric": {"type": "string"},
                "values": {"type": "array", "items": {"type": "number"}},
                "data_id_a": {"type": "string"}, "data_id_b": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.market_data, f, indent=4)

    def add_market_data(self, data_id: str, market_segment: str, metric: str, values: List[float]) -> Dict[str, Any]:
        """Adds a new market data series."""
        if data_id in self.market_data:
            raise ValueError(f"Data with ID '{data_id}' already exists.")
        
        new_data = {
            "data_id": data_id, "market_segment": market_segment, "metric": metric,
            "values": values, "added_at": datetime.now().isoformat()
        }
        self.market_data[data_id] = new_data
        self._save_data()
        return new_data

    def calculate_volatility(self, data_id: str) -> Dict[str, Any]:
        """Calculates the volatility (std dev) and growth of a data series."""
        data = self.market_data.get(data_id)
        if not data or not data.get('values'): raise ValueError(f"No data found for ID '{data_id}'.")
        
        values = data['values']
        if len(values) < 2: return {"error": "Not enough data to calculate volatility."}

        volatility = np.std(values)
        growth_pct = ((values[-1] - values[0]) / values[0]) * 100 if values[0] != 0 else 0

        return {
            "data_id": data_id,
            "volatility": round(volatility, 4),
            "growth_percent": round(growth_pct, 2),
            "mean": round(np.mean(values), 2)
        }

    def compare_trends(self, data_id_a: str, data_id_b: str) -> Dict[str, Any]:
        """Compares two market data series for volatility and growth."""
        analysis_a = self.calculate_volatility(data_id_a)
        analysis_b = self.calculate_volatility(data_id_b)

        comparison = {
            "more_volatile": data_id_a if analysis_a['volatility'] > analysis_b['volatility'] else data_id_b,
            "higher_growth": data_id_a if analysis_a['growth_percent'] > analysis_b['growth_percent'] else data_id_b,
        }
        
        return {
            "comparison_summary": comparison,
            "details": {data_id_a: analysis_a, data_id_b: analysis_b}
        }

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_market_data": self.add_market_data,
            "calculate_volatility": self.calculate_volatility,
            "compare_trends": self.compare_trends
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MarketTrendComparisonTool functionality...")
    temp_dir = "temp_market_comparer_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    comparer_tool = MarketTrendComparisonTool(data_dir=temp_dir)
    
    try:
        # 1. Add two data series
        print("\n--- Adding market data for two products ---")
        comparer_tool.execute(
            operation="add_market_data", data_id="product_A_sales", market_segment="electronics",
            metric="monthly_sales", values=[100, 110, 105, 120, 130]
        )
        comparer_tool.execute(
            operation="add_market_data", data_id="product_B_sales", market_segment="electronics",
            metric="monthly_sales", values=[50, 60, 80, 110, 150]
        )
        print("Data for Product A and Product B added.")

        # 2. Calculate volatility for one product
        print("\n--- Calculating volatility for Product A ---")
        volatility_a = comparer_tool.execute(operation="calculate_volatility", data_id="product_A_sales")
        print(json.dumps(volatility_a, indent=2))

        # 3. Compare the two products
        print("\n--- Comparing trends of Product A vs. Product B ---")
        comparison_report = comparer_tool.execute(operation="compare_trends", data_id_a="product_A_sales", data_id_b="product_B_sales")
        print(json.dumps(comparison_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")