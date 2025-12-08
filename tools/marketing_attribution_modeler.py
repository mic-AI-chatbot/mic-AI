

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MarketingAttributionModelerTool(BaseTool):
    """
    A tool to perform marketing attribution analysis using classic models like
    'first_click', 'last_click', 'linear', and 'time_decay'.
    """

    def __init__(self, tool_name: str = "AttributionModeler", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "attribution_data.json")
        self.data: Dict[str, List[Dict[str, Any]]] = self._load_data(self.data_file, default={"conversion_paths": []})

    @property
    def description(self) -> str:
        return "Calculates marketing channel contributions using various attribution models."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_conversion_paths", "run_attribution_model", "list_paths"]},
                "paths": {"type": "array", "description": "List of conversion paths, where each path is a list of channels. E.g., [['social', 'paid'], ['organic']]", "items": {"type": "array"}},
                "model_type": {"type": "string", "enum": ["first_click", "last_click", "linear", "time_decay"]},
                "half_life_days": {"type": "integer", "default": 7, "description": "Half-life in days for the time-decay model."}
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
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=4)

    def add_conversion_paths(self, paths: List[List[str]]) -> Dict[str, Any]:
        """Adds new conversion paths to the dataset."""
        if not paths: raise ValueError("Paths cannot be empty.")
        
        # Assuming each path leads to one conversion
        for path in paths:
            self.data["conversion_paths"].append({"path": path, "conversions": 1})
            
        self._save_data()
        return {"status": "success", "added_count": len(paths)}

    def run_attribution_model(self, model_type: str, half_life_days: int = 7) -> Dict[str, float]:
        """Runs a specified attribution model on the stored conversion data."""
        if not self.data["conversion_paths"]:
            return {"error": "No conversion paths available to analyze."}

        channel_credits = Counter()
        total_conversions = 0

        for item in self.data["conversion_paths"]:
            path = item["path"]
            conversions = item["conversions"]
            total_conversions += conversions
            
            if not path: continue

            if model_type == "first_click":
                channel_credits[path[0]] += conversions
            elif model_type == "last_click":
                channel_credits[path[-1]] += conversions
            elif model_type == "linear":
                credit_per_channel = conversions / len(path)
                for channel in path:
                    channel_credits[channel] += credit_per_channel
            elif model_type == "time_decay":
                total_weight = 0
                weights = []
                for i in range(len(path)):
                    # Assuming each step is one day for simplicity
                    days_before_conversion = len(path) - 1 - i
                    weight = 2 ** (-days_before_conversion / half_life_days)
                    weights.append(weight)
                    total_weight += weight
                
                if total_weight > 0:
                    for i, channel in enumerate(path):
                        channel_credits[channel] += (weights[i] / total_weight) * conversions
            else:
                raise ValueError(f"Unsupported model type: {model_type}")

        # Normalize to percentage
        if total_conversions > 0:
            return {channel: round((credit / total_conversions) * 100, 2) for channel, credit in channel_credits.items()}
        return {}

    def list_paths(self) -> List[Dict[str, Any]]:
        """Lists all stored conversion paths."""
        return self.data["conversion_paths"]

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_conversion_paths": self.add_conversion_paths,
            "run_attribution_model": self.run_attribution_model,
            "list_paths": self.list_paths
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MarketingAttributionModelerTool functionality...")
    temp_dir = "temp_attribution_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    modeler_tool = MarketingAttributionModelerTool(data_dir=temp_dir)
    
    try:
        # 1. Add conversion path data
        print("\n--- Adding conversion path data ---")
        paths_to_add = [
            ["social", "organic", "paid"],
            ["organic", "paid"],
            ["social", "email"],
            ["paid"],
            ["social", "organic", "email", "paid"]
        ]
        modeler_tool.execute(operation="add_conversion_paths", paths=paths_to_add)
        print(f"{len(paths_to_add)} paths added.")

        # 2. Run different attribution models
        print("\n--- Running 'last_click' model ---")
        last_click_report = modeler_tool.execute(operation="run_attribution_model", model_type="last_click")
        print(json.dumps(last_click_report, indent=2))

        print("\n--- Running 'first_click' model ---")
        first_click_report = modeler_tool.execute(operation="run_attribution_model", model_type="first_click")
        print(json.dumps(first_click_report, indent=2))

        print("\n--- Running 'linear' model ---")
        linear_report = modeler_tool.execute(operation="run_attribution_model", model_type="linear")
        print(json.dumps(linear_report, indent=2))
        
        print("\n--- Running 'time_decay' model ---")
        time_decay_report = modeler_tool.execute(operation="run_attribution_model", model_type="time_decay")
        print(json.dumps(time_decay_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
