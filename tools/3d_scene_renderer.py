import logging
from typing import List, Dict, Any
from tools.base_tool import BaseTool
import matplotlib.pyplot as plt
import numpy as np
import os

logger = logging.getLogger(__name__)

# In-memory storage for simulated scenes
# This dictionary will hold the state of various scenes being worked on.
scenes: Dict[str, List[Dict[str, Any]]] = {}

class Create3DSceneTool(BaseTool):
    """Tool to create a new, empty 3D scene."""
    def __init__(self, tool_name: str = "create_3d_scene", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Creates a new, empty 3D scene with a unique ID that other tools can use to modify it."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_id": {
                    "type": "string",
                    "description": "The unique identifier for the new scene to be created."
                }
            },
            "required": ["scene_id"]
        }

    def execute(self, scene_id: str, **kwargs: Any) -> str:
        """Creates a new 3D scene."""
        if scene_id in scenes:
            return f"Error: Scene with ID '{scene_id}' already exists."
        scenes[scene_id] = []
        logger.info(f"Created new 3D scene with ID: {scene_id}")
        return f"Successfully created a new empty 3D scene with ID '{scene_id}'."

class AddObjectTo3DSceneTool(BaseTool):
    """Tool to add an object to a 3D scene."""
    def __init__(self, tool_name: str = "add_object_to_3d_scene", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Adds an object to a specified 3D scene."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_id": {
                    "type": "string",
                    "description": "The ID of the scene to add the object to."
                },
                "object_type": {
                    "type": "string",
                    "description": "The type of object to add (e.g., 'cube', 'sphere', 'pyramid')."
                },
                "position": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "z": {"type": "number"}
                    },
                    "required": ["x", "y", "z"],
                    "description": "The position of the object in 3D space."
                },
                "scale": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number"},
                        "y": {"type": "number"},
                        "z": {"type": "number"}
                    },
                    "required": ["x", "y", "z"],
                    "description": "The scale of the object."
                },
                "color": {
                    "type": "string",
                    "description": "The color of the object (e.g., 'red', '#FF0000')."
                }
            },
            "required": ["scene_id", "object_type", "position", "scale", "color"]
        }

    def execute(self, scene_id: str, object_type: str, position: Dict[str, float], scale: Dict[str, float], color: str, **kwargs: Any) -> str:
        """Adds an object to a 3D scene."""
        if scene_id not in scenes:
            return f"Error: Scene with ID '{scene_id}' not found."
        
        new_object = {
            "type": object_type,
            "position": position,
            "scale": scale,
            "color": color
        }
        scenes[scene_id].append(new_object)
        logger.info(f"Added object to scene '{scene_id}': {new_object}")
        return f"Successfully added a {object_type} to scene '{scene_id}'."

class Render3DSceneTool(BaseTool):
    """Tool to render a 3D scene as a 2D image."""
    def __init__(self, tool_name: str = "render_3d_scene", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Renders a specified 3D scene as a 2D image and returns the path to the image."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_id": {
                    "type": "string",
                    "description": "The ID of the scene to render."
                },
                "output_path": {
                    "type": "string",
                    "description": "The path to save the rendered image to. Should be a .png file."
                }
            },
            "required": ["scene_id", "output_path"]
        }

    def execute(self, scene_id: str, output_path: str, **kwargs: Any) -> str:
        """Renders a 3D scene as a 2D image."""
        if scene_id not in scenes:
            return f"Error: Scene with ID '{scene_id}' not found."

        scene_objects = scenes[scene_id]
        if not scene_objects:
            return f"Scene '{scene_id}' is empty."

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        for obj in scene_objects:
            pos = obj['position']
            scale = obj['scale']
            color = obj['color']
            obj_type = obj['type']

            # Simple representation: a single point for each object
            ax.scatter(pos['x'], pos['y'], pos['z'], c=color, marker='o', s=np.mean(list(scale.values()))*50, label=obj_type)

        ax.set_xlabel('X Axis')
        ax.set_ylabel('Y Axis')
        ax.set_zlabel('Z Axis')
        ax.set_title(f'Render of Scene: {scene_id}')
        
        # Handling legend for multiple objects of the same type
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())

        try:
            # Ensure the output directory exists
            if os.path.dirname(output_path):
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close(fig)
            logger.info(f"Rendered scene '{scene_id}' to {output_path}")
            return f"Successfully rendered scene '{scene_id}' to {output_path}"
        except Exception as e:
            logger.error(f"Failed to save rendered scene: {e}")
            return f"Error: Failed to save rendered scene to {output_path}. Reason: {e}"
