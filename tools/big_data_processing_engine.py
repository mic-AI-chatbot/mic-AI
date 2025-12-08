import logging
import json
import random
import pandas as pd # Used for conceptual data processing, though not directly in simulation logic
import numpy as np # Used for conceptual data processing, though not directly in simulation logic
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BigDataJob:
    """Represents a single big data processing job with detailed status and results."""
    def __init__(self, job_name: str, job_type: str, data_source: str):
        self.job_name = job_name
        self.job_type = job_type
        self.data_source = data_source
        self.status = "initiated" # initiated, running, completed, failed
        self.progress_percent = 0
        self.start_time = datetime.now()
        self.end_time = None
        self.results: Dict[str, Any] = {}
        self.error_message: str = None

    def update_status(self, status: str, progress: int = None, results: Dict[str, Any] = None, error_message: str = None):
        self.status = status
        if progress is not None:
            self.progress_percent = progress
        if status in ["completed", "failed"]:
            self.end_time = datetime.now()
        if results:
            self.results = results
        if error_message:
            self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_name": self.job_name,
            "job_type": self.job_type,
            "data_source": self.data_source,
            "status": self.status,
            "progress_percent": self.progress_percent,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "results": self.results,
            "error_message": self.error_message
        }

class JobManager:
    """Manages all big data jobs, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobManager, cls).__new__(cls)
            cls._instance.jobs: Dict[str, BigDataJob] = {}
        return cls._instance

    def create_job(self, job_name: str, job_type: str, data_source: str) -> BigDataJob:
        job = BigDataJob(job_name, job_type, data_source)
        self.jobs[job_name] = job
        return job

    def get_job(self, job_name: str) -> BigDataJob:
        return self.jobs.get(job_name)

job_manager = JobManager()

class RunBigDataJobTool(BaseTool):
    """Runs a big data processing job on a specified data source."""
    def __init__(self, tool_name="run_big_data_job"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Initiates a big data processing job (e.g., ETL, analytics, machine learning) on a specified data source."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "job_name": {"type": "string", "description": "A unique name for the big data job."},
                "job_type": {"type": "string", "description": "The type of big data job.", "enum": ["etl", "analytics", "machine_learning"]},
                "data_source": {"type": "string", "description": "The data source for the job (e.g., 'hdfs://data', 's3://my-bucket/logs')."}
            },
            "required": ["job_name", "job_type", "data_source"]
        }

    def execute(self, job_name: str, job_type: str, data_source: str, **kwargs: Any) -> str:
        if job_name in job_manager.jobs:
            return json.dumps({"error": f"Job '{job_name}' already exists. Please choose a unique name."})
        
        job = job_manager.create_job(job_name, job_type, data_source)
        job.update_status("running", 10) # Simulate initial progress
        
        report = {
            "message": f"Big data job '{job_name}' of type '{job_type}' initiated on '{data_source}'.",
            "job_details": job.to_dict()
        }
        return json.dumps(report, indent=2)

class GetBigDataJobStatusTool(BaseTool):
    """Retrieves the current status of a big data job."""
    def __init__(self, tool_name="get_big_data_job_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status and progress of a running or completed big data job."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"job_name": {"type": "string", "description": "The name of the big data job to check status for."}},
            "required": ["job_name"]
        }

    def execute(self, job_name: str, **kwargs: Any) -> str:
        job = job_manager.get_job(job_name)
        if not job:
            return json.dumps({"error": f"Job '{job_name}' not found."})

        # Simulate progress and completion/failure if job is still running
        if job.status == "running":
            if job.progress_percent < 90:
                job.update_status("running", job.progress_percent + random.randint(10, 30))  # nosec B311
            else:
                if random.random() < 0.9: # 90% chance to complete successfully  # nosec B311
                    simulated_results = {}
                    if job.job_type == "etl":
                        simulated_results = {"records_processed": 100000, "data_quality_score": 0.98}
                    elif job.job_type == "analytics":
                        simulated_results = {"insights": "Sales increased by 15% last quarter.", "report_link": "http://example.com/report.pdf"}
                    elif job.job_type == "machine_learning":
                        simulated_results = {"model_accuracy": 0.85, "model_version": "v1.2"}
                    job.update_status("completed", 100, simulated_results)
                else:
                    job.update_status("failed", job.progress_percent, error_message="Processing failed due to data inconsistency or resource limits.")
        
        return json.dumps(job.to_dict(), indent=2)

class GetBigDataJobResultsTool(BaseTool):
    """Retrieves the results of a completed big data job."""
    def __init__(self, tool_name="get_big_data_job_results"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the simulated results of a completed big data processing job."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"job_name": {"type": "string", "description": "The name of the big data job to retrieve results for."}},
            "required": ["job_name"]
        }

    def execute(self, job_name: str, **kwargs: Any) -> str:
        job = job_manager.get_job(job_name)
        if not job:
            return json.dumps({"error": f"Job '{job_name}' not found."})
        if job.status != "completed":
            return json.dumps({"error": f"Job '{job_name}' is not completed. Current status: {job.status}. Please check status first."})
        
        return json.dumps({"job_name": job_name, "results": job.results}, indent=2)