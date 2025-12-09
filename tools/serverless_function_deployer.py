import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ServerlessConfigCostEstimatorTool(BaseTool):
    """
    A tool that simulates serverless function configuration and cost estimation,
    allowing users to define function resources and get estimated monthly costs.
    """

    def __init__(self, tool_name: str = "ServerlessConfigCostEstimator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.configs_file = os.path.join(self.data_dir, "function_configurations.json")
        self.costs_file = os.path.join(self.data_dir, "cost_estimates.json")
        
        # Function configurations: {function_id: {name: ..., runtime: ..., memory_mb: ..., timeout_seconds: ...}}
        self.function_configurations: Dict[str, Dict[str, Any]] = self._load_data(self.configs_file, default={})
        # Cost estimates: {estimate_id: {function_id: ..., num_invocations: ..., estimated_cost: ...}}
        self.cost_estimates: Dict[str, Dict[str, Any]] = self._load_data(self.costs_file, default={})

    @property
    def description(self) -> str:
        return "Simulates serverless function configuration and cost estimation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["configure_function", "estimate_cost", "get_function_config"]},
                "function_id": {"type": "string"},
                "name": {"type": "string"},
                "runtime": {"type": "string", "enum": ["nodejs", "python", "java", "go"]},
                "memory_mb": {"type": "integer", "minimum": 128, "maximum": 1024},
                "timeout_seconds": {"type": "integer", "minimum": 1, "maximum": 300},
                "num_invocations_per_month": {"type": "integer", "minimum": 1},
                "estimate_id": {"type": "string", "description": "ID of the cost estimate to retrieve."}
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

    def _save_configs(self):
        with open(self.configs_file, 'w') as f: json.dump(self.function_configurations, f, indent=2)

    def _save_costs(self):
        with open(self.costs_file, 'w') as f: json.dump(self.cost_estimates, f, indent=2)

    def configure_function(self, function_id: str, name: str, runtime: str, memory_mb: int, timeout_seconds: int) -> Dict[str, Any]:
        """Configures a serverless function's resources."""
        if function_id in self.function_configurations: raise ValueError(f"Function '{function_id}' already configured.")
        
        new_config = {
            "id": function_id, "name": name, "runtime": runtime,
            "memory_mb": memory_mb, "timeout_seconds": timeout_seconds,
            "configured_at": datetime.now().isoformat()
        }
        self.function_configurations[function_id] = new_config
        self._save_configs()
        return new_config

    def estimate_cost(self, function_id: str, num_invocations_per_month: int) -> Dict[str, Any]:
        """Estimates the monthly cost of a serverless function."""
        config = self.function_configurations.get(function_id)
        if not config: raise ValueError(f"Function '{function_id}' not configured. Configure it first.")
        
        # Simplified cost model (e.g., AWS Lambda pricing approximation)
        # Free tier not considered for simplicity
        
        # Cost per GB-second: e.g., $0.0000166667 per GB-second
        # Cost per 1M requests: e.g., $0.20 per 1M requests
        
        memory_gb = config["memory_mb"] / 1024
        duration_seconds = config["timeout_seconds"] # Assuming average execution time is close to timeout for max cost
        
        # Compute cost
        compute_cost_per_invocation = memory_gb * duration_seconds * 0.0000166667
        total_compute_cost = compute_cost_per_invocation * num_invocations_per_month
        
        request_cost_per_invocation = 0.20 / 1_000_000
        total_request_cost = request_cost_per_invocation * num_invocations_per_month
        
        estimated_monthly_cost = total_compute_cost + total_request_cost
        
        estimate_id = f"cost_est_{function_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        new_estimate = {
            "id": estimate_id, "function_id": function_id, "num_invocations_per_month": num_invocations_per_month,
            "estimated_monthly_cost_usd": round(estimated_monthly_cost, 4),
            "estimated_at": datetime.now().isoformat()
        }
        self.cost_estimates[estimate_id] = new_estimate
        self._save_costs()
        return new_estimate

    def get_function_config(self, function_id: str) -> Dict[str, Any]:
        """Retrieves the configuration of a serverless function."""
        config = self.function_configurations.get(function_id)
        if not config: raise ValueError(f"Function '{function_id}' not configured.")
        return config

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "configure_function":
            function_id = kwargs.get('function_id')
            name = kwargs.get('name')
            runtime = kwargs.get('runtime')
            memory_mb = kwargs.get('memory_mb')
            timeout_seconds = kwargs.get('timeout_seconds')
            if not all([function_id, name, runtime, memory_mb is not None, timeout_seconds is not None]):
                raise ValueError("Missing 'function_id', 'name', 'runtime', 'memory_mb', or 'timeout_seconds' for 'configure_function' operation.")
            return self.configure_function(function_id, name, runtime, memory_mb, timeout_seconds)
        elif operation == "estimate_cost":
            function_id = kwargs.get('function_id')
            num_invocations_per_month = kwargs.get('num_invocations_per_month')
            if not all([function_id, num_invocations_per_month is not None]):
                raise ValueError("Missing 'function_id' or 'num_invocations_per_month' for 'estimate_cost' operation.")
            return self.estimate_cost(function_id, num_invocations_per_month)
        elif operation == "get_function_config":
            function_id = kwargs.get('function_id')
            if not function_id:
                raise ValueError("Missing 'function_id' for 'get_function_config' operation.")
            return self.get_function_config(function_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ServerlessConfigCostEstimatorTool functionality...")
    temp_dir = "temp_serverless_cost_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    cost_estimator = ServerlessConfigCostEstimatorTool(data_dir=temp_dir)
    
    try:
        # 1. Configure a serverless function
        print("\n--- Configuring function 'image_resizer' ---")
        cost_estimator.execute(operation="configure_function", function_id="image_resizer", name="Image Resizer", runtime="python", memory_mb=512, timeout_seconds=30)
        print("Function configured.")

        # 2. Estimate its cost
        print("\n--- Estimating cost for 'image_resizer' (1M invocations/month) ---")
        cost_estimate = cost_estimator.execute(operation="estimate_cost", function_id="image_resizer", num_invocations_per_month=1_000_000)
        print(json.dumps(cost_estimate, indent=2))

        # 3. Configure another function with higher memory
        print("\n--- Configuring function 'video_processor' ---")
        cost_estimator.execute(operation="configure_function", function_id="video_processor", name="Video Processor", runtime="nodejs", memory_mb=1024, timeout_seconds=60)
        print("Function configured.")

        # 4. Estimate its cost
        print("\n--- Estimating cost for 'video_processor' (500K invocations/month) ---")
        cost_estimate_video = cost_estimator.execute(operation="estimate_cost", function_id="video_processor", num_invocations_per_month=500_000)
        print(json.dumps(cost_estimate_video, indent=2))

        # 5. Get function configuration
        print("\n--- Getting configuration for 'image_resizer' ---")
        config = cost_estimator.execute(operation="get_function_config", function_id="image_resizer")
        print(json.dumps(config, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")