import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Union

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MetaverseAssetGeneratorTool(BaseTool):
    """
    A tool for procedurally generating descriptive JSON files for metaverse assets
    and simulating their deployment.
    """

    def __init__(self, tool_name: str = "MetaverseAssetGenerator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.assets_dir = os.path.join(self.data_dir, "metaverse_assets")
        self.catalog_file = os.path.join(self.data_dir, "asset_catalog.json")
        os.makedirs(self.assets_dir, exist_ok=True)
        self.catalog: Dict[str, Dict[str, Any]] = self._load_data(self.catalog_file, default={})

    @property
    def description(self) -> str:
        return "Procedurally generates JSON descriptions of metaverse assets and simulates their deployment."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_asset", "deploy_asset"]},
                "asset_id": {"type": "string"},
                "asset_type": {"type": "string", "enum": ["avatar", "building", "vehicle"]},
                "description": {"type": "string"},
                "metaverse_platform": {"type": "string", "default": "Decentraland"}
            },
            "required": ["operation", "asset_id"]
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
        with open(self.catalog_file, 'w') as f: json.dump(self.catalog, f, indent=2)

    def _generate_procedural_asset(self, asset_type: str, description: str) -> Dict:
        """Generates a dictionary of properties based on the asset type."""
        if asset_type == "avatar":
            return {
                "height_m": round(random.uniform(1.5, 2.0), 2),  # nosec B311
                "clothing": random.choice(["cyberpunk jacket", "space suit", "casual wear"]),  # nosec B311
                "accessories": random.sample(["goggles", "jetpack", "glowing shoes", "holographic watch"], k=2)  # nosec B311
            }
        if asset_type == "building":
            return {
                "style": random.choice(["modern", "gothic", "neo-futurist"]),  # nosec B311
                "dimensions_m": {"width": random.randint(10, 50), "depth": random.randint(10, 50), "height": random.randint(10, 200)},  # nosec B311
                "num_floors": random.randint(1, 20),  # nosec B311
                "primary_material": random.choice(["glass", "steel", "glowing energy"])  # nosec B311
            }
        if asset_type == "vehicle":
            return {
                "vehicle_type": random.choice(["car", "spaceship", "hoverbike"]),  # nosec B311
                "color": random.choice(["chrome", "matte black", "iridescent"]),  # nosec B311
                "max_speed_kph": random.randint(100, 1000)  # nosec B311
            }
        return {"description": description}

    def create_asset(self, asset_id: str, asset_type: str, description: str) -> Dict:
        """Procedurally generates a JSON asset file."""
        if asset_id in self.catalog:
            raise ValueError(f"Asset with ID '{asset_id}' already exists.")

        procedural_properties = self._generate_procedural_asset(asset_type, description)
        
        asset_data = {
            "asset_id": asset_id, "asset_type": asset_type, "description": description,
            "createdAt": datetime.now().isoformat(), "properties": procedural_properties
        }

        asset_path = os.path.join(self.assets_dir, f"{asset_id}.json")
        with open(asset_path, 'w') as f:
            json.dump(asset_data, f, indent=2)
            
        self.catalog[asset_id] = {"path": asset_path, "type": asset_type}
        self._save_data()
        
        return {"status": "success", "asset_id": asset_id, "asset_file_path": asset_path}

    def deploy_asset(self, asset_id: str, metaverse_platform: str) -> Dict:
        """Simulates deploying an asset to a metaverse platform."""
        if asset_id not in self.catalog:
            raise ValueError(f"Asset '{asset_id}' not found in catalog. Please create it first.")
        
        coords = (random.randint(-100, 100), random.randint(-100, 100))  # nosec B311
        
        return {
            "status": "success",
            "message": f"Asset '{asset_id}' deployed to {metaverse_platform} at coordinates {coords}."
        }

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {"create_asset": self.create_asset, "deploy_asset": self.deploy_asset}
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MetaverseAssetGeneratorTool functionality...")
    temp_dir = "temp_metaverse_assets"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    asset_generator = MetaverseAssetGeneratorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a 'building' asset
        print("\n--- Creating a 'building' asset ---")
        create_result = asset_generator.execute(
            operation="create_asset", asset_id="cyber_tower_01", asset_type="building",
            description="A tall skyscraper for the city center."
        )
        print(f"Asset created. File at: {create_result['asset_file_path']}")

        # 2. Show the content of the generated asset file
        with open(create_result['asset_file_path'], 'r') as f:
            print("\n--- Generated Asset File Content ---")
            print(f.read())

        # 3. "Deploy" the asset
        print("\n--- Deploying the asset ---")
        deploy_result = asset_generator.execute(
            operation="deploy_asset", asset_id="cyber_tower_01", metaverse_platform="Somnium Space"
        )
        print(deploy_result['message'])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")