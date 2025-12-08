import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RootCauseAnalysisSimulatorTool(BaseTool):
    """
    A tool that simulates root cause analysis for incidents, identifying
    underlying problems, contributing factors, and recommending solutions.
    """

    def __init__(self, tool_name: str = "RootCauseAnalysisSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.incidents_file = os.path.join(self.data_dir, "incident_records.json")
        self.reports_file = os.path.join(self.data_dir, "rca_reports.json")
        
        # Incident records: {incident_id: {description: ..., severity: ..., symptoms: []}}
        self.incident_records: Dict[str, Dict[str, Any]] = self._load_data(self.incidents_file, default={})
        # Analysis reports: {report_id: {incident_id: ..., root_cause: ..., contributing_factors: []}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates root cause analysis: identifies underlying problems, contributing factors, and recommends solutions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_incident", "analyze_incident", "get_analysis_report"]},
                "incident_id": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "symptoms": {"type": "array", "items": {"type": "string"}, "description": "List of observed symptoms."},
                "analysis_level": {"type": "string", "enum": ["basic", "detailed"], "default": "basic"},
                "report_id": {"type": "string", "description": "ID of the analysis report to retrieve."}
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

    def _save_incidents(self):
        with open(self.incidents_file, 'w') as f: json.dump(self.incident_records, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def create_incident(self, incident_id: str, description: str, severity: str, symptoms: List[str]) -> Dict[str, Any]:
        """Creates a new incident record."""
        if incident_id in self.incident_records: raise ValueError(f"Incident '{incident_id}' already exists.")
        
        new_incident = {
            "id": incident_id, "description": description, "severity": severity,
            "symptoms": symptoms, "status": "open",
            "created_at": datetime.now().isoformat()
        }
        self.incident_records[incident_id] = new_incident
        self._save_incidents()
        return new_incident

    def analyze_incident(self, incident_id: str, analysis_level: str = "basic") -> Dict[str, Any]:
        """Simulates root cause analysis for an incident."""
        incident = self.incident_records.get(incident_id)
        if not incident: raise ValueError(f"Incident '{incident_id}' not found. Create it first.")
        
        report_id = f"rca_report_{incident_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        root_cause = "unknown"
        contributing_factors = []
        recommended_actions = []

        # Rule-based RCA
        symptoms_lower = [s.lower() for s in incident["symptoms"]]
        
        if "high cpu" in symptoms_lower or "slow response" in symptoms_lower:
            if analysis_level == "detailed" and "database" in incident["description"].lower():
                root_cause = "database bottleneck"
                contributing_factors.append("inefficient queries")
                recommended_actions.append("Optimize database queries.")
            else:
                root_cause = "performance degradation"
                contributing_factors.append("increased load")
                recommended_actions.append("Scale up resources.")
        
        if "login failed" in symptoms_lower or "authentication error" in symptoms_lower:
            root_cause = "authentication system issue"
            contributing_factors.append("incorrect credentials")
            recommended_actions.append("Check user credentials and system logs.")
        
        if not root_cause: root_cause = "undetermined"
        
        report = {
            "id": report_id, "incident_id": incident_id, "analysis_level": analysis_level,
            "root_cause": root_cause, "contributing_factors": contributing_factors,
            "recommended_actions": recommended_actions,
            "analyzed_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated root cause analysis report."""
        report = self.analysis_reports.get(report_id)
        if not report: raise ValueError(f"Analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_incident":
            incident_id = kwargs.get('incident_id')
            description = kwargs.get('description')
            severity = kwargs.get('severity')
            symptoms = kwargs.get('symptoms')
            if not all([incident_id, description, severity, symptoms]):
                raise ValueError("Missing 'incident_id', 'description', 'severity', or 'symptoms' for 'create_incident' operation.")
            return self.create_incident(incident_id, description, severity, symptoms)
        elif operation == "analyze_incident":
            incident_id = kwargs.get('incident_id')
            if not incident_id:
                raise ValueError("Missing 'incident_id' for 'analyze_incident' operation.")
            return self.analyze_incident(incident_id, kwargs.get('analysis_level', 'basic'))
        elif operation == "get_analysis_report":
            report_id = kwargs.get('report_id')
            if not report_id:
                raise ValueError("Missing 'report_id' for 'get_analysis_report' operation.")
            return self.get_analysis_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RootCauseAnalysisSimulatorTool functionality...")
    temp_dir = "temp_rca_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rca_tool = RootCauseAnalysisSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create an incident
        print("\n--- Creating incident 'INC-001' ---")
        rca_tool.execute(operation="create_incident", incident_id="INC-001", description="Website is slow and users report login failures.", severity="high", symptoms=["high CPU", "slow response", "login failed"])
        print("Incident created.")

        # 2. Analyze the incident (detailed level)
        print("\n--- Analyzing incident 'INC-001' (detailed) ---")
        analysis_report = rca_tool.execute(operation="analyze_incident", incident_id="INC-001", analysis_level="detailed")
        print(json.dumps(analysis_report, indent=2))

        # 3. Get the analysis report
        print(f"\n--- Getting analysis report for '{analysis_report['id']}' ---")
        report_details = rca_tool.execute(operation="get_analysis_report", incident_id="any", report_id=analysis_report["id"]) # incident_id is not used for get_analysis_report
        print(json.dumps(report_details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")