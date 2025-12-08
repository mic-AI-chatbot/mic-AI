import logging
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BuildJob:
    """Represents a single build job with detailed status, stages, history, and simulated artifacts."""
    def __init__(self, project_name: str, branch_name: str, build_parameters: Dict[str, Any]):
        self.build_id = f"build_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"  # nosec B311
        self.project_name = project_name
        self.branch_name = branch_name
        self.build_parameters = build_parameters
        self.status = "initiated" # Overall status: initiated, running, succeeded, failed, cancelled
        self.current_stage = "pending" # Current stage: pending, checkout, compile, test, package
        self.history: List[Dict[str, Any]] = [{"timestamp": datetime.now().isoformat(), "status": "initiated", "stage": "pending", "message": "Build initiated."}]
        self.start_time = datetime.now()
        self.end_time = None
        self.logs: List[str] = []
        self.artifacts: List[str] = []

    def update_status(self, status: str, stage: str = None, message: str = None):
        self.status = status
        if stage:
            self.current_stage = stage
        self.history.append({"timestamp": datetime.now().isoformat(), "status": status, "stage": stage, "message": message})
        self.logs.append(f"[{datetime.now().isoformat()}] [{status.upper()}] {message}")
        if status in ["succeeded", "failed", "cancelled"]:
            self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "build_id": self.build_id,
            "project_name": self.project_name,
            "branch_name": self.branch_name,
            "build_parameters": self.build_parameters,
            "overall_status": self.status,
            "current_stage": self.current_stage,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "history_count": len(self.history),
            "artifacts": self.artifacts
        }

class BuildManager:
    """Manages all build jobs, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BuildManager, cls).__new__(cls)
            cls._instance.build_jobs: Dict[str, BuildJob] = {}
        return cls._instance

    def create_build_job(self, project_name: str, branch_name: str, build_parameters: Dict[str, Any]) -> BuildJob:
        job = BuildJob(project_name, branch_name, build_parameters)
        self.build_jobs[job.build_id] = job
        return job

    def get_build_job(self, build_id: str) -> BuildJob:
        return self.build_jobs.get(build_id)

build_manager = BuildManager()

class TriggerBuildTool(BaseTool):
    """Triggers a build job in a CI/CD pipeline."""
    def __init__(self, tool_name="trigger_build"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Triggers a build job for a specified project and branch in a continuous integration/continuous delivery (CI/CD) pipeline."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "The name of the project to build."},
                "branch_name": {"type": "string", "description": "The name of the branch to build from (e.g., 'main', 'feature/new-feature')."},
                "build_parameters": {"type": "object", "description": "Optional: A dictionary of additional parameters for the build job."}
            },
            "required": ["project_name", "branch_name"]
        }

    def execute(self, project_name: str, branch_name: str, build_parameters: Dict[str, Any] = None, **kwargs: Any) -> str:
        job = build_manager.create_build_job(project_name, branch_name, build_parameters if build_parameters else {})
        job.update_status("running", "checkout", "Code checkout initiated.")
        
        report = {
            "message": f"Build for project '{project_name}' on branch '{branch_name}' triggered.",
            "build_id": job.build_id,
            "current_overall_status": job.status,
            "current_stage": job.current_stage
        }
        return json.dumps(report, indent=2)

class GetBuildStatusTool(BaseTool):
    """Retrieves the current status of a build job and advances its simulated stage."""
    def __init__(self, tool_name="get_build_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status of a build job and advances its simulated stage (e.g., from checkout to compile)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"build_id": {"type": "string", "description": "The ID of the build job to check status for."}},
            "required": ["build_id"]
        }

    def execute(self, build_id: str, **kwargs: Any) -> str:
        job = build_manager.get_build_job(build_id)
        if not job:
            return json.dumps({"error": f"Build job with ID '{build_id}' not found."})

        if job.status in ["succeeded", "failed", "cancelled"]:
            return json.dumps(job.to_dict(), indent=2)

        # Simulate advancing the build stage
        current_stage = job.current_stage
        next_stage = None
        new_status = "running"
        message = None

        if current_stage == "checkout":
            if random.random() < 0.95: # 95% chance to succeed checkout  # nosec B311
                next_stage = "compile"
                message = "Code checked out successfully. Starting compilation."
            else:
                new_status = "failed"
                message = "Code checkout failed."
        elif current_stage == "compile":
            if random.random() < 0.9: # 90% chance to succeed compile  # nosec B311
                next_stage = "test"
                message = "Compilation successful. Running tests."
            else:
                new_status = "failed"
                message = "Compilation failed due to syntax errors."
        elif current_stage == "test":
            if random.random() < 0.8: # 80% chance to succeed test  # nosec B311
                next_stage = "package"
                message = "Tests passed. Packaging application."
            else:
                new_status = "failed"
                message = "Tests failed due to functional issues."
        elif current_stage == "package":
            if random.random() < 0.95: # 95% chance to succeed package  # nosec B311
                new_status = "succeeded"
                message = "Application packaged successfully. Build completed."
                job.artifacts.append(f"{job.project_name}-{job.branch_name}-{job.build_id}.zip")
            else:
                new_status = "failed"
                message = "Packaging failed."
        
        job.update_status(new_status, next_stage, message)
        return json.dumps(job.to_dict(), indent=2)

class GetBuildLogsTool(BaseTool):
    """Retrieves the simulated logs for a specific build job."""
    def __init__(self, tool_name="get_build_logs"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the simulated logs for a specific build job, showing the history of events and status updates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"build_id": {"type": "string", "description": "The ID of the build job to retrieve logs for."}},
            "required": ["build_id"]
        }

    def execute(self, build_id: str, **kwargs: Any) -> str:
        job = build_manager.get_build_job(build_id)
        if not job:
            return json.dumps({"error": f"Build job with ID '{build_id}' not found."})
            
        report = {
            "build_id": build_id,
            "logs": job.logs
        }
        return json.dumps(report, indent=2)