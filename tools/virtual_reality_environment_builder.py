import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated VR environments
vr_environments: Dict[str, Dict[str, Any]] = {}

class VirtualRealityEnvironmentBuilderTool(BaseTool):
    """
    A tool to simulate building and managing virtual reality (VR) environments.
    """
    def __init__(self, tool_name: str = "virtual_reality_environment_builder_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates building VR environments: create, add assets, and list environments."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_env', 'add_asset', 'get_env_details', 'list_envs'."
                },
                "env_name": {"type": "string", "description": "The unique name of the VR environment."},
                "theme": {
                    "type": "string", 
                    "description": "The theme for a new environment (e.g., 'sci-fi', 'fantasy', 'urban')."
                },
                "asset_name": {"type": "string", "description": "The name of the asset to add (e.g., 'spaceship', 'dragon')."},
                "asset_type": {"type": "string", "description": "The type of asset.", "default": "3d_model"}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            env_name = kwargs.get("env_name")

            if action in ['add_asset', 'get_env_details'] and not env_name:
                raise ValueError(f"'env_name' is required for the '{action}' action.")

            actions = {
                "create_env": self._create_environment,
                "add_asset": self._add_asset,
                "get_env_details": self._get_environment_details,
                "list_envs": self._list_environments,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VREnvironmentBuilderTool: {e}")
            return {"error": str(e)}

    def _create_environment(self, env_name: str, theme: str, **kwargs) -> Dict:
        if not env_name or not theme:
            raise ValueError("'env_name' and 'theme' are required to create an environment.")
        
        if env_name in vr_environments:
            raise ValueError(f"An environment with the name '{env_name}' already exists.")

        logger.info(f"Creating VR environment '{env_name}'.")
        
        new_env = {
            "name": env_name,
            "theme": theme,
            "status": "created",
            "assets": [],
            "skybox": f"{theme}_sky.jpg"
        }
        vr_environments[env_name] = new_env
        
        return {"message": "VR environment created successfully.", "details": new_env}

    def _add_asset(self, env_name: str, asset_name: str, asset_type: str = "3d_model", **kwargs) -> Dict:
        if not asset_name:
            raise ValueError("'asset_name' is required to add an asset.")
            
        if env_name not in vr_environments:
            raise ValueError(f"Environment '{env_name}' not found.")
        
        env = vr_environments[env_name]
        
        new_asset = {
            "asset_name": asset_name,
            "asset_type": asset_type,
            "position": {
                "x": round(random.uniform(-100, 100), 2),  # nosec B311
                "y": round(random.uniform(0, 50), 2),  # nosec B311
                "z": round(random.uniform(-100, 100), 2)  # nosec B311
            }
        }
        env["assets"].append(new_asset)
        
        logger.info(f"Added asset '{asset_name}' to environment '{env_name}'.")
        return {"message": "Asset added successfully.", "environment": env_name, "asset": new_asset}

    def _get_environment_details(self, env_name: str, **kwargs) -> Dict:
        if env_name not in vr_environments:
            raise ValueError(f"Environment '{env_name}' not found.")
        return {"environment_details": vr_environments[env_name]}

    def _list_environments(self, **kwargs) -> Dict:
        if not vr_environments:
            return {"message": "No VR environments have been created yet."}
        
        summary = {
            name: {
                "theme": details["theme"],
                "asset_count": len(details["assets"])
            } for name, details in vr_environments.items()
        }
        return {"environments": summary}