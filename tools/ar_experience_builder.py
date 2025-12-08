import logging
import json
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ARScene:
    """Represents a single AR scene with its objects and properties."""
    def __init__(self, scene_name: str, target_platform: str):
        self.scene_name = scene_name
        self.target_platform = target_platform
        self.objects: List[Dict[str, Any]] = []
        self.lighting = {"type": "ambient", "intensity": 0.8}

    def add_object(self, object_id: str, model_path: str, position: List[float], rotation: List[float], scale: List[float]):
        self.objects.append({
            "object_id": object_id,
            "model_path": model_path,
            "position": position,
            "rotation": rotation,
            "scale": scale
        })

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_name": self.scene_name,
            "target_platform": self.target_platform,
            "lighting": self.lighting,
            "objects": self.objects
        }

class SceneManager:
    """Manages all created AR scenes."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SceneManager, cls).__new__(cls)
            cls._instance.scenes: Dict[str, ARScene] = {}
        return cls._instance

    def create_scene(self, scene_name: str, target_platform: str) -> bool:
        if scene_name in self.scenes:
            return False
        self.scenes[scene_name] = ARScene(scene_name, target_platform)
        return True

    def get_scene(self, scene_name: str) -> ARScene:
        return self.scenes.get(scene_name)

scene_manager = SceneManager()

class CreateARSceneTool(BaseTool):
    """Tool to create a new, empty AR scene."""
    def __init__(self, tool_name="create_ar_scene"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new, empty Augmented Reality (AR) scene with a specified name and target platform."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_name": {"type": "string", "description": "A unique name for the new AR scene."},
                "target_platform": {"type": "string", "description": "The target platform.", "enum": ["ARKit", "ARCore", "WebXR"]}
            },
            "required": ["scene_name", "target_platform"]
        }

    def execute(self, scene_name: str, target_platform: str, **kwargs: Any) -> str:
        if scene_manager.create_scene(scene_name, target_platform):
            report = {"message": f"AR scene '{scene_name}' created successfully for platform '{target_platform}'."}
        else:
            report = {"error": f"An AR scene with the name '{scene_name}' already exists."}
        return json.dumps(report, indent=2)

class AddARObjectTool(BaseTool):
    """Tool to add a 3D object to an AR scene."""
    def __init__(self, tool_name="add_ar_object"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a 3D object to an existing AR scene with a specified position, rotation, and scale."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_name": {"type": "string", "description": "The name of the scene to add the object to."},
                "object_id": {"type": "string", "description": "A unique ID for the new object."},
                "model_path": {"type": "string", "description": "The path to the 3D model file (e.g., 'models/chair.gltf')."},
                "position": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] position of the object."},
                "rotation": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] Euler rotation in degrees.", "default": [0, 0, 0]},
                "scale": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] scale of the object.", "default": [1, 1, 1]}
            },
            "required": ["scene_name", "object_id", "model_path", "position"]
        }

    def execute(self, scene_name: str, object_id: str, model_path: str, position: List[float], rotation: List[float] = [0,0,0], scale: List[float] = [1,1,1], **kwargs: Any) -> str:
        scene = scene_manager.get_scene(scene_name)
        if not scene:
            return json.dumps({"error": f"AR scene '{scene_name}' not found."})
        
        scene.add_object(object_id, model_path, position, rotation, scale)
        report = {"message": f"Object '{object_id}' added to AR scene '{scene_name}'."}
        return json.dumps(report, indent=2)

class ExportSceneToGLTFJsonTool(BaseTool):
    """Tool to export an AR scene to a simplified glTF-like JSON format."""
    def __init__(self, tool_name="export_scene_to_gltf_json"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Exports an AR scene's structure to a simplified, glTF-like JSON format, which is useful for understanding the scene's composition."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"scene_name": {"type": "string", "description": "The name of the scene to export."}},
            "required": ["scene_name"]
        }

    def execute(self, scene_name: str, **kwargs: Any) -> str:
        scene = scene_manager.get_scene(scene_name)
        if not scene:
            return json.dumps({"error": f"AR scene '{scene_name}' not found."})

        # This is a simplified representation and not a valid glTF file, but it demonstrates the structure.
        gltf_like_json = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(scene.objects)))}],
            "nodes": [
                {
                    "mesh": i,
                    "translation": obj["position"],
                    "rotation": obj["rotation"], # In a real glTF, this would be a quaternion
                    "scale": obj["scale"]
                } for i, obj in enumerate(scene.objects)
            ],
            "meshes": [
                {"primitives": [{"attributes": {"POSITION": i}}]} for i in range(len(scene.objects))
            ],
            "buffers": [
                {"uri": obj["model_path"]} for obj in scene.objects
            ]
        }
        
        report = {
            "message": f"Scene '{scene_name}' exported to a glTF-like JSON structure.",
            "gltf_json": gltf_like_json
        }
        return json.dumps(report, indent=2)