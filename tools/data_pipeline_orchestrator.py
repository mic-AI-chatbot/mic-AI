import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataPipelineOrchestratorTool(BaseTool):
    """
    A tool for orchestrating data pipelines, allowing for their creation,
    starting, stopping, and status monitoring.
    """

    def __init__(self, tool_name: str = "data_pipeline_orchestrator"):
        super().__init__(tool_name)
        self.pipelines_file = "data_pipelines.json"
        self.pipelines: Dict[str, Dict[str, Any]] = self._load_pipelines()

    @property
    def description(self) -> str:
        return "Orchestrates data pipelines: creates, starts, stops, and monitors their status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The pipeline operation to perform.",
                    "enum": ["create_pipeline", "start_pipeline", "stop_pipeline", "get_pipeline_status", "list_pipelines"]
                },
                "pipeline_id": {"type": "string"},
                "pipeline_name": {"type": "string"},
                "definition": {"type": "object"},
                "description": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_pipelines(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.pipelines_file):
            with open(self.pipelines_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted pipelines file '{self.pipelines_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_pipelines(self) -> None:
        with open(self.pipelines_file, 'w') as f:
            json.dump(self.pipelines, f, indent=4)

    def _create_pipeline(self, pipeline_id: str, pipeline_name: str, definition: Dict[str, Any], description: Optional[str] = None) -> Dict[str, Any]:
        if not all([pipeline_id, pipeline_name, definition]):
            raise ValueError("Pipeline ID, name, and definition cannot be empty.")
        if pipeline_id in self.pipelines:
            raise ValueError(f"Data pipeline '{pipeline_id}' already exists.")

        new_pipeline = {
            "pipeline_id": pipeline_id, "pipeline_name": pipeline_name, "definition": definition,
            "description": description, "status": "created", "created_at": datetime.now().isoformat(),
            "last_run_at": None
        }
        self.pipelines[pipeline_id] = new_pipeline
        self._save_pipelines()
        return new_pipeline

    def _start_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline: raise ValueError(f"Data pipeline '{pipeline_id}' not found.")
        if pipeline["status"] == "running": raise ValueError(f"Data pipeline '{pipeline_id}' is already running.")

        pipeline["status"] = "running"
        pipeline["last_run_at"] = datetime.now().isoformat()
        self._save_pipelines()
        return pipeline

    def _stop_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        pipeline = self.pipelines.get(pipeline_id)
        if not pipeline: raise ValueError(f"Data pipeline '{pipeline_id}' not found.")
        if pipeline["status"] == "stopped": raise ValueError(f"Data pipeline '{pipeline_id}' is already stopped.")

        pipeline["status"] = "stopped"
        self._save_pipelines()
        return pipeline

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_pipeline":
            return self._create_pipeline(kwargs.get("pipeline_id"), kwargs.get("pipeline_name"), kwargs.get("definition"), kwargs.get("description"))
        elif operation == "start_pipeline":
            return self._start_pipeline(kwargs.get("pipeline_id"))
        elif operation == "stop_pipeline":
            return self._stop_pipeline(kwargs.get("pipeline_id"))
        elif operation == "get_pipeline_status":
            return self.pipelines.get(kwargs.get("pipeline_id"))
        elif operation == "list_pipelines":
            return list(self.pipelines.values())
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataPipelineOrchestratorTool functionality...")
    tool = DataPipelineOrchestratorTool()
    
    try:
        print("\n--- Creating Pipeline ---")
        tool.execute(operation="create_pipeline", pipeline_id="etl_customer_data", pipeline_name="ETL Customer Data", definition={"source": "CRM_DB", "transform": "clean"}, description="Extracts and cleans customer data.")
        
        print("\n--- Starting Pipeline ---")
        tool.execute(operation="start_pipeline", pipeline_id="etl_customer_data")

        print("\n--- Getting Pipeline Status ---")
        status = tool.execute(operation="get_pipeline_status", pipeline_id="etl_customer_data")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.pipelines_file):
            os.remove(tool.pipelines_file)
        print("\nCleanup complete.")