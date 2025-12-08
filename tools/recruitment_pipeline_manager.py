import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RecruitmentPipelineSimulatorTool(BaseTool):
    """
    A tool that simulates recruitment pipeline management, allowing for adding
    candidates, updating their stages, and generating pipeline status reports.
    """

    def __init__(self, tool_name: str = "RecruitmentPipelineSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.candidates_file = os.path.join(self.data_dir, "candidate_data.json")
        # Candidates structure: {candidate_id: {name: ..., job_id: ..., current_stage: ..., status: ...}}
        self.candidates: Dict[str, Dict[str, Any]] = self._load_data(self.candidates_file, default={})
        self.pipeline_stages = ["Application Received", "Resume Review", "Phone Screen", "Technical Interview", "Onsite Interview", "Offer Extended", "Hired", "Rejected"]

    @property
    def description(self) -> str:
        return "Simulates recruitment pipeline management: add candidates, update stages, and generate status reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_candidate", "update_candidate_stage", "get_pipeline_status", "generate_report"]},
                "candidate_id": {"type": "string"},
                "name": {"type": "string"},
                "job_id": {"type": "string"},
                "current_stage": {"type": "string", "enum": ["Application Received", "Resume Review", "Phone Screen", "Technical Interview", "Onsite Interview", "Offer Extended", "Hired", "Rejected"]},
                "new_stage": {"type": "string", "enum": ["Application Received", "Resume Review", "Phone Screen", "Technical Interview", "Onsite Interview", "Offer Extended", "Hired", "Rejected"]},
                "report_type": {"type": "string", "enum": ["summary", "detailed"], "default": "summary"}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.candidates_file, 'w') as f: json.dump(self.candidates, f, indent=2)

    def add_candidate(self, candidate_id: str, name: str, job_id: str, current_stage: str = "Application Received") -> Dict[str, Any]:
        """Adds a new candidate to the pipeline."""
        if candidate_id in self.candidates: raise ValueError(f"Candidate '{candidate_id}' already exists.")
        if current_stage not in self.pipeline_stages: raise ValueError(f"Invalid stage: {current_stage}.")
        
        new_candidate = {
            "id": candidate_id, "name": name, "job_id": job_id,
            "current_stage": current_stage, "status": "active",
            "added_at": datetime.now().isoformat()
        }
        self.candidates[candidate_id] = new_candidate
        self._save_data()
        return new_candidate

    def update_candidate_stage(self, candidate_id: str, new_stage: str) -> Dict[str, Any]:
        """Updates a candidate's stage in the pipeline."""
        candidate = self.candidates.get(candidate_id)
        if not candidate: raise ValueError(f"Candidate '{candidate_id}' not found.")
        if new_stage not in self.pipeline_stages: raise ValueError(f"Invalid stage: {new_stage}.")
        
        candidate["current_stage"] = new_stage
        candidate["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return candidate

    def get_pipeline_status(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves the current status of the recruitment pipeline."""
        status_by_stage = {stage: 0 for stage in self.pipeline_stages}
        total_candidates = 0
        
        for candidate in self.candidates.values():
            if job_id is None or candidate["job_id"] == job_id:
                status_by_stage[candidate["current_stage"]] = status_by_stage.get(candidate["current_stage"], 0) + 1
                total_candidates += 1
        
        return {"status": "success", "total_candidates": total_candidates, "candidates_by_stage": status_by_stage}

    def generate_report(self, job_id: Optional[str] = None, report_type: str = "summary") -> Dict[str, Any]:
        """Generates a recruitment pipeline report."""
        pipeline_status = self.get_pipeline_status(job_id)
        
        report_lines = [f"--- Recruitment Pipeline Report ({job_id or 'All Jobs'}) ---"]
        report_lines.append(f"Total Candidates: {pipeline_status['total_candidates']}")
        
        if report_type == "summary":
            report_lines.append("\nCandidates by Stage:")
            for stage, count in pipeline_status["candidates_by_stage"].items():
                report_lines.append(f"- {stage}: {count}")
        elif report_type == "detailed":
            report_lines.append("\nDetailed Candidate List:")
            for candidate in self.candidates.values():
                if job_id is None or candidate["job_id"] == job_id:
                    report_lines.append(f"- {candidate['name']} (ID: {candidate['id']}) - Job: {candidate['job_id']} - Stage: {candidate['current_stage']}")
        
        return {"status": "success", "report": "\n".join(report_lines)}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "add_candidate":
            candidate_id = kwargs.get('candidate_id')
            name = kwargs.get('name')
            job_id = kwargs.get('job_id')
            if not all([candidate_id, name, job_id]):
                raise ValueError("Missing 'candidate_id', 'name', or 'job_id' for 'add_candidate' operation.")
            return self.add_candidate(candidate_id, name, job_id, kwargs.get('current_stage', 'Application Received'))
        elif operation == "update_candidate_stage":
            candidate_id = kwargs.get('candidate_id')
            new_stage = kwargs.get('new_stage')
            if not all([candidate_id, new_stage]):
                raise ValueError("Missing 'candidate_id' or 'new_stage' for 'update_candidate_stage' operation.")
            return self.update_candidate_stage(candidate_id, new_stage)
        elif operation == "get_pipeline_status":
            # job_id is optional, so no strict check needed here
            return self.get_pipeline_status(kwargs.get('job_id'))
        elif operation == "generate_report":
            # job_id and report_type are optional, so no strict check needed here
            return self.generate_report(kwargs.get('job_id'), kwargs.get('report_type', 'summary'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RecruitmentPipelineSimulatorTool functionality...")
    temp_dir = "temp_recruitment_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rec_tool = RecruitmentPipelineSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add candidates
        print("\n--- Adding candidates ---")
        rec_tool.execute(operation="add_candidate", candidate_id="cand_001", name="Alice Smith", job_id="SWE_Lead", current_stage="Application Received")
        rec_tool.execute(operation="add_candidate", candidate_id="cand_002", name="Bob Johnson", job_id="SWE_Lead", current_stage="Resume Review")
        rec_tool.execute(operation="add_candidate", candidate_id="cand_003", name="Charlie Brown", job_id="UX_Designer", current_stage="Application Received")
        print("Candidates added.")

        # 2. Update candidate stage
        print("\n--- Updating 'cand_001' to 'Phone Screen' ---")
        rec_tool.execute(operation="update_candidate_stage", candidate_id="cand_001", new_stage="Phone Screen")
        print("Stage updated.")

        # 3. Get pipeline status
        print("\n--- Getting pipeline status for 'SWE_Lead' ---")
        status = rec_tool.execute(operation="get_pipeline_status", candidate_id="any", job_id="SWE_Lead") # candidate_id is not used for get_pipeline_status
        print(json.dumps(status, indent=2))

        # 4. Generate summary report
        print("\n--- Generating summary report for all jobs ---")
        summary_report = rec_tool.execute(operation="generate_report", candidate_id="any", report_type="summary")
        print(summary_report["report"])

        # 5. Generate detailed report for a specific job
        print("\n--- Generating detailed report for 'SWE_Lead' ---")
        detailed_report = rec_tool.execute(operation="generate_report", candidate_id="any", job_id="SWE_Lead", report_type="detailed")
        print(detailed_report["report"])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")