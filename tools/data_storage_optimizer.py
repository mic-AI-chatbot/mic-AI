import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataStorageOptimizerTool(BaseTool):
    """
    A tool for simulating data storage optimization actions, including
    registering storage systems, analyzing usage, and applying optimizations.
    """

    def __init__(self, tool_name: str = "data_storage_optimizer"):
        super().__init__(tool_name)
        self.systems_file = "storage_systems.json"
        self.systems: Dict[str, Dict[str, Any]] = self._load_systems()

    @property
    def description(self) -> str:
        return "Simulates data storage optimization: registers systems, analyzes usage, and applies optimizations like compression or tiering."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The storage optimization operation to perform.",
                    "enum": ["register_storage_system", "analyze_usage", "optimize_storage", "list_storage_systems", "get_system_details"]
                },
                "system_id": {"type": "string"},
                "system_name": {"type": "string"},
                "total_capacity_gb": {"type": "integer", "minimum": 1},
                "used_capacity_gb": {"type": "integer", "minimum": 0},
                "cost_per_gb_usd": {"type": "number", "minimum": 0.0},
                "optimization_type": {"type": "string", "enum": ["compression", "tiering", "deduplication"]}
            },
            "required": ["operation"]
        }

    def _load_systems(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.systems_file):
            with open(self.systems_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted systems file '{self.systems_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_systems(self) -> None:
        with open(self.systems_file, 'w') as f:
            json.dump(self.systems, f, indent=4)

    def _register_storage_system(self, system_id: str, system_name: str, total_capacity_gb: int, used_capacity_gb: int, cost_per_gb_usd: float) -> Dict[str, Any]:
        if not all([system_id, system_name, total_capacity_gb, used_capacity_gb, cost_per_gb_usd is not None]):
            raise ValueError("All parameters are required for registration.")
        if used_capacity_gb > total_capacity_gb: raise ValueError("Used capacity cannot exceed total capacity.")
        if system_id in self.systems: raise ValueError(f"Storage system '{system_id}' already exists.")

        new_system = {
            "system_id": system_id, "system_name": system_name, "total_capacity_gb": total_capacity_gb,
            "used_capacity_gb": used_capacity_gb, "cost_per_gb_usd": cost_per_gb_usd,
            "registered_at": datetime.now().isoformat()
        }
        self.systems[system_id] = new_system
        self._save_systems()
        return new_system

    def _analyze_usage(self, system_id: str) -> Dict[str, Any]:
        system = self.systems.get(system_id)
        if not system: raise ValueError(f"Storage system '{system_id}' not found.")

        utilization_percent = (system["used_capacity_gb"] / system["total_capacity_gb"]) * 100
        remaining_capacity_gb = system["total_capacity_gb"] - system["used_capacity_gb"]
        estimated_monthly_cost = system["used_capacity_gb"] * system["cost_per_gb_usd"]

        analysis_result = {
            "system_id": system_id, "system_name": system["system_name"], "total_capacity_gb": system["total_capacity_gb"],
            "used_capacity_gb": system["used_capacity_gb"], "utilization_percent": round(utilization_percent, 2),
            "remaining_capacity_gb": round(remaining_capacity_gb, 2), "estimated_monthly_cost_usd": round(estimated_monthly_cost, 2),
            "analyzed_at": datetime.now().isoformat()
        }
        return analysis_result

    def _optimize_storage(self, system_id: str, optimization_type: str) -> Dict[str, Any]:
        system = self.systems.get(system_id)
        if not system: raise ValueError(f"Storage system '{system_id}' not found.")
        if optimization_type not in ["compression", "tiering", "deduplication"]: raise ValueError(f"Unsupported optimization type: '{optimization_type}'.")

        original_used_capacity = system["used_capacity_gb"]
        original_monthly_cost = original_used_capacity * system["cost_per_gb_usd"]
        
        reduction_factor = 0.0
        if optimization_type == "compression": reduction_factor = 0.3
        elif optimization_type == "deduplication": reduction_factor = 0.2
        
        optimized_used_capacity = original_used_capacity * (1 - reduction_factor)
        optimized_monthly_cost = optimized_used_capacity * system["cost_per_gb_usd"]

        if optimization_type == "tiering":
            # Simulate moving 50% of data to a cheaper tier (e.g., 50% cheaper)
            tiering_effect_on_cost = 0.5 * system["used_capacity_gb"] * (system["cost_per_gb_usd"] * 0.5)
            optimized_monthly_cost = (original_used_capacity * system["cost_per_gb_usd"]) - tiering_effect_on_cost

        system["used_capacity_gb"] = round(optimized_used_capacity, 2)
        self._save_systems()

        optimization_result = {
            "system_id": system_id, "system_name": system["system_name"], "optimization_type": optimization_type,
            "original_used_capacity_gb": round(original_used_capacity, 2), "optimized_used_capacity_gb": round(optimized_used_capacity, 2),
            "capacity_reduction_percent": round(reduction_factor * 100, 2),
            "original_monthly_cost_usd": round(original_monthly_cost, 2), "optimized_monthly_cost_usd": round(optimized_monthly_cost, 2),
            "cost_reduction_percent": round(((original_monthly_cost - optimized_monthly_cost) / original_monthly_cost) * 100, 2) if original_monthly_cost > 0 else 0,
            "optimized_at": datetime.now().isoformat()
        }
        return optimization_result

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "register_storage_system":
            return self._register_storage_system(kwargs.get("system_id"), kwargs.get("system_name"), kwargs.get("total_capacity_gb"), kwargs.get("used_capacity_gb"), kwargs.get("cost_per_gb_usd"))
        elif operation == "analyze_usage":
            return self._analyze_usage(kwargs.get("system_id"))
        elif operation == "optimize_storage":
            return self._optimize_storage(kwargs.get("system_id"), kwargs.get("optimization_type"))
        elif operation == "list_storage_systems":
            return list(self.systems.values())
        elif operation == "get_system_details":
            return self.systems.get(kwargs.get("system_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataStorageOptimizerTool functionality...")
    tool = DataStorageOptimizerTool()
    
    try:
        print("\n--- Registering Storage System ---")
        tool.execute(operation="register_storage_system", system_id="s3_prod", system_name="Production S3", total_capacity_gb=1000, used_capacity_gb=700, cost_per_gb_usd=0.023)
        
        print("\n--- Analyzing Usage ---")
        usage_report = tool.execute(operation="analyze_usage", system_id="s3_prod")
        print(json.dumps(usage_report, indent=2))

        print("\n--- Optimizing Storage (Compression) ---")
        optimization_result = tool.execute(operation="optimize_storage", system_id="s3_prod", optimization_type="compression")
        print(json.dumps(optimization_result, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.systems_file): os.remove(tool.systems_file)
        print("\nCleanup complete.")