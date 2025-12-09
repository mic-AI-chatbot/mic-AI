import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SelfHealingITSystemSimulatorTool(BaseTool):
    """
    A tool that simulates self-healing IT systems, allowing for defining systems,
    detecting anomalies, diagnosing issues, and automatically remediating problems.
    """

    def __init__(self, tool_name: str = "SelfHealingITSystemSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.systems_file = os.path.join(self.data_dir, "it_system_definitions.json")
        self.incidents_file = os.path.join(self.data_dir, "self_healing_incidents.json")
        
        # System definitions: {system_id: {name: ..., components: [], health_thresholds: {}}}
        self.system_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.systems_file, default={})
        # Incident records: {incident_id: {system_id: ..., anomaly_details: {}, root_cause: ..., status: ...}}
        self.incident_records: Dict[str, Dict[str, Any]] = self._load_data(self.incidents_file, default={})

    @property
    def description(self) -> str:
        return "Simulates self-healing IT systems: detect anomalies, diagnose issues, and automatically remediate problems."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_system", "detect_anomaly", "diagnose_issue", "remediate_problem"]},
                "system_id": {"type": "string"},
                "name": {"type": "string"},
                "components": {"type": "array", "items": {"type": "string"}},
                "health_thresholds": {"type": "object", "description": "e.g., {'cpu_usage': 0.8, 'error_rate': 0.05}"},
                "current_metrics": {"type": "object", "description": "e.g., {'cpu_usage': 0.9, 'error_rate': 0.02}"},
                "anomaly_details": {"type": "object", "description": "Details of the detected anomaly."},
                "incident_id": {"type": "string"}
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

    def _save_systems(self):
        with open(self.systems_file, 'w') as f: json.dump(self.system_definitions, f, indent=2)

    def _save_incidents(self):
        with open(self.incidents_file, 'w') as f: json.dump(self.incident_records, f, indent=2)

    def define_system(self, system_id: str, name: str, components: List[str], health_thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Defines a new IT system for self-healing."""
        if system_id in self.system_definitions: raise ValueError(f"System '{system_id}' already exists.")
        
        new_system = {
            "id": system_id, "name": name, "components": components,
            "health_thresholds": health_thresholds, "defined_at": datetime.now().isoformat()
        }
        self.system_definitions[system_id] = new_system
        self._save_systems()
        return new_system

    def detect_anomaly(self, system_id: str, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Detects anomalies by comparing current metrics against health thresholds."""
        system = self.system_definitions.get(system_id)
        if not system: raise ValueError(f"System '{system_id}' not found. Define it first.")
        
        anomalies = []
        for metric, threshold in system["health_thresholds"].items():
            current_value = current_metrics.get(metric)
            if current_value is not None and current_value > threshold:
                anomalies.append({"metric": metric, "current_value": current_value, "threshold": threshold})
        
        if anomalies:
            incident_id = f"INC_{system_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            return {"status": "anomaly_detected", "incident_id": incident_id, "system_id": system_id, "anomalies": anomalies}
        else:
            return {"status": "no_anomaly", "system_id": system_id, "message": "No anomalies detected."}

    def diagnose_issue(self, system_id: str, anomaly_details: Dict[str, Any]) -> Dict[str, Any]:
        """Diagnoses the root cause and recommends remediation for an anomaly."""
        system = self.system_definitions.get(system_id)
        if not system: raise ValueError(f"System '{system_id}' not found. Define it first.")
        
        incident_id = f"INC_{system_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        root_cause = "unknown"
        recommended_remediation = "Investigate manually."
        
        # Rule-based diagnosis
        for anomaly in anomaly_details.get("anomalies", []):
            if anomaly["metric"] == "cpu_usage" and anomaly["current_value"] > 0.9:
                root_cause = "high CPU utilization"
                recommended_remediation = "Scale up CPU resources or optimize application."
            elif anomaly["metric"] == "error_rate" and anomaly["current_value"] > 0.05:
                root_cause = "application errors"
                recommended_remediation = "Check application logs for errors and deploy hotfix."
        
        new_incident = {
            "id": incident_id, "system_id": system_id, "anomaly_details": anomaly_details,
            "root_cause": root_cause, "recommended_remediation": recommended_remediation,
            "status": "diagnosed", "diagnosed_at": datetime.now().isoformat()
        }
        self.incident_records[incident_id] = new_incident
        self._save_incidents()
        return new_incident

    def remediate_problem(self, incident_id: str) -> Dict[str, Any]:
        """Simulates applying the recommended remediation for an incident."""
        incident = self.incident_records.get(incident_id)
        if not incident: raise ValueError(f"Incident '{incident_id}' not found.")
        if incident["status"] != "diagnosed": raise ValueError(f"Incident '{incident_id}' not yet diagnosed.")
        
        incident["status"] = "remediated"
        incident["remediated_at"] = datetime.now().isoformat()
        self._save_incidents()
        return {"status": "success", "message": f"Simulated: Problem for incident '{incident_id}' remediated by '{incident['recommended_remediation']}'."}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_system":
            system_id = kwargs.get('system_id')
            name = kwargs.get('name')
            components = kwargs.get('components')
            health_thresholds = kwargs.get('health_thresholds')
            if not all([system_id, name, components, health_thresholds]):
                raise ValueError("Missing 'system_id', 'name', 'components', or 'health_thresholds' for 'define_system' operation.")
            return self.define_system(system_id, name, components, health_thresholds)
        elif operation == "detect_anomaly":
            system_id = kwargs.get('system_id')
            current_metrics = kwargs.get('current_metrics')
            if not all([system_id, current_metrics]):
                raise ValueError("Missing 'system_id' or 'current_metrics' for 'detect_anomaly' operation.")
            return self.detect_anomaly(system_id, current_metrics)
        elif operation == "diagnose_issue":
            system_id = kwargs.get('system_id')
            anomaly_details = kwargs.get('anomaly_details')
            if not all([system_id, anomaly_details]):
                raise ValueError("Missing 'system_id' or 'anomaly_details' for 'diagnose_issue' operation.")
            return self.diagnose_issue(system_id, anomaly_details)
        elif operation == "remediate_problem":
            incident_id = kwargs.get('incident_id')
            if not incident_id:
                raise ValueError("Missing 'incident_id' for 'remediate_problem' operation.")
            return self.remediate_problem(incident_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SelfHealingITSystemSimulatorTool functionality...")
    temp_dir = "temp_self_healing_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sh_tool = SelfHealingITSystemSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a system
        print("\n--- Defining system 'web_server_prod' ---")
        sh_tool.execute(operation="define_system", system_id="web_server_prod", name="Production Web Server",
                        components=["nginx", "php-fpm", "database_client"],
                        health_thresholds={"cpu_usage": 0.85, "error_rate": 0.01})
        print("System defined.")

        # 2. Detect an anomaly (high CPU)
        print("\n--- Detecting anomaly for 'web_server_prod' (high CPU) ---")
        anomaly_metrics = {"cpu_usage": 0.92, "error_rate": 0.005}
        anomaly_detection_result = sh_tool.execute(operation="detect_anomaly", system_id="web_server_prod", current_metrics=anomaly_metrics)
        print(json.dumps(anomaly_detection_result, indent=2))

        # 3. Diagnose the issue
        if anomaly_detection_result["status"] == "anomaly_detected":
            incident_id = anomaly_detection_result["incident_id"]
            print(f"\n--- Diagnosing issue for incident '{incident_id}' ---")
            diagnosis_result = sh_tool.execute(operation="diagnose_issue", system_id="web_server_prod", anomaly_details=anomaly_detection_result)
            print(json.dumps(diagnosis_result, indent=2))

            # 4. Remediate the problem
            print(f"\n--- Remediating problem for incident '{incident_id}' ---")
            remediation_result = sh_tool.execute(operation="remediate_problem", system_id="any", incident_id=incident_id) # system_id is not used for remediate_problem
            print(json.dumps(remediation_result, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")