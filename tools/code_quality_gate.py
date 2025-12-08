import logging
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import ProjectQuality
from sqlalchemy.exc import IntegrityError

# Import code complexity analyzer tool
try:
    from .code_complexity_analyzer import AnalyzePythonCodeComplexityTool
    CODE_COMPLEXITY_TOOL_AVAILABLE = True
except ImportError:
    CODE_COMPLEXITY_TOOL_AVAILABLE = False
    logging.warning("AnalyzePythonCodeComplexityTool not found. Code quality checks will use simulated complexity.")

logger = logging.getLogger(__name__)

class SetQualityThresholdTool(BaseTool):
    """Sets the code quality threshold for a project in the persistent database."""
    def __init__(self, tool_name="set_quality_threshold"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Sets a numerical code quality threshold (0-100%) for a specified project, against which future quality checks will be evaluated."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "The name of the project to set the threshold for."},
                "threshold": {"type": "number", "description": "The code quality threshold as a percentage (0-100)."}
            },
            "required": ["project_name", "threshold"]
        }

    def execute(self, project_name: str, threshold: float, **kwargs: Any) -> str:
        if not (0 <= threshold <= 100):
            return json.dumps({"error": "Threshold must be between 0 and 100."})
            
        db = next(get_db())
        try:
            project = db.query(ProjectQuality).filter(ProjectQuality.project_name == project_name).first()
            now = datetime.now().isoformat() + "Z"
            if project:
                project.quality_threshold = threshold
                project.created_at = now # Update created_at to reflect last modification
                db.commit()
                db.refresh(project)
            else:
                new_project = ProjectQuality(
                    project_name=project_name,
                    quality_threshold=threshold,
                    created_at=now
                )
                db.add(new_project)
                db.commit()
                db.refresh(new_project)
            report = {"message": f"Quality threshold for project '{project_name}' set to {threshold}%."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error setting quality threshold: {e}")
            report = {"error": f"Failed to set quality threshold for project '{project_name}'. An unexpected error occurred: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class RunQualityCheckTool(BaseTool):
    """Runs a code quality check for a project, integrating with code complexity analysis."""
    def __init__(self, tool_name="run_quality_check"):
        super().__init__(tool_name=tool_name)
        self.complexity_analyzer = AnalyzePythonCodeComplexityTool()

    @property
    def description(self) -> str:
        return "Runs a code quality check for a specified project, integrating with code complexity analysis, and returns the quality score and compliance status against the set threshold."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "The name of the project to run the quality check for."},
                "code_file_path": {"type": "string", "description": "The absolute path to the main code file or a representative file for quality analysis."}
            },
            "required": ["project_name", "code_file_path"]
        }

    def execute(self, project_name: str, code_file_path: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            project = db.query(ProjectQuality).filter(ProjectQuality.project_name == project_name).first()
            if not project:
                return json.dumps({"error": f"Project '{project_name}' not found or no quality threshold set. Please set a threshold first."})
            
            threshold = project.quality_threshold
            
            # Integrate with code complexity analysis
            complexity_report_json = self.complexity_analyzer.execute(file_path=code_file_path)
            complexity_report = json.loads(complexity_report_json)

            if "error" in complexity_report:
                return json.dumps({"error": f"Failed to run complexity analysis: {complexity_report['error']}"})

            # Calculate a simulated quality score based on complexity and other factors
            overall_cc = complexity_report["summary"]["overall_cyclomatic_complexity"]
            estimated_bugs = complexity_report["summary"]["estimated_halstead_bugs"]

            # Simple heuristic for quality score: lower complexity, fewer bugs = higher score
            # Max score 100, min 0. Adjust weights as needed.
            quality_score = 100 - (overall_cc * 1.5) - (estimated_bugs * 50) # Example weights
            quality_score = max(0, min(100, quality_score + random.randint(-5, 5))) # Add some randomness  # nosec B311
            
            compliance_status = "compliant" if quality_score >= threshold else "non-compliant"
            
            project.last_quality_score = quality_score
            project.last_check_timestamp = datetime.now().isoformat() + "Z"
            db.commit()
            db.refresh(project)
            
            report = {
                "project_name": project_name,
                "quality_score": round(quality_score, 2),
                "threshold": threshold,
                "compliance_status": compliance_status,
                "complexity_metrics_summary": complexity_report["summary"],
                "message": f"Code quality check for '{project_name}' completed. Score: {quality_score:.2f}%, Threshold: {threshold}%."
            }
        except Exception as e:
            db.rollback()
            logger.error(f"Error running quality check: {e}")
            report = {"error": f"Failed to run quality check: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class GetProjectQualityStatusTool(BaseTool):
    """Retrieves the current quality status of a project."""
    def __init__(self, tool_name="get_project_quality_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current quality status of a project, including its set threshold, last quality score, and compliance status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"project_name": {"type": "string", "description": "The name of the project to retrieve quality status for."}},
            "required": ["project_name"]
        }

    def execute(self, project_name: str, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            project = db.query(ProjectQuality).filter(ProjectQuality.project_name == project_name).first()
            if not project:
                return json.dumps({"error": f"Project '{project_name}' not found."})
            
            compliance_status = "N/A"
            if project.last_quality_score is not None:
                compliance_status = "compliant" if project.last_quality_score >= project.quality_threshold else "non-compliant"

            report = {
                "project_name": project_name,
                "quality_threshold": project.quality_threshold,
                "last_quality_score": project.last_quality_score,
                "last_check_timestamp": project.last_check_timestamp,
                "compliance_status": compliance_status
            }
        except Exception as e:
            logger.error(f"Error getting project quality status: {e}")
            report = {"error": f"Failed to get project quality status: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)
