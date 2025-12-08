import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CSR_INITIATIVES_FILE = Path("csr_initiatives.json")

class CSRManager:
    """Manages CSR initiatives, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CSR_INITIATIVES_FILE):
        if cls._instance is None:
            cls._instance = super(CSRManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.initiatives: Dict[str, Any] = cls._instance._load_initiatives()
        return cls._instance

    def _load_initiatives(self) -> Dict[str, Any]:
        """Loads CSR initiative information from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty initiatives.")
                return {}
            except Exception as e:
                logger.error(f"Error loading initiatives from {self.file_path}: {e}")
                return {}
        return {}

    def _save_initiatives(self) -> None:
        """Saves CSR initiative information to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.initiatives, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving initiatives to {self.file_path}: {e}")

    def create_initiative(self, initiative_name: str, focus_area: str, budget: float, start_date: str, end_date: str) -> bool:
        if initiative_name in self.initiatives:
            return False
        self.initiatives[initiative_name] = {
            "focus_area": focus_area,
            "budget": budget,
            "start_date": start_date,
            "end_date": end_date,
            "status": "planned",
            "impact_metrics": {},
            "created_at": datetime.now().isoformat() + "Z",
            "last_updated_at": datetime.now().isoformat() + "Z"
        }
        self._save_initiatives()
        return True

    def get_initiative(self, initiative_name: str) -> Optional[Dict[str, Any]]:
        return self.initiatives.get(initiative_name)

    def list_initiatives(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if not status:
            return [{"name": name, "focus_area": details['focus_area'], "status": details['status'], "budget": details['budget'], "start_date": details['start_date'], "end_date": details['end_date']} for name, details in self.initiatives.items()]
        
        filtered_list = []
        for name, details in self.initiatives.items():
            if details['status'] == status:
                filtered_list.append({"name": name, "focus_area": details['focus_area'], "status": details['status'], "budget": details['budget'], "start_date": details['start_date'], "end_date": details['end_date']})
        return filtered_list

    def track_impact(self, initiative_name: str, metric_name: str, value: float) -> bool:
        if initiative_name not in self.initiatives:
            return False
        
        self.initiatives[initiative_name]["impact_metrics"][metric_name] = value
        self.initiatives[initiative_name]["last_updated_at"] = datetime.now().isoformat() + "Z"
        self._save_initiatives()
        return True

csr_manager = CSRManager()

class CreateCSRInitiativeTool(BaseTool):
    """Creates a new Corporate Social Responsibility (CSR) initiative."""
    def __init__(self, tool_name="create_csr_initiative"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new Corporate Social Responsibility (CSR) initiative with a specified name, focus area, budget, and timeline."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "initiative_name": {"type": "string", "description": "A unique name for the CSR initiative."},
                "focus_area": {"type": "string", "description": "The primary focus area of the initiative.", "enum": ["environmental_sustainability", "community_development", "ethical_labor_practices", "philanthropy"]},
                "budget": {"type": "number", "description": "The allocated budget for the initiative."},
                "start_date": {"type": "string", "description": "The start date of the initiative (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "The end date of the initiative (YYYY-MM-DD)."}
            },
            "required": ["initiative_name", "focus_area", "budget", "start_date", "end_date"]
        }

    def execute(self, initiative_name: str, focus_area: str, budget: float, start_date: str, end_date: str, **kwargs: Any) -> str:
        success = csr_manager.create_initiative(initiative_name, focus_area, budget, start_date, end_date)
        if success:
            report = {"message": f"CSR Initiative '{initiative_name}' created successfully. Status: planned."}
        else:
            report = {"error": f"CSR Initiative '{initiative_name}' already exists. Please choose a unique name."}
        return json.dumps(report, indent=2)

class TrackCSRImpactTool(BaseTool):
    """Tracks and updates impact metrics for a specific CSR initiative."""
    def __init__(self, tool_name="track_csr_impact"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tracks and updates impact metrics for a specific Corporate Social Responsibility (CSR) initiative."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "initiative_name": {"type": "string", "description": "The name of the CSR initiative to track."},
                "metric_name": {"type": "string", "description": "The name of the impact metric to update (e.g., 'trees_planted', 'community_members_reached', 'carbon_emissions_reduced')."},
                "value": {"type": "number", "description": "The value of the impact metric."}
            },
            "required": ["initiative_name", "metric_name", "value"]
        }

    def execute(self, initiative_name: str, metric_name: str, value: float, **kwargs: Any) -> str:
        initiative = csr_manager.get_initiative(initiative_name)
        if not initiative:
            return json.dumps({"error": f"CSR Initiative '{initiative_name}' not found. Please create it first."})
        
        success = csr_manager.track_impact(initiative_name, metric_name, value)
        if success:
            report = {"message": f"Impact metric '{metric_name}' for initiative '{initiative_name}' updated to {value}."}
        else:
            report = {"error": f"Failed to update impact metric for initiative '{initiative_name}'. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class GetCSRInitiativeDetailsTool(BaseTool):
    """Retrieves details of a specific CSR initiative."""
    def __init__(self, tool_name="get_csr_initiative_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves details of a specific Corporate Social Responsibility (CSR) initiative, including its focus area, budget, timeline, and impact metrics."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"initiative_name": {"type": "string", "description": "The name of the CSR initiative to retrieve details for."}},
            "required": ["initiative_name"]
        }

    def execute(self, initiative_name: str, **kwargs: Any) -> str:
        initiative = csr_manager.get_initiative(initiative_name)
        if not initiative:
            return json.dumps({"error": f"CSR Initiative '{initiative_name}' not found."})
            
        return json.dumps(initiative, indent=2)

class ListCSRInitiativesTool(BaseTool):
    """Lists all CSR initiatives."""
    def __init__(self, tool_name="list_csr_initiatives"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all Corporate Social Responsibility (CSR) initiatives, showing their name, focus area, status, and budget."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Optional: Filter initiatives by status.", "enum": ["planned", "in_progress", "completed", "cancelled"], "default": None}
            },
            "required": []
        }

    def execute(self, status: Optional[str] = None, **kwargs: Any) -> str:
        initiatives = csr_manager.list_initiatives(status)
        if not initiatives:
            return json.dumps({"message": "No CSR initiatives found matching the criteria."})
        
        return json.dumps({"total_initiatives": len(initiatives), "initiatives": initiatives}, indent=2)

class GenerateCSRReportTool(BaseTool):
    """Generates a summary report of a CSR initiative's impact."""
    def __init__(self, tool_name="generate_csr_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a summary report of a Corporate Social Responsibility (CSR) initiative's impact, including key metrics and a narrative summary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"initiative_name": {"type": "string", "description": "The name of the CSR initiative to generate a report for."}},
            "required": ["initiative_name"]
        }

    def execute(self, initiative_name: str, **kwargs: Any) -> str:
        initiative = csr_manager.get_initiative(initiative_name)
        if not initiative:
            return json.dumps({"error": f"CSR Initiative '{initiative_name}' not found."})
        
        report_summary = f"CSR Initiative Report: {initiative_name}\n"
        report_summary += f"Focus Area: {initiative['focus_area']}\n"
        report_summary += f"Status: {initiative['status']}\n"
        report_summary += f"Budget: ${initiative['budget']:.2f}\n"
        report_summary += f"Timeline: {initiative['start_date']} to {initiative['end_date']}\n"
        report_summary += "\nImpact Metrics:\n"
        if initiative["impact_metrics"]:
            for metric, value in initiative["impact_metrics"].items():
                report_summary += f"- {metric}: {value}\n"
        else:
            report_summary += "No impact metrics tracked yet.\n"
        
        report_summary += "\nNarrative Summary: This initiative aims to contribute positively to its focus area. Further analysis of metrics will provide deeper insights into its success."

        return json.dumps({"initiative_name": initiative_name, "report_summary": report_summary}, indent=2)