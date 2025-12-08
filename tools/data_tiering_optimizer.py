import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataTieringOptimizerTool(BaseTool):
    """
    A tool for simulating data tiering optimization, allowing for the registration
    of data sets, analysis of access patterns, and optimization of storage tiers.
    """

    def __init__(self, tool_name: str = "data_tiering_optimizer"):
        super().__init__(tool_name)
        self.tiers_file = "data_tiers.json"
        self.data_sets: Dict[str, Dict[str, Any]] = self._load_data_sets()

    @property
    def description(self) -> str:
        return "Simulates data tiering optimization: registers data sets, analyzes access patterns, and optimizes storage tiers."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The data tiering operation to perform.",
                    "enum": ["register_data_set", "analyze_access_patterns", "optimize_tiers", "list_data_sets", "get_data_set_details"]
                },
                "data_set_id": {"type": "string"},
                "data_set_name": {"type": "string"},
                "current_tier": {"type": "string", "enum": ["hot", "cold", "archive"]},
                "size_gb": {"type": "integer", "minimum": 1},
                "access_frequency": {"type": "string", "enum": ["frequent", "infrequent", "rare"]},
                "optimization_strategy": {"type": "string", "enum": ["cost_optimization", "performance_optimization"]}
            },
            "required": ["operation"]
        }

    def _load_data_sets(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.tiers_file):
            with open(self.tiers_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted data sets file '{self.tiers_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_data_sets(self) -> None:
        with open(self.tiers_file, 'w') as f:
            json.dump(self.data_sets, f, indent=4)

    def _register_data_set(self, data_set_id: str, data_set_name: str, current_tier: str, size_gb: int, access_frequency: str) -> Dict[str, Any]:
        if not all([data_set_id, data_set_name, current_tier, size_gb, access_frequency]):
            raise ValueError("All parameters are required for data set registration.")
        if data_set_id in self.data_sets: raise ValueError(f"Data set '{data_set_id}' already exists.")
        if current_tier not in ["hot", "cold", "archive"]: raise ValueError(f"Invalid current_tier: '{current_tier}'.")
        if access_frequency not in ["frequent", "infrequent", "rare"]: raise ValueError(f"Invalid access_frequency: '{access_frequency}'.")

        new_data_set = {
            "data_set_id": data_set_id, "data_set_name": data_set_name, "current_tier": current_tier,
            "size_gb": size_gb, "access_frequency": access_frequency, "registered_at": datetime.now().isoformat()
        }
        self.data_sets[data_set_id] = new_data_set
        self._save_data_sets()
        return new_data_set

    def _analyze_access_patterns(self, data_set_id: str) -> Dict[str, Any]:
        data_set = self.data_sets.get(data_set_id)
        if not data_set: raise ValueError(f"Data set '{data_set_id}' not found.")

        suggested_tier = data_set["current_tier"]
        reason = "No change suggested."

        if data_set["access_frequency"] == "frequent" and data_set["current_tier"] != "hot":
            suggested_tier = "hot"; reason = "Frequent access detected, suggesting move to hot tier for performance."
        elif data_set["access_frequency"] == "infrequent" and data_set["current_tier"] == "hot":
            suggested_tier = "cold"; reason = "Infrequent access detected, suggesting move to cold tier for cost savings."
        elif data_set["access_frequency"] == "rare" and data_set["current_tier"] != "archive":
            suggested_tier = "archive"; reason = "Rare access detected, suggesting move to archive tier for maximum cost savings."

        analysis_result = {
            "data_set_id": data_set_id, "data_set_name": data_set["data_set_name"],
            "current_tier": data_set["current_tier"], "access_frequency": data_set["access_frequency"],
            "suggested_tier": suggested_tier, "reason": reason, "analyzed_at": datetime.now().isoformat()
        }
        return analysis_result

    def _optimize_tiers(self, data_set_id: str, optimization_strategy: str) -> Dict[str, Any]:
        data_set = self.data_sets.get(data_set_id)
        if not data_set: raise ValueError(f"Data set '{data_set_id}' not found.")
        if optimization_strategy not in ["cost_optimization", "performance_optimization"]: raise ValueError(f"Unsupported optimization strategy: '{optimization_strategy}'.")

        original_tier = data_set["current_tier"]
        new_tier = original_tier
        reason = "No change based on strategy."

        if optimization_strategy == "cost_optimization":
            if data_set["access_frequency"] == "infrequent" and original_tier == "hot": new_tier = "cold"; reason = "Moved to cold tier for cost optimization."
            elif data_set["access_frequency"] == "rare" and original_tier != "archive": new_tier = "archive"; reason = "Moved to archive tier for cost optimization."
        elif optimization_strategy == "performance_optimization":
            if data_set["access_frequency"] == "frequent" and original_tier != "hot": new_tier = "hot"; reason = "Moved to hot tier for performance optimization."
        
        data_set["current_tier"] = new_tier
        self._save_data_sets()

        optimization_result = {
            "data_set_id": data_set_id, "data_set_name": data_set["data_set_name"],
            "original_tier": original_tier, "new_tier": new_tier, "optimization_strategy": optimization_strategy,
            "reason": reason, "optimized_at": datetime.now().isoformat()
        }
        return optimization_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "register_data_set":
            return self._register_data_set(kwargs.get("data_set_id"), kwargs.get("data_set_name"), kwargs.get("current_tier"), kwargs.get("size_gb"), kwargs.get("access_frequency"))
        elif operation == "analyze_access_patterns":
            return self._analyze_access_patterns(kwargs.get("data_set_id"))
        elif operation == "optimize_tiers":
            return self._optimize_tiers(kwargs.get("data_set_id"), kwargs.get("optimization_strategy"))
        elif operation == "list_data_sets":
            return list(self.data_sets.values())
        elif operation == "get_data_set_details":
            return self.data_sets.get(kwargs.get("data_set_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataTieringOptimizerTool functionality...")
    tool = DataTieringOptimizerTool()
    
    try:
        print("\n--- Registering Data Set ---")
        tool.execute(operation="register_data_set", data_set_id="customer_data", data_set_name="Customer Transactions", current_tier="hot", size_gb=500, access_frequency="frequent")
        
        print("\n--- Analyzing Access Patterns ---")
        analysis_result = tool.execute(operation="analyze_access_patterns", data_set_id="customer_data")
        print(json.dumps(analysis_result, indent=2))

        print("\n--- Optimizing Tiers ---")
        optimization_result = tool.execute(operation="optimize_tiers", data_set_id="customer_data", optimization_strategy="cost_optimization")
        print(json.dumps(optimization_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.tiers_file): os.remove(tool.tiers_file)
        print("\nCleanup complete.")
