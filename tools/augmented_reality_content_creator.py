import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ARProject:
    """Represents a single AR project with its objects and properties."""
    def __init__(self, project_name: str, target_platform: str = "WebXR"):
        self.project_name = project_name
        self.target_platform = target_platform
        self.objects: List[Dict[str, Any]] = []
        self.metadata = {"creation_date": datetime.now().isoformat()}

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
            "project_name": self.project_name,
            "target_platform": self.target_platform,
            "metadata": self.metadata,
            "objects": self.objects
        }

class ProjectManager:
    """Manages all created AR projects."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance.projects: Dict[str, ARProject] = {}
        return cls._instance

    def create_project(self, project_name: str, target_platform: str) -> bool:
        if project_name in self.projects:
            return False
        self.projects[project_name] = ARProject(project_name, target_platform)
        return True

    def get_project(self, project_name: str) -> ARProject:
        return self.projects.get(project_name)

project_manager = ProjectManager()

class CreateARProjectTool(BaseTool):
    """Tool to create a new, empty AR project."""
    def __init__(self, tool_name="create_ar_project"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new, empty Augmented Reality (AR) project with a specified name and target platform."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "A unique name for the new AR project."},
                "target_platform": {"type": "string", "description": "The target platform.", "enum": ["ARKit", "ARCore", "WebXR"], "default": "WebXR"}
            },
            "required": ["project_name"]
        }

    def execute(self, project_name: str, target_platform: str = "WebXR", **kwargs: Any) -> str:
        if project_manager.create_project(project_name, target_platform):
            report = {"message": f"AR project '{project_name}' created successfully for platform '{target_platform}'."}
        else:
            report = {"error": f"An AR project with the name '{project_name}' already exists."}
        return json.dumps(report, indent=2)

class AddObjectToARProjectTool(BaseTool):
    """Tool to add a 3D object to an AR project."""
    def __init__(self, tool_name="add_object_to_ar_project"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a 3D object to an existing AR project with specified position, rotation, and scale."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "The name of the AR project to add the object to."},
                "object_id": {"type": "string", "description": "A unique ID for the new object."},
                "model_path": {"type": "string", "description": "The path to the 3D model file (e.g., 'models/chair.gltf')."},
                "position": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] position of the object."},
                "rotation": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] Euler rotation in degrees.", "default": [0, 0, 0]},
                "scale": {"type": "array", "items": {"type": "number"}, "description": "The [x, y, z] scale of the object.", "default": [1, 1, 1]}
            },
            "required": ["project_name", "object_id", "model_path", "position"]
        }

    def execute(self, project_name: str, object_id: str, model_path: str, position: List[float], rotation: List[float] = [0,0,0], scale: List[float] = [1,1,1], **kwargs: Any) -> str:
        project = project_manager.get_project(project_name)
        if not project:
            return json.dumps({"error": f"AR project '{project_name}' not found."})
        
        project.add_object(object_id, model_path, position, rotation, scale)
        report = {"message": f"Object '{object_id}' added to AR project '{project_name}'."}
        return json.dumps(report, indent=2)

class ExportARProjectToGLTFJsonTool(BaseTool):
    """Tool to export an AR project to a simplified glTF-like JSON format."""
    def __init__(self, tool_name="export_ar_project_to_gltf_json"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Exports an AR project's structure to a simplified, glTF-like JSON format, which is useful for understanding the project's composition."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"project_name": {"type": "string", "description": "The name of the project to export."}},
            "required": ["project_name"]
        }

    def execute(self, project_name: str, **kwargs: Any) -> str:
        project = project_manager.get_project(project_name)
        if not project:
            return json.dumps({"error": f"AR project '{project_name}' not found."})

        # This is a simplified representation and not a valid glTF file, but it demonstrates the structure.
        gltf_like_json = {
            "asset": {"version": "2.0"},
            "scene": 0,
            "scenes": [{"nodes": list(range(len(project.objects)))}],
            "nodes": [
                {
                    "mesh": i,
                    "translation": obj["position"],
                    "rotation": obj["rotation"], # In a real glTF, this would be a quaternion
                    "scale": obj["scale"]
                } for i, obj in enumerate(project.objects)
            ],
            "meshes": [
                {"primitives": [{"attributes": {"POSITION": i}}]} for i in range(len(project.objects))
            ],
            "buffers": [
                {"uri": obj["model_path"]} for obj in project.objects
            ]
        }
        
        report = {
            "message": f"AR project '{project_name}' exported to a glTF-like JSON structure.",
            "gltf_json": gltf_like_json
        }
        return json.dumps(report, indent=2)