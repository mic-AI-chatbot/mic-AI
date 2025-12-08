import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

ORCHESTRATION_DATA_FILE = Path("orchestration_data.json")

class OrchestrationManager:
    """Manages container deployments and cluster health, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = ORCHESTRATION_DATA_FILE):
        if cls._instance is None:
            cls._instance = super(OrchestrationManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.data: Dict[str, Any] = cls._instance._load_data()
        return cls._instance

    def _load_data(self) -> Dict[str, Any]:
        """Loads orchestration data from the JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty data.")
                return {"deployments": {}, "cluster_health": self._generate_initial_health()}
            except Exception as e:
                logger.error(f"Error loading data from {self.file_path}: {e}")
                return {"deployments": {}, "cluster_health": self._generate_initial_health()}
        return {"deployments": {}, "cluster_health": self._generate_initial_health()}

    def _save_data(self) -> None:
        """Saves orchestration data to the JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving data to {self.file_path}: {e}")

    def _generate_initial_health(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "cpu_utilization_percent": round(random.uniform(20, 50), 2),  # nosec B311
            "memory_utilization_percent": round(random.uniform(30, 60), 2),  # nosec B311
            "node_count": random.randint(3, 10),  # nosec B311
            "last_updated": datetime.now().isoformat() + "Z"
        }

    def create_deployment(self, deployment_name: str, image: str, replicas: int, ports: List[int]) -> bool:
        if deployment_name in self.data["deployments"]:
            return False
        self.data["deployments"][deployment_name] = {
            "image": image,
            "replicas": replicas,
            "ports": ports,
            "status": "running",
            "created_at": datetime.now().isoformat() + "Z",
            "updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_data()
        return True

    def get_deployment(self, deployment_name: str) -> Optional[Dict[str, Any]]:
        return self.data["deployments"].get(deployment_name)

    def update_deployment(self, deployment_name: str, image: Optional[str] = None, replicas: Optional[int] = None, ports: Optional[List[int]] = None) -> bool:
        if deployment_name not in self.data["deployments"]:
            return False
        
        if image is not None: self.data["deployments"][deployment_name]["image"] = image
        if replicas is not None: self.data["deployments"][deployment_name]["replicas"] = replicas
        if ports is not None: self.data["deployments"][deployment_name]["ports"] = ports
        
        self.data["deployments"][deployment_name]["updated_at"] = datetime.now().isoformat() + "Z"
        self._save_data()
        return True

    def scale_deployment(self, deployment_name: str, new_replicas: int) -> bool:
        if deployment_name not in self.data["deployments"]:
            return False
        if new_replicas < 0:
            return False
        self.data["deployments"][deployment_name]["replicas"] = new_replicas
        self.data["deployments"][deployment_name]["updated_at"] = datetime.now().isoformat() + "Z"
        self._save_data()
        return True

    def delete_deployment(self, deployment_name: str) -> bool:
        if deployment_name in self.data["deployments"]:
            del self.data["deployments"][deployment_name]
            self._save_data()
            return True
        return False

    def list_deployments(self) -> List[Dict[str, Any]]:
        return [{"name": name, "image": details['image'], "replicas": details['replicas'], "status": details['status'], "updated_at": details['updated_at']} for name, details in self.data["deployments"].items()]

    def get_cluster_health(self) -> Dict[str, Any]:
        # Simulate dynamic health updates
        health = self.data["cluster_health"]
        health["cpu_utilization_percent"] = round(random.uniform(20, 80), 2)  # nosec B311
        health["memory_utilization_percent"] = round(random.uniform(30, 90), 2)  # nosec B311
        health["status"] = "healthy" if health["cpu_utilization_percent"] < 70 and health["memory_utilization_percent"] < 80 else "degraded"
        health["last_updated"] = datetime.now().isoformat() + "Z"
        self._save_data() # Save updated health
        return health

orchestration_manager = OrchestrationManager()

class CreateDeploymentTool(BaseTool):
    """Creates a new container deployment in the orchestration system."""
    def __init__(self, tool_name="create_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new container deployment with a specified image, number of replicas, and exposed ports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "deployment_name": {"type": "string", "description": "A unique name for the deployment."},
                "image": {"type": "string", "description": "The container image to deploy (e.g., 'nginx:latest')."},
                "replicas": {"type": "integer", "description": "The number of container instances to run.", "default": 1},
                "ports": {"type": "array", "items": {"type": "integer"}, "description": "A list of ports to expose (e.g., [80, 443]).", "default": []}
            },
            "required": ["deployment_name", "image"]
        }

    def execute(self, deployment_name: str, image: str, replicas: int = 1, ports: List[int] = None, **kwargs: Any) -> str:
        if ports is None: ports = []
        success = orchestration_manager.create_deployment(deployment_name, image, replicas, ports)
        if success:
            report = {"message": f"Deployment '{deployment_name}' created successfully with {replicas} replicas of image '{image}'."}
        else:
            report = {"error": f"Deployment '{deployment_name}' already exists. Please choose a unique name."}
        return json.dumps(report, indent=2)

class GetDeploymentTool(BaseTool):
    """Retrieves details of a specific container deployment."""
    def __init__(self, tool_name="get_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific container deployment, including its image, replicas, and exposed ports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"deployment_name": {"type": "string", "description": "The name of the deployment to retrieve details for."}},
            "required": ["deployment_name"]
        }

    def execute(self, deployment_name: str, **kwargs: Any) -> str:
        deployment = orchestration_manager.get_deployment(deployment_name)
        if deployment:
            return json.dumps(deployment, indent=2)
        else:
            return json.dumps({"error": f"Deployment '{deployment_name}' not found."})

class UpdateDeploymentTool(BaseTool):
    """Updates an existing container deployment."""
    def __init__(self, tool_name="update_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Updates an existing container deployment (e.g., changing image version, exposed ports)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "deployment_name": {"type": "string", "description": "The name of the deployment to update."},
                "image": {"type": "string", "description": "Optional: The new container image to deploy.", "default": None},
                "ports": {"type": "array", "items": {"type": "integer"}, "description": "Optional: The new list of ports to expose.", "default": None}
            },
            "required": ["deployment_name"]
        }

    def execute(self, deployment_name: str, image: Optional[str] = None, ports: Optional[List[int]] = None, **kwargs: Any) -> str:
        success = orchestration_manager.update_deployment(deployment_name, image, None, ports) # Replicas not updated here
        if success:
            report = {"message": f"Deployment '{deployment_name}' updated successfully."}
        else:
            report = {"error": f"Deployment '{deployment_name}' not found or no changes made."}
        return json.dumps(report, indent=2)

class ScaleDeploymentTool(BaseTool):
    """Scales a container deployment up or down."""
    def __init__(self, tool_name="scale_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Scales a container deployment up or down by adjusting the number of replicas."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "deployment_name": {"type": "string", "description": "The name of the deployment to scale."},
                "new_replicas": {"type": "integer", "description": "The new number of container instances to run."}
            },
            "required": ["deployment_name", "new_replicas"]
        }

    def execute(self, deployment_name: str, new_replicas: int, **kwargs: Any) -> str:
        success = orchestration_manager.scale_deployment(deployment_name, new_replicas)
        if success:
            report = {"message": f"Deployment '{deployment_name}' scaled to {new_replicas} replicas successfully."}
        else:
            report = {"error": f"Deployment '{deployment_name}' not found or invalid number of replicas."}
        return json.dumps(report, indent=2)

class DeleteDeploymentTool(BaseTool):
    """Deletes a container deployment."""
    def __init__(self, tool_name="delete_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Deletes a container deployment from the orchestration system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"deployment_name": {"type": "string", "description": "The name of the deployment to delete."}},
            "required": ["deployment_name"]
        }

    def execute(self, deployment_name: str, **kwargs: Any) -> str:
        success = orchestration_manager.delete_deployment(deployment_name)
        if success:
            report = {"message": f"Deployment '{deployment_name}' deleted successfully."}
        else:
            report = {"error": f"Deployment '{deployment_name}' not found."}
        return json.dumps(report, indent=2)

class ListDeploymentsTool(BaseTool):
    """Lists all container deployments."""
    def __init__(self, tool_name="list_deployments"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all container deployments, showing their name, image, replicas, and status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        deployments = orchestration_manager.list_deployments()
        if not deployments:
            return json.dumps({"message": "No container deployments found."})
        
        return json.dumps({"total_deployments": len(deployments), "deployments": deployments}, indent=2)

class GetClusterHealthTool(BaseTool):
    """Retrieves the current health status of the container cluster."""
    def __init__(self, tool_name="get_cluster_health"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current health and resource utilization status of the container orchestration cluster."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        health = orchestration_manager.get_cluster_health()
        return json.dumps(health, indent=2)
