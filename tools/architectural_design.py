import logging
import json
import random
import numpy as np
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class Building:
    """Represents a building design, including its properties and a grid-based floor plan."""
    def __init__(self, building_id: str, building_type: str, num_floors: int, area_sqm: int):
        self.building_id = building_id
        self.building_type = building_type
        self.num_floors = num_floors
        self.area_sqm = area_sqm
        self.floor_plan: np.ndarray = None
        self.rooms: List[str] = []

    def generate_floor_plan(self, grid_size: int = 20):
        """Generates a simple, randomized floor plan on a grid."""
        self.floor_plan = np.zeros((grid_size, grid_size), dtype=int)
        
        if self.building_type == "commercial":
            self.rooms = ["Lobby", "Office", "Office", "Conference Room", "Restroom", "Stairs/Elevator"]
        else: # residential
            self.rooms = ["Living Room", "Kitchen", "Bedroom", "Bedroom", "Bathroom", "Closet"]

        # Place rooms randomly on the grid
        for i, room in enumerate(self.rooms, 1):
            # Avoid placing rooms on top of each other (simple check)
            for _ in range(10): # Try 10 times to find an empty spot
                w, h = random.randint(3, 6), random.randint(3, 6)  # nosec B311
                x, y = random.randint(0, grid_size - w), random.randint(0, grid_size - h)  # nosec B311
                if np.all(self.floor_plan[x:x+w, y:y+h] == 0):
                    self.floor_plan[x:x+w, y:y+h] = i
                    break

    def to_dict(self) -> Dict[str, Any]:
        return {
            "building_id": self.building_id,
            "building_type": self.building_type,
            "num_floors": self.num_floors,
            "area_sqm": self.area_sqm,
            "rooms": self.rooms,
            "floor_plan_grid": self.floor_plan.tolist() if self.floor_plan is not None else None
        }

buildings: Dict[str, Building] = {}

class DesignBuildingTool(BaseTool):
    """Tool to design a building and generate a basic floor plan."""
    def __init__(self, tool_name="design_building"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Designs a new building with specified requirements and generates a randomized floor plan."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "building_id": {"type": "string", "description": "A unique identifier for the building design."},
                "building_type": {"type": "string", "description": "The type of building.", "enum": ["residential", "commercial"]},
                "num_floors": {"type": "integer", "description": "The number of floors."},
                "area_sqm": {"type": "integer", "description": "The total square meters."}
            },
            "required": ["building_id", "building_type", "num_floors", "area_sqm"]
        }

    def execute(self, building_id: str, building_type: str, num_floors: int, area_sqm: int, **kwargs: Any) -> str:
        if building_id in buildings:
            return json.dumps({"error": f"Building with ID '{building_id}' already exists."})
        
        building = Building(building_id, building_type, num_floors, area_sqm)
        building.generate_floor_plan()
        buildings[building_id] = building
        
        return json.dumps(building.to_dict(), indent=2)

class OptimizeBuildingLayoutTool(BaseTool):
    """Tool to simulate optimizing a building's layout by regenerating the floor plan."""
    def __init__(self, tool_name="optimize_building_layout"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates optimizing a building's layout by re-generating a new randomized floor plan."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"building_id": {"type": "string", "description": "The ID of the building to optimize."}},
            "required": ["building_id"]
        }

    def execute(self, building_id: str, **kwargs: Any) -> str:
        if building_id not in buildings:
            return json.dumps({"error": f"Building with ID '{building_id}' not found."})
        
        building = buildings[building_id]
        # This is a simple simulation of optimization: we just regenerate the floor plan
        building.generate_floor_plan()
        
        report = {
            "message": f"Layout for building '{building_id}' has been re-optimized.",
            "new_floor_plan_grid": building.floor_plan.tolist()
        }
        return json.dumps(report, indent=2)

class VisualizeFloorPlanTool(BaseTool):
    """Tool to generate a text-based visualization of a floor plan."""
    def __init__(self, tool_name="visualize_floor_plan"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a simple text-based visualization of a building's floor plan grid."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"building_id": {"type": "string", "description": "The ID of the building to visualize."}},
            "required": ["building_id"]
        }

    def execute(self, building_id: str, **kwargs: Any) -> str:
        if building_id not in buildings:
            return json.dumps({"error": f"Building with ID '{building_id}' not found."})
            
        building = buildings[building_id]
        if building.floor_plan is None:
            return json.dumps({"error": "Building has no floor plan to visualize."})

        # Create a simple text visualization
        vis = ""
        for row in building.floor_plan:
            vis_row = ""
            for cell in row:
                vis_row += f"[{cell if cell > 0 else ' '}]"
            vis += vis_row + "\n"
            
        legend = {i: room for i, room in enumerate(building.rooms, 1)}
        legend[0] = "Empty Space"
        
        report = {
            "visualization": vis,
            "legend": legend
        }
        return json.dumps(report, indent=2)