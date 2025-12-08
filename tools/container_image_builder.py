import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CONTAINER_IMAGES_FILE = Path("container_images.json")

class ImageManager:
    """Manages container image information, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CONTAINER_IMAGES_FILE):
        if cls._instance is None:
            cls._instance = super(ImageManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.images: Dict[str, Any] = cls._instance._load_images()
        return cls._instance

    def _load_images(self) -> Dict[str, Any]:
        """Loads container image information from the JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty image data.")
                return {}
            except Exception as e:
                logger.error(f"Error loading images from {self.file_path}: {e}")
                return {}
        return {}

    def _save_images(self) -> None:
        """Saves container image information to the JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.images, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving images to {self.file_path}: {e}")

    def build_image(self, image_name: str, dockerfile_path: str, context_path: str, runtime: str) -> Dict[str, Any]:
        if image_name in self.images:
            return {"error": f"Image with name '{image_name}' already exists."}

        image_id = f"img_{random.randint(100000, 999999)}"  # nosec B311
        build_logs = [
            f"[{datetime.now().isoformat()}] INFO: Starting build for {image_name}...",
            f"[{datetime.now().isoformat()}] INFO: Using Dockerfile at {dockerfile_path} and context {context_path}",
            f"[{datetime.now().isoformat()}] INFO: Pulling base image (simulated)...",
            f"[{datetime.now().isoformat()}] INFO: Running build commands (simulated)...",
            f"[{datetime.now().isoformat()}] INFO: Successfully built {image_id}",
            f"[{datetime.now().isoformat()}] INFO: Tagged {image_id} as {image_name}:latest"
        ]
        
        self.images[image_name] = {
            "id": image_id,
            "tags": [f"{image_name}:latest"],
            "dockerfile_path": dockerfile_path,
            "context_path": context_path,
            "runtime": runtime,
            "status": "built",
            "build_logs": build_logs,
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_images()
        return {"image_name": image_name, "image_id": image_id, "status": "success", "logs": build_logs}

    def tag_image(self, image_name: str, new_tag: str) -> bool:
        if image_name not in self.images:
            return False
        
        full_tag = f"{image_name}:{new_tag}"
        if full_tag not in self.images[image_name]["tags"]:
            self.images[image_name]["tags"].append(full_tag)
            self._save_images()
        return True

    def push_image(self, image_name: str, tag: str, registry: str) -> Dict[str, Any]:
        if image_name not in self.images:
            return {"error": f"Image '{image_name}' not found."}
        
        full_image_name = f"{image_name}:{tag}"
        if full_image_name not in self.images[image_name]["tags"]:
            return {"error": f"Image '{image_name}' not tagged with '{tag}'."}

        # Simulate push
        push_logs = [
            f"[{datetime.now().isoformat()}] INFO: Pushing {full_image_name} to {registry}...",
            f"[{datetime.now().isoformat()}] INFO: The push refers to repository [{registry}/{image_name}]",
            f"[{datetime.now().isoformat()}] INFO: {tag}: Pushed",
            f"[{datetime.now().isoformat()}] INFO: Digest: sha256:{random.randint(10**20, 10**21)}",  # nosec B311
            f"[{datetime.now().isoformat()}] INFO: Successfully pushed {full_image_name}"
        ]
        self.images[image_name]["last_pushed"] = datetime.now().isoformat() + "Z"
        self._save_images()
        return {"image_name": image_name, "tag": tag, "registry": registry, "status": "pushed", "logs": push_logs}

    def list_images(self) -> List[Dict[str, Any]]:
        return [{"name": name, "id": details['id'], "tags": details['tags'], "status": details['status'], "created_at": details['created_at']} for name, details in self.images.items()]

image_manager = ImageManager()

class BuildContainerImageTool(BaseTool):
    """Builds a new container image and stores its metadata persistently."""
    def __init__(self, tool_name="build_container_image"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Builds a new container image from a Dockerfile and context path, returning build logs and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_name": {"type": "string", "description": "A unique name for the container image."},
                "dockerfile_path": {"type": "string", "description": "The path to the Dockerfile (e.g., './Dockerfile').", "default": "./Dockerfile"},
                "context_path": {"type": "string", "description": "The build context path (e.g., '.').", "default": "."},
                "runtime": {"type": "string", "description": "The container runtime (e.g., 'docker', 'podman').", "default": "docker"}
            },
            "required": ["image_name"]
        }

    def execute(self, image_name: str, dockerfile_path: str = "./Dockerfile", context_path: str = ".", runtime: str = "docker", **kwargs: Any) -> str:
        result = image_manager.build_image(image_name, dockerfile_path, context_path, runtime)
        if "error" in result:
            return json.dumps(result)
        return json.dumps(result, indent=2)

class TagContainerImageTool(BaseTool):
    """Tags an existing container image with a new tag."""
    def __init__(self, tool_name="tag_container_image"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tags an existing container image with a new tag (e.g., 'my-image:v1.0')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_name": {"type": "string", "description": "The name of the existing container image."},
                "new_tag": {"type": "string", "description": "The new tag to apply to the image (e.g., 'v1.0', 'latest')."}
            },
            "required": ["image_name", "new_tag"]
        }

    def execute(self, image_name: str, new_tag: str, **kwargs: Any) -> str:
        success = image_manager.tag_image(image_name, new_tag)
        if success:
            return json.dumps({"message": f"Image '{image_name}' successfully tagged as '{new_tag}'."})
        else:
            return json.dumps({"error": f"Image with name '{image_name}' not found."})

class PushContainerImageTool(BaseTool):
    """Pushes a container image to a registry."""
    def __init__(self, tool_name="push_container_image"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Pushes a container image to a specified registry (e.g., Docker Hub, ECR)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_name": {"type": "string", "description": "The name of the image to push."},
                "tag": {"type": "string", "description": "The tag of the image to push (e.g., 'latest', 'v1.0')."},
                "registry": {"type": "string", "description": "The container registry to push to (e.g., 'docker.io/myuser', '123456789012.dkr.ecr.us-east-1.amazonaws.com')."}
            },
            "required": ["image_name", "tag", "registry"]
        }

    def execute(self, image_name: str, tag: str, registry: str, **kwargs: Any) -> str:
        result = image_manager.push_image(image_name, tag, registry)
        if "error" in result:
            return json.dumps(result)
        return json.dumps(result, indent=2)

class ListContainerImagesTool(BaseTool):
    """Lists all built container images."""
    def __init__(self, tool_name="list_container_images"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all built container images, showing their name, ID, tags, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        images = image_manager.list_images()
        if not images:
            return json.dumps({"message": "No container images found."})
        
        return json.dumps({"total_images": len(images), "images": images}, indent=2)