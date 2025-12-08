import logging
import json
import random
import os
from datetime import datetime, timedelta
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CD_PIPELINES_FILE = Path("cd_pipelines.json")

class PipelineManager:
    """Manages CI/CD pipelines, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CD_PIPELINES_FILE):
        if cls._instance is None:
            cls._instance = super(PipelineManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.pipelines: Dict[str, Any] = cls._instance._load_pipelines()
        return cls._instance

    def _load_pipelines(self) -> Dict[str, Any]:
        """Loads pipeline information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty pipelines.")
                return {}
            except Exception as e:
                logger.error(f"Error loading pipelines from {self.file_path}: {e}")
                return {}
        return {}

    def _save_pipelines(self) -> None:
        """Saves pipeline information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.pipelines, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving pipelines to {self.file_path}: {e}")

    def start_pipeline(self, pipeline_name: str, branch: str) -> Dict[str, Any]:
        if pipeline_name in self.pipelines and self.pipelines[pipeline_name]["status"] == "running":
            return {"error": f"Pipeline '{pipeline_name}' is already running."}

        pipeline_run_id = f"run_{random.randint(100000, 999999)}"  # nosec B311
        self.pipelines[pipeline_name] = {
            "run_id": pipeline_run_id,
            "branch": branch,
            "status": "running",
            "start_time": datetime.now().isoformat() + "Z",
            "end_time": None,
            "stages": {
                "checkout": {"status": "pending", "logs": []},
                "build": {"status": "pending", "logs": []},
                "test": {"status": "pending", "logs": []},
                "deploy": {"status": "pending", "logs": []}
            }
        }
        self._save_pipelines()
        return {"pipeline_name": pipeline_name, "run_id": pipeline_run_id, "status": "started", "message": f"Pipeline '{pipeline_name}' started for branch '{branch}'."}

    def get_pipeline_status(self, pipeline_name: str) -> Optional[Dict[str, Any]]:
        if pipeline_name not in self.pipelines:
            return None
        
        pipeline_status = self.pipelines[pipeline_name]
        
        if pipeline_status["status"] == "running":
            # Simulate pipeline progress
            for stage_name in ["checkout", "build", "test", "deploy"]:
                stage = pipeline_status["stages"][stage_name]
                if stage["status"] == "pending":
                    if random.random() < 0.5: # 50% chance to start a stage  # nosec B311
                        stage["status"] = "running"
                        stage["logs"].append(f"[{datetime.now().isoformat()}] INFO: Stage '{stage_name}' started.")
                        break # Only one stage can start at a time
                elif stage["status"] == "running":
                    if random.random() < 0.7: # 70% chance to complete a stage  # nosec B311
                        stage["status"] = random.choice(["success", "failed"])  # nosec B311
                        stage["logs"].append(f"[{datetime.now().isoformat()}] INFO: Stage '{stage_name}' {stage['status']}.")
                        if stage["status"] == "failed":
                            pipeline_status["status"] = "failed"
                            break # Stop if a stage fails
                    break # Only one stage can be running at a time
            
            # If all stages are successful, mark pipeline as successful
            if all(s["status"] == "success" for s in pipeline_status["stages"].values()):
                pipeline_status["status"] = "success"
                pipeline_status["end_time"] = datetime.now().isoformat() + "Z"
            
            self._save_pipelines()
            
        return pipeline_status

    def stop_pipeline(self, pipeline_name: str) -> bool:
        if pipeline_name not in self.pipelines:
            return False
        if self.pipelines[pipeline_name]["status"] == "running":
            self.pipelines[pipeline_name]["status"] = "cancelled"
            self.pipelines[pipeline_name]["end_time"] = datetime.now().isoformat() + "Z"
            self.pipelines[pipeline_name]["stages"]["checkout"]["logs"].append(f"[{datetime.now().isoformat()}] WARNING: Pipeline cancelled by user.") # Add log to first stage
            self._save_pipelines()
            return True
        return False

    def list_pipelines(self) -> List[Dict[str, Any]]:
        return [{"name": name, "run_id": details['run_id'], "status": details['status'], "branch": details['branch'], "start_time": details['start_time']} for name, details in self.pipelines.items()]

pipeline_manager = PipelineManager()

class StartCDPipelineTool(BaseTool):
    """Starts a CI/CD pipeline for a specified project and branch."""
    def __init__(self, tool_name="start_cd_pipeline"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a Continuous Integration/Continuous Delivery (CI/CD) pipeline for a specified project and branch."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pipeline_name": {"type": "string", "description": "The name of the CI/CD pipeline to start."},
                "branch": {"type": "string", "description": "The Git branch to build and deploy from (e.g., 'main', 'develop').", "default": "main"}
            },
            "required": ["pipeline_name"]
        }

    def execute(self, pipeline_name: str, branch: str = "main", **kwargs: Any) -> str:
        result = pipeline_manager.start_pipeline(pipeline_name, branch)
        if "error" in result:
            return json.dumps(result)
        return json.dumps(result, indent=2)

class GetCDPipelineStatusTool(BaseTool):
    """Retrieves the current status of a CI/CD pipeline."""
    def __init__(self, tool_name="get_cd_pipeline_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status of a Continuous Integration/Continuous Delivery (CI/CD) pipeline, including its stages and overall progress."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"pipeline_name": {"type": "string", "description": "The name of the CI/CD pipeline to get status for."}},
            "required": ["pipeline_name"]
        }

    def execute(self, pipeline_name: str, **kwargs: Any) -> str:
        status = pipeline_manager.get_pipeline_status(pipeline_name)
        if not status:
            return json.dumps({"error": f"Pipeline '{pipeline_name}' not found."})
        return json.dumps(status, indent=2)

class StopCDPipelineTool(BaseTool):
    """Stops a running CI/CD pipeline."""
    def __init__(self, tool_name="stop_cd_pipeline"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Stops a running Continuous Integration/Continuous Delivery (CI/CD) pipeline."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"pipeline_name": {"type": "string", "description": "The name of the CI/CD pipeline to stop."}},
            "required": ["pipeline_name"]
        }

    def execute(self, pipeline_name: str, **kwargs: Any) -> str:
        success = pipeline_manager.stop_pipeline(pipeline_name)
        if success:
            return json.dumps({"message": f"Pipeline '{pipeline_name}' stopped successfully."})
        else:
            return json.dumps({"error": f"Pipeline '{pipeline_name}' not found or not running."})

class ListCDPipelinesTool(BaseTool):
    """Lists all defined CI/CD pipelines."""
    def __init__(self, tool_name="list_cd_pipelines"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all defined CI/CD pipelines, showing their name, run ID, status, and branch."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        pipelines = pipeline_manager.list_pipelines()
        if not pipelines:
            return json.dumps({"message": "No CI/CD pipelines found."})
        
        return json.dumps({"total_pipelines": len(pipelines), "pipelines": pipelines}, indent=2)