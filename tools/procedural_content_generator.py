import logging
import random
import json
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ProceduralContentGeneratorTool(BaseTool):
    """
    A tool that generates various types of content (e.g., game levels,
    texture descriptions, items) procedurally based on specified parameters.
    """
    def __init__(self, tool_name: str = "ProceduralContentGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates various types of content (levels, textures, items) procedurally based on content type and complexity."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "enum": ["level", "texture", "item"], "description": "The type of content to generate."},
                "complexity": {"type": "string", "enum": ["low", "medium", "high"], "default": "medium", "description": "The desired complexity of the generated content."}
            },
            "required": ["content_type"]
        }

    def execute(self, content_type: str, complexity: str = "medium", **kwargs: Any) -> Dict[str, Any]:
        """
        Generates procedural content based on the specified type and complexity.
        """
        if content_type == "level":
            return self._generate_level(complexity)
        elif content_type == "texture":
            return self._generate_texture(complexity)
        elif content_type == "item":
            return self._generate_item(complexity)
        else:
            raise ValueError(f"Unsupported content type: {content_type}. Choose from 'level', 'texture', 'item'.")

    def _generate_level(self, complexity: str) -> Dict[str, Any]:
        """Generates a simulated 2D grid-based game level."""
        grid_size = {"low": 5, "medium": 10, "high": 15}[complexity]
        num_obstacles = {"low": 5, "medium": 15, "high": 30}[complexity]
        num_enemies = {"low": 2, "medium": 5, "high": 10}[complexity]
        
        level_map = [['.' for _ in range(grid_size)] for _ in range(grid_size)]
        
        # Place player start
        start_x, start_y = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
        level_map[start_y][start_x] = 'P'
        
        # Place exit
        exit_x, exit_y = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
        while (exit_x, exit_y) == (start_x, start_y):
            exit_x, exit_y = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
        level_map[exit_y][exit_x] = 'E'

        # Place obstacles
        for _ in range(num_obstacles):
            ox, oy = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
            while level_map[oy][ox] != '.':
                ox, oy = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
            level_map[oy][ox] = '#'
        
        # Place enemies
        for _ in range(num_enemies):
            ex, ey = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
            while level_map[ey][ex] != '.':
                ex, ey = random.randint(0, grid_size - 1), random.randint(0, grid_size - 1)  # nosec B311
            level_map[ey][ex] = 'X'

        return {
            "content_type": "level",
            "complexity": complexity,
            "grid_size": grid_size,
            "num_obstacles": num_obstacles,
            "num_enemies": num_enemies,
            "level_map": ["".join(row) for row in level_map],
            "legend": {"P": "Player Start", "E": "Exit", "#": "Obstacle", "X": "Enemy", ".": "Empty Space"}
        }

    def _generate_texture(self, complexity: str) -> Dict[str, Any]:
        """Generates a textual description of a texture."""
        base_materials = ["stone", "wood", "metal", "fabric", "crystal"]
        surface_qualities = {"low": ["rough", "smooth"], "medium": ["gritty", "polished", "worn"], "high": ["intricate", "glowing", "weathered", "ornate"]}[complexity]
        colors = ["grey", "brown", "silver", "gold", "blue", "red", "green"]
        patterns = {"low": ["plain"], "medium": ["striped", "checkered"], "high": ["swirling", "geometric", "organic"]}[complexity]

        description = f"A {random.choice(surface_qualities)} texture of {random.choice(colors)} {random.choice(base_materials)} with a {random.choice(patterns)} pattern."  # nosec B311
        
        return {
            "content_type": "texture",
            "complexity": complexity,
            "description": description,
            "properties": {
                "base_material": random.choice(base_materials),  # nosec B311
                "surface_quality": random.choice(surface_qualities),  # nosec B311
                "color": random.choice(colors),  # nosec B311
                "pattern": random.choice(patterns)  # nosec B311
            }
        }

    def _generate_item(self, complexity: str) -> Dict[str, Any]:
        """Generates a description of an item."""
        item_types = ["sword", "shield", "potion", "ring", "armor", "scroll"]
        rarities = {"low": "common", "medium": "uncommon", "high": "legendary"}[complexity]
        
        item_type = random.choice(item_types)  # nosec B311
        
        stats = {}
        if item_type in ["sword", "armor", "shield"]:
            stats["attack"] = random.randint(5, 20) * {"low": 1, "medium": 2, "high": 4}[complexity]  # nosec B311
            stats["defense"] = random.randint(2, 10) * {"low": 1, "medium": 2, "high": 4}[complexity]  # nosec B311
        elif item_type == "potion":
            stats["effect"] = random.choice(["healing", "strength_boost", "invisibility"])  # nosec B311
            stats["duration_seconds"] = random.randint(30, 300)  # nosec B311
        
        name_prefix = {"low": "", "medium": "Enchanted ", "high": "Legendary "}[complexity]
        item_name = f"{name_prefix}{item_type.title()} of {random.choice(['Power', 'Wisdom', 'Swiftness', 'Protection'])}"  # nosec B311

        return {
            "content_type": "item",
            "complexity": complexity,
            "name": item_name,
            "type": item_type,
            "rarity": rarities,
            "stats": stats
        }

if __name__ == '__main__':
    print("Demonstrating ProceduralContentGeneratorTool functionality...")
    
    generator_tool = ProceduralContentGeneratorTool()
    
    try:
        # 1. Generate a low complexity game level
        print("\n--- Generating a low complexity game level ---")
        level_low = generator_tool.execute(content_type="level", complexity="low")
        print(json.dumps(level_low, indent=2))

        # 2. Generate a high complexity texture
        print("\n--- Generating a high complexity texture ---")
        texture_high = generator_tool.execute(content_type="texture", complexity="high")
        print(json.dumps(texture_high, indent=2))
        
        # 3. Generate a medium complexity item
        print("\n--- Generating a medium complexity item ---")
        item_medium = generator_tool.execute(content_type="item", complexity="medium")
        print(json.dumps(item_medium, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")