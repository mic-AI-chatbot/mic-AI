
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizedMetaverseBuilderTool(BaseTool):
    """
    A tool for simulating the creation and management of personalized virtual
    metaverse spaces, including adding assets and retrieving space details.
    """

    def __init__(self, tool_name: str = "MetaverseBuilder", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.spaces_file = os.path.join(self.data_dir, "metaverse_spaces.json")
        # Metaverse spaces structure: {space_id: {theme: ..., size: ..., assets: []}}
        self.metaverse_spaces: Dict[str, Dict[str, Any]] = self._load_data(self.spaces_file, default={})
        self.available_assets = ["tree", "bench", "statue", "fountain", "building", "car", "avatar_spawn_point"]

    @property
    def description(self) -> str:
        return "Simulates creating and managing personalized virtual metaverse spaces, adding assets, and getting details."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_virtual_space", "add_virtual_asset", "get_space_details"]},
                "space_id": {"type": "string"},
                "theme": {"type": "string", "enum": ["fantasy", "sci-fi", "city", "nature"]},
                "size": {"type": "string", "enum": ["small", "medium", "large"], "default": "medium"},
                "asset_name": {"type": "string", "enum": ["tree", "bench", "statue", "fountain", "building", "car", "avatar_spawn_point"]},
                "position": {"type": "array", "items": {"type": "number"}, "minItems": 3, "maxItems": 3, "description": "[x, y, z] coordinates."}
            },
            "required": ["operation", "space_id"]
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
        with open(self.spaces_file, 'w') as f: json.dump(self.metaverse_spaces, f, indent=2)

    def create_virtual_space(self, space_id: str, theme: str, size: str = "medium") -> Dict[str, Any]:
        """Creates a new virtual space with a given theme and size."""
        if space_id in self.metaverse_spaces: raise ValueError(f"Virtual space '{space_id}' already exists.")
        
        new_space = {
            "id": space_id, "theme": theme, "size": size, "assets": [],
            "created_at": datetime.now().isoformat()
        }
        self.metaverse_spaces[space_id] = new_space
        self._save_data()
        return new_space

    def add_virtual_asset(self, space_id: str, asset_name: str, position: Optional[List[float]] = None) -> Dict[str, Any]:
        """Adds a virtual asset to a created space."""
        space = self.metaverse_spaces.get(space_id)
        if not space: raise ValueError(f"Virtual space '{space_id}' not found. Create it first.")
        if asset_name not in self.available_assets: raise ValueError(f"Asset '{asset_name}' not available. Available assets: {', '.join(self.available_assets)}.")
        
        asset_data = {"name": asset_name}
        if position: asset_data["position"] = position
        else: asset_data["position"] = [round(random.uniform(-100, 100), 2), round(random.uniform(0, 50), 2), round(random.uniform(-100, 100), 2)]  # nosec B311
        
        space["assets"].append(asset_data)
        self._save_data()
        return {"status": "success", "message": f"Asset '{asset_name}' added to space '{space_id}'."}

    def get_space_details(self, space_id: str) -> Dict[str, Any]:
        """Provides details about a created virtual space."""
        space = self.metaverse_spaces.get(space_id)
        if not space: raise ValueError(f"Virtual space '{space_id}' not found.")
        return space

    def execute(self, operation: str, space_id: str, **kwargs: Any) -> Any:
        if operation == "create_virtual_space":
            theme = kwargs.get('theme')
            if not theme:
                raise ValueError("Missing 'theme' for 'create_virtual_space' operation.")
            return self.create_virtual_space(space_id, theme, kwargs.get('size', 'medium'))
        elif operation == "add_virtual_asset":
            asset_name = kwargs.get('asset_name')
            if not asset_name:
                raise ValueError("Missing 'asset_name' for 'add_virtual_asset' operation.")
            return self.add_virtual_asset(space_id, asset_name, kwargs.get('position'))
        elif operation == "get_space_details":
            return self.get_space_details(space_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizedMetaverseBuilderTool functionality...")
    temp_dir = "temp_metaverse_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    metaverse_builder = PersonalizedMetaverseBuilderTool(data_dir=temp_dir)
    
    try:
        # 1. Create a virtual space
        print("\n--- Creating virtual space 'fantasy_forest_01' ---")
        metaverse_builder.execute(operation="create_virtual_space", space_id="fantasy_forest_01", theme="fantasy", size="large")
        print("Space created.")

        # 2. Add some assets
        print("\n--- Adding assets to 'fantasy_forest_01' ---")
        metaverse_builder.execute(operation="add_virtual_asset", space_id="fantasy_forest_01", asset_name="tree", position=[10.0, 0.0, 5.0])
        metaverse_builder.execute(operation="add_virtual_asset", space_id="fantasy_forest_01", asset_name="fountain")
        metaverse_builder.execute(operation="add_virtual_asset", space_id="fantasy_forest_01", asset_name="avatar_spawn_point", position=[0.0, 0.0, 0.0])
        print("Assets added.")

        # 3. Get space details
        print("\n--- Getting details for 'fantasy_forest_01' ---")
        space_details = metaverse_builder.execute(operation="get_space_details", space_id="fantasy_forest_01")
        print(json.dumps(space_details, indent=2))

        # 4. Create another space
        print("\n--- Creating virtual space 'cyberpunk_city_01' ---")
        metaverse_builder.execute(operation="create_virtual_space", space_id="cyberpunk_city_01", theme="sci-fi", size="medium")
        print("Space created.")

        # 5. Add assets to the new space
        print("\n--- Adding assets to 'cyberpunk_city_01' ---")
        metaverse_builder.execute(operation="add_virtual_asset", space_id="cyberpunk_city_01", asset_name="building")
        metaverse_builder.execute(operation="add_virtual_asset", space_id="cyberpunk_city_01", asset_name="car")
        print("Assets added.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
