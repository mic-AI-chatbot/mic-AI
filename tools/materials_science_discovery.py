
import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MaterialsDiscoveryTool(BaseTool):
    """
    A tool to simulate materials science discovery using a genetic
    algorithm-inspired approach for discovery and optimization.
    """

    def __init__(self, tool_name: str = "MaterialsDiscovery", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "materials_data.json")
        self.data = self._load_data(self.data_file, default={"projects": {}})

    @property
    def description(self) -> str:
        return "Simulates materials discovery using fitness scoring and iterative optimization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_project", "run_discovery_simulation", "run_optimization_cycle"]},
                "project_id": {"type": "string"}, "name": {"type": "string"}, "discovery_goal": {"type": "string"},
                "target_properties": {"type": "object", "description": "e.g., {'strength_gpa': 1.5, 'density_kg_m3': 2000}"},
                "population_size": {"type": "integer", "default": 20},
                "material_to_optimize": {"type": "object", "description": "The full dictionary of the material to optimize."}
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

    def create_project(self, project_id: str, name: str, discovery_goal: str, target_properties: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a new materials discovery project."""
        if project_id in self.data["projects"]:
            raise ValueError(f"Project with ID '{project_id}' already exists.")
        
        new_project = {
            "project_id": project_id, "name": name, "discovery_goal": discovery_goal,
            "target_properties": target_properties, "created_at": datetime.now().isoformat()
        }
        self.data["projects"][project_id] = new_project
        self._save_data()
        return new_project

    def run_discovery_simulation(self, project_id: str, population_size: int = 20) -> List[Dict[str, Any]]:
        """Simulates a generation of material discovery and returns the top candidates."""
        project = self.data["projects"].get(project_id)
        if not project: raise ValueError(f"Project '{project_id}' not found.")
        
        target_props = project["target_properties"]
        candidates = []

        for i in range(population_size):
            # Simulate properties around a plausible range
            props = {
                "strength_gpa": round(random.uniform(0.5, 5.0), 2),  # nosec B311
                "density_kg_m3": round(random.uniform(1500, 8000)),  # nosec B311
                "conductivity_pct_iacs": round(random.uniform(10, 110))  # nosec B311
            }
            
            # Calculate fitness score (lower is better)
            fitness = 0
            for key, target_val in target_props.items():
                if key in props:
                    # Normalized difference
                    fitness += abs(props[key] - target_val) / target_val
            
            candidates.append({"material_id": f"CANDIDATE-{i}", "properties": props, "fitness_score": fitness})

        # Return top 3 candidates
        sorted_candidates = sorted(candidates, key=lambda x: x['fitness_score'])
        return sorted_candidates[:3]

    def run_optimization_cycle(self, material_to_optimize: Dict[str, Any], optimization_goal: Dict[str, str]) -> Dict[str, Any]:
        """'Mutates' a material's properties to simulate an optimization cycle."""
        goal_prop, direction = list(optimization_goal.items())[0]
        
        optimized_props = material_to_optimize["properties"].copy()
        if goal_prop not in optimized_props:
            raise ValueError(f"Property '{goal_prop}' not found in material.")

        # Mutate the target property
        change_factor = random.uniform(1.05, 1.20) # 5-20% improvement  # nosec B311
        if direction == "maximize":
            optimized_props[goal_prop] *= change_factor
        elif direction == "minimize":
            optimized_props[goal_prop] /= change_factor
        
        # Simulate a trade-off (e.g., increasing strength might slightly increase density)
        if goal_prop == "strength_gpa" and "density_kg_m3" in optimized_props:
            optimized_props["density_kg_m3"] *= random.uniform(1.0, 1.05)  # nosec B311

        return {"original_material": material_to_optimize, "optimized_material": {"properties": optimized_props}}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_project": self.create_project,
            "run_discovery_simulation": self.run_discovery_simulation,
            "run_optimization_cycle": self.run_optimization_cycle
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MaterialsDiscoveryTool functionality...")
    import shutil
    temp_dir = "temp_materials_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    discovery_tool = MaterialsDiscoveryTool(data_dir=temp_dir)
    
    try:
        # 1. Create a project with numerical targets
        print("\n--- Creating a discovery project ---")
        targets = {"strength_gpa": 4.0, "density_kg_m3": 2500}
        discovery_tool.execute(
            operation="create_project", project_id="high_strength_alloy", name="High-Strength Low-Density Alloy",
            discovery_goal="Find a material for aerospace applications.", target_properties=targets
        )
        print("Project 'high_strength_alloy' created.")

        # 2. Run a discovery simulation to find candidates
        print("\n--- Running discovery simulation ---")
        top_candidates = discovery_tool.execute(operation="run_discovery_simulation", project_id="high_strength_alloy")
        print("Top 3 candidates from simulation:")
        print(json.dumps(top_candidates, indent=2))

        # 3. Take the best candidate and try to optimize it
        if top_candidates:
            best_candidate = top_candidates[0]
            print(f"\n--- Optimizing best candidate ({best_candidate['material_id']}) to maximize strength ---")
            optimization_result = discovery_tool.execute(
                operation="run_optimization_cycle",
                material_to_optimize=best_candidate,
                optimization_goal={"strength_gpa": "maximize"}
            )
            print("Optimization Result:")
            print(json.dumps(optimization_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
