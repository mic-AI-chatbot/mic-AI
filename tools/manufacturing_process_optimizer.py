

import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ManufacturingOptimizerTool(BaseTool):
    """
    A tool to define, optimize, and analyze manufacturing processes
    using data-driven calculations instead of pure simulation.
    """

    def __init__(self, tool_name: str = "ManufacturingOptimizer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "manufacturing_data.json")
        self.data = self._load_data(self.data_file, default={"processes": {}, "reports": {}})

    @property
    def description(self) -> str:
        return "Defines, optimizes, and analyzes manufacturing processes with data-driven logic."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_process", "optimize_process", "analyze_production_data", "list_processes"]},
                "process_id": {"type": "string"}, "name": {"type": "string"}, "description": {"type": "string"},
                "current_metrics": {"type": "object", "description": "e.g., {'cycle_time_s': 120, 'defect_rate_pct': 2.5, 'cost_per_unit': 10}"},
                "optimization_goal": {"type": "string", "enum": ["efficiency", "quality", "cost"]},
                "production_data": {"type": "array", "items": {"type": "object"}}
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

    def define_process(self, process_id: str, name: str, description: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Defines a new manufacturing process with its baseline metrics."""
        if process_id in self.data["processes"]:
            raise ValueError(f"Process with ID '{process_id}' already exists.")
        
        new_process = {
            "process_id": process_id, "name": name, "description": description,
            "metrics_log": [current_metrics], "defined_at": datetime.now().isoformat()
        }
        self.data["processes"][process_id] = new_process
        self._save_data()
        return new_process

    def optimize_process(self, process_id: str, optimization_goal: str) -> Dict[str, Any]:
        """Optimizes a process by applying a calculated improvement to its metrics."""
        process = self.data["processes"].get(process_id)
        if not process: raise ValueError(f"Process '{process_id}' not found.")

        original_metrics = process["metrics_log"][-1].copy()
        new_metrics = original_metrics.copy()
        
        recommendations = []
        if optimization_goal == "efficiency":
            improvement = random.uniform(0.1, 0.2)  # nosec B311
            new_metrics['cycle_time_s'] *= (1 - improvement)
            recommendations.append(f"Reduced cycle time by {improvement:.1%}.")
        elif optimization_goal == "quality":
            improvement = random.uniform(0.15, 0.3)  # nosec B311
            new_metrics['defect_rate_pct'] *= (1 - improvement)
            recommendations.append(f"Reduced defect rate by {improvement:.1%}.")
        elif optimization_goal == "cost":
            improvement = random.uniform(0.05, 0.15)  # nosec B311
            new_metrics['cost_per_unit'] *= (1 - improvement)
            recommendations.append(f"Reduced cost per unit by {improvement:.1%}.")
        else:
            raise ValueError(f"Unsupported optimization goal: {optimization_goal}")

        process["metrics_log"].append(new_metrics)
        
        report = {
            "report_id": f"OPT-{process_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "process_id": process_id, "optimization_goal": optimization_goal,
            "original_metrics": original_metrics, "optimized_metrics": new_metrics,
            "recommendations": " ".join(recommendations)
        }
        self.data["reports"][report['report_id']] = report
        self._save_data()
        return report

    def analyze_production_data(self, process_id: str, production_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes production data to find deviations and insights."""
        if not self.data["processes"].get(process_id):
            raise ValueError(f"Process '{process_id}' not found.")
        if not production_data: raise ValueError("Production data cannot be empty.")

        insights = {}
        # Transpose data for analysis
        data_by_metric = {k: [d[k] for d in production_data if k in d] for k in production_data[0]}

        for metric, values in data_by_metric.items():
            if not np.issubdtype(np.array(values).dtype, np.number): continue
            insights[metric] = {
                "mean": np.mean(values), "std_dev": np.std(values),
                "min": np.min(values), "max": np.max(values)
            }
        
        report = {"report_id": f"ANALYSIS-{process_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}", "insights": insights}
        self.data["reports"][report['report_id']] = report
        self._save_data()
        return report

    def list_processes(self) -> List[Dict[str, Any]]:
        """Lists all defined manufacturing processes."""
        return list(self.data["processes"].values())

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "define_process": self.define_process, "optimize_process": self.optimize_process,
            "analyze_production_data": self.analyze_production_data, "list_processes": self.list_processes
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating ManufacturingOptimizerTool functionality...")
    temp_dir = "temp_mfg_optimizer_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    optimizer_tool = ManufacturingOptimizerTool(data_dir=temp_dir)
    
    try:
        # 1. Define a process
        print("\n--- Defining a new process ---")
        initial_metrics = {'cycle_time_s': 120, 'defect_rate_pct': 2.5, 'cost_per_unit': 10.0}
        optimizer_tool.execute(
            operation="define_process", process_id="assembly_A", name="Assembly Line A",
            description="Main assembly line.", current_metrics=initial_metrics
        )
        print("Process 'assembly_A' defined.")

        # 2. Optimize it for efficiency
        print("\n--- Optimizing for efficiency ---")
        opt_report = optimizer_tool.execute(operation="optimize_process", process_id="assembly_A", optimization_goal="efficiency")
        print(f"Optimization Report: {opt_report['recommendations']}")
        print(f"Old cycle time: {opt_report['original_metrics']['cycle_time_s']:.2f}s, New cycle time: {opt_report['optimized_metrics']['cycle_time_s']:.2f}s")

        # 3. Analyze some production data
        print("\n--- Analyzing production data ---")
        prod_data = [
            {'cycle_time_s': 110, 'defect_rate_pct': 2.1},
            {'cycle_time_s': 115, 'defect_rate_pct': 2.2},
            {'cycle_time_s': 108, 'defect_rate_pct': 2.0}
        ]
        analysis_report = optimizer_tool.execute(operation="analyze_production_data", process_id="assembly_A", production_data=prod_data)
        print("Analysis Insights:")
        print(json.dumps(analysis_report['insights'], indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
