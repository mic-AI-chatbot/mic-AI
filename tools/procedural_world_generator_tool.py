
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProceduralWorldGeneratorTool(BaseTool):
    """
    A tool that generates simulated procedural worlds based on parameters
    like world size, biome type, and resource density.
    """

    def __init__(self, tool_name: str = "ProceduralWorldGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.worlds_file = os.path.join(self.data_dir, "generated_worlds.json")
        # Worlds structure: {world_id: {world_size: ..., biome_type: ..., map: [], features: {}}}
        self.generated_worlds: Dict[str, Dict[str, Any]] = self._load_data(self.worlds_file, default={})

    @property
    def description(self) -> str:
        return "Generates simulated procedural worlds based on size, biome, and resource density."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["generate_world", "get_world_details"]},
                "world_id": {"type": "string"},
                "world_size": {"type": "string", "enum": ["small", "medium", "large"]},
                "biome_type": {"type": "string", "enum": ["forest", "desert", "tundra", "ocean"]},
                "resource_density": {"type": "string", "enum": ["sparse", "normal", "abundant"]}
            },
            "required": ["operation", "world_id"]
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
        with open(self.worlds_file, 'w') as f: json.dump(self.generated_worlds, f, indent=2)

    def generate_world(self, world_id: str, world_size: str, biome_type: str, resource_density: str) -> Dict[str, Any]:
        """Generates a simulated procedural world map with features."""
        if world_id in self.generated_worlds: raise ValueError(f"World '{world_id}' already exists.")
        
        grid_dimensions = {"small": 10, "medium": 20, "large": 30}[world_size]
        world_map = [['.' for _ in range(grid_dimensions)] for _ in range(grid_dimensions)]
        
        features = {"terrain": {}, "resources": {}, "points_of_interest": []}

        # Biome generation
        terrain_char = {"forest": 'T', "desert": 'S', "tundra": 'I', "ocean": 'W'}[biome_type]
        for r in range(grid_dimensions):
            for c in range(grid_dimensions):
                world_map[r][c] = terrain_char
        features["terrain"] = {"type": biome_type, "character": terrain_char}

        # Resource placement
        resource_count = {"sparse": 5, "normal": 15, "abundant": 30}[resource_density]
        resource_types = {"forest": ["wood", "berries"], "desert": ["sand", "oil"], "tundra": ["ice", "minerals"], "ocean": ["fish", "salt"]}
        
        for _ in range(resource_count):
            rx, ry = random.randint(0, grid_dimensions - 1), random.randint(0, grid_dimensions - 1)  # nosec B311
            resource = random.choice(resource_types[biome_type])  # nosec B311
            world_map[ry][rx] = resource[0].upper() # Use first letter as symbol
            features["resources"].setdefault(resource, []).append({"x": rx, "y": ry})

        # Points of interest
        num_poi = random.randint(1, 3)  # nosec B311
        poi_types = ["ancient ruins", "abandoned mine", "mysterious cave", "trading post"]
        for _ in range(num_poi):
            px, py = random.randint(0, grid_dimensions - 1), random.randint(0, grid_dimensions - 1)  # nosec B311
            poi_type = random.choice(poi_types)  # nosec B311
            world_map[py][px] = '!'
            features["points_of_interest"].append({"type": poi_type, "x": px, "y": py})

        new_world = {
            "id": world_id, "world_size": world_size, "biome_type": biome_type,
            "resource_density": resource_density, "grid_dimensions": grid_dimensions,
            "map": ["".join(row) for row in world_map], "features": features,
            "generated_at": datetime.now().isoformat()
        }
        self.generated_worlds[world_id] = new_world
        self._save_data()
        return new_world

    def get_world_details(self, world_id: str) -> Dict[str, Any]:
        """Retrieves details of a previously generated world."""
        world = self.generated_worlds.get(world_id)
        if not world: raise ValueError(f"World '{world_id}' not found.")
        return world

    def execute(self, operation: str, world_id: str, **kwargs: Any) -> Any:
        if operation == "generate_world":
            return self.generate_world(world_id, kwargs['world_size'], kwargs['biome_type'], kwargs['resource_density'])
        elif operation == "get_world_details":
            return self.get_world_details(world_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ProceduralWorldGeneratorTool functionality...")
    temp_dir = "temp_world_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    world_generator = ProceduralWorldGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Generate a small forest world with normal resources
        print("\n--- Generating a small forest world 'forest_realm_01' ---")
        world1 = world_generator.execute(operation="generate_world", world_id="forest_realm_01", world_size="small", biome_type="forest", resource_density="normal")
        print(json.dumps(world1, indent=2))

        # 2. Generate a large desert world with abundant resources
        print("\n--- Generating a large desert world 'sandy_expanse_01' ---")
        world2 = world_generator.execute(operation="generate_world", world_id="sandy_expanse_01", world_size="large", biome_type="desert", resource_density="abundant")
        print(json.dumps(world2, indent=2))

        # 3. Get details of a generated world
        print("\n--- Getting details for 'forest_realm_01' ---")
        details = world_generator.execute(operation="get_world_details", world_id="forest_realm_01")
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
