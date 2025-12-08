import logging
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class Deployment:
    """Represents a single application deployment with detailed status and history."""
    def __init__(self, app_name: str, app_version: str, environment: str):
        self.deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"  # nosec B311
        self.app_name = app_name
        self.app_version = app_version
        self.environment = environment
        self.status = "initiated" # Overall status: initiated, in_progress, succeeded, failed, rolled_back
        self.stage = "pending"    # Current stage: pending, build, test, deploy, verify, rollback
        self.history: List[Dict[str, Any]] = [{"timestamp": datetime.now().isoformat(), "status": "initiated", "stage": "pending", "message": "Deployment initiated."}]
        self.start_time = datetime.now()
        self.end_time = None

    def update_status(self, status: str, stage: str = None, message: str = None):
        self.status = status
        if stage:
            self.stage = stage
        self.history.append({"timestamp": datetime.now().isoformat(), "status": status, "stage": stage, "message": message})
        if status in ["succeeded", "failed", "rolled_back"]:
            self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deployment_id": self.deployment_id,
            "app_name": self.app_name,
            "app_version": self.app_version,
            "environment": self.environment,
            "overall_status": self.status,
            "current_stage": self.stage,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "history": self.history
        }

class DeploymentManager:
    """Manages all active and historical deployments, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeploymentManager, cls).__new__(cls)
            cls._instance.deployments: Dict[str, Deployment] = {}
        return cls._instance

    def create_deployment(self, app_name: str, app_version: str, environment: str) -> Deployment:
        deployment = Deployment(app_name, app_version, environment)
        self.deployments[deployment.deployment_id] = deployment
        return deployment

    def get_deployment(self, deployment_id: str) -> Deployment:
        return self.deployments.get(deployment_id)

deployment_manager = DeploymentManager()

class DeployApplicationTool(BaseTool):
    """Initiates a new application deployment with a simulated multi-stage process."""
    def __init__(self, tool_name="deploy_application"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Initiates a new application deployment to a target environment, simulating a multi-stage process (build, test, deploy, verify)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "The name of the application to deploy."},
                "app_version": {"type": "string", "description": "The version of the application to deploy."},
                "environment": {"type": "string", "description": "The target environment.", "enum": ["development", "staging", "production"]}
            },
            "required": ["app_name", "app_version", "environment"]
        }

    def execute(self, app_name: str, app_version: str, environment: str, **kwargs: Any) -> str:
        deployment = deployment_manager.create_deployment(app_name, app_version, environment)
        deployment.update_status("in_progress", "build", "Build initiated.")
        
        report = {
            "message": f"Deployment of '{app_name}' version '{app_version}' to '{environment}' initiated.",
            "deployment_id": deployment.deployment_id,
            "current_overall_status": deployment.status,
            "current_stage": deployment.stage
        }
        return json.dumps(report, indent=2)

class CheckDeploymentStatusTool(BaseTool):
    """Checks the status of an application deployment and advances its simulated stage."""
    def __init__(self, tool_name="check_deployment_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Checks the status of an ongoing or completed application deployment and advances its simulated stage (e.g., from build to test)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"deployment_id": {"type": "string", "description": "The ID of the deployment to check."}},
            "required": ["deployment_id"]
        }

    def execute(self, deployment_id: str, **kwargs: Any) -> str:
        deployment = deployment_manager.get_deployment(deployment_id)
        if not deployment:
            return json.dumps({"error": f"Deployment with ID '{deployment_id}' not found."})

        if deployment.status in ["succeeded", "failed", "rolled_back"]:
            return json.dumps(deployment.to_dict(), indent=2)

        # Simulate advancing the deployment stage
        current_stage = deployment.stage
        next_stage = None
        new_overall_status = "in_progress"
        message = None

        if current_stage == "build":
            if random.random() < 0.9: # 90% chance to succeed build  # nosec B311
                next_stage = "test"
                message = "Build completed successfully. Proceeding to testing."
            else:
                new_overall_status = "failed"
                message = "Build failed due to compilation errors."
        elif current_stage == "test":
            if random.random() < 0.8: # 80% chance to succeed test  # nosec B311
                next_stage = "deploy"
                message = "Tests passed. Proceeding to deployment."
            else:
                new_overall_status = "failed"
                message = "Tests failed due to functional issues."
        elif current_stage == "deploy":
            if random.random() < 0.95: # 95% chance to succeed deploy  # nosec B311
                next_stage = "verify"
                message = "Application deployed successfully. Initiating verification."
            else:
                new_overall_status = "failed"
                message = "Deployment failed due to infrastructure issues."
        elif current_stage == "verify":
            if random.random() < 0.9: # 90% chance to succeed verify  # nosec B311
                new_overall_status = "succeeded"
                message = "Verification successful. Deployment completed."
            else:
                new_overall_status = "failed"
                message = "Verification failed. Application not functioning as expected."
        
        deployment.update_status(new_overall_status, next_stage, message)
        return json.dumps(deployment.to_dict(), indent=2)

class RollbackDeploymentTool(BaseTool):
    """Simulates rolling back a failed or problematic deployment."""
    def __init__(self, tool_name="rollback_deployment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates rolling back a failed or problematic deployment to a previous stable state."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"deployment_id": {"type": "string", "description": "The ID of the deployment to roll back."}},
            "required": ["deployment_id"]
        }

    def execute(self, deployment_id: str, **kwargs: Any) -> str:
        deployment = deployment_manager.get_deployment(deployment_id)
        if not deployment:
            return json.dumps({"error": f"Deployment with ID '{deployment_id}' not found."})

        if deployment.status == "succeeded":
            return json.dumps({"error": f"Deployment '{deployment_id}' is already successful. No rollback needed unless explicitly requested for a successful deployment."})
        
        deployment.update_status("rolled_back", "rollback", "Deployment rolled back to previous version.")
        
        report = {
            "message": f"Deployment '{deployment_id}' successfully rolled back.",
            "new_overall_status": deployment.status,
            "new_stage": deployment.stage
        }
        return json.dumps(report, indent=2)