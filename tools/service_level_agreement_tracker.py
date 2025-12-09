import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SLATrackerSimulatorTool(BaseTool):
    """
    A tool that simulates Service Level Agreement (SLA) tracking, allowing for
    defining SLAs, tracking performance against them, and generating reports.
    """

    def __init__(self, tool_name: str = "SLATrackerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.slas_file = os.path.join(self.data_dir, "sla_definitions.json")
        self.performance_file = os.path.join(self.data_dir, "sla_performance_records.json")
        
        # SLA definitions: {sla_id: {service_name: ..., target_uptime_percent: ..., target_response_time_ms: ...}}
        self.sla_definitions: Dict[str, Dict[str, Any]] = self._load_data(self.slas_file, default={})
        # Performance records: {sla_id: [{timestamp: ..., actual_uptime_percent: ..., actual_response_time_ms: ...}]}
        self.performance_records: Dict[str, List[Dict[str, Any]]] = self._load_data(self.performance_file, default={})

    @property
    def description(self) -> str:
        return "Simulates SLA tracking: define SLAs, track performance, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_sla", "track_performance", "generate_report", "list_slas"]},
                "sla_id": {"type": "string"},
                "service_name": {"type": "string"},
                "target_uptime_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "target_response_time_ms": {"type": "integer", "minimum": 1},
                "actual_uptime_percent": {"type": "number", "minimum": 0, "maximum": 100},
                "actual_response_time_ms": {"type": "integer", "minimum": 1}
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

    def _save_slas(self):
        with open(self.slas_file, 'w') as f: json.dump(self.sla_definitions, f, indent=2)

    def _save_performance(self):
        with open(self.performance_file, 'w') as f: json.dump(self.performance_records, f, indent=2)

    def define_sla(self, sla_id: str, service_name: str, target_uptime_percent: float, target_response_time_ms: int) -> Dict[str, Any]:
        """Defines a new Service Level Agreement (SLA)."""
        if sla_id in self.sla_definitions: raise ValueError(f"SLA '{sla_id}' already exists.")
        
        new_sla = {
            "id": sla_id, "service_name": service_name,
            "target_uptime_percent": target_uptime_percent,
            "target_response_time_ms": target_response_time_ms,
            "defined_at": datetime.now().isoformat()
        }
        self.sla_definitions[sla_id] = new_sla
        self._save_slas()
        return new_sla

    def track_performance(self, sla_id: str, actual_uptime_percent: float, actual_response_time_ms: int) -> Dict[str, Any]:
        """Tracks service performance against an SLA."""
        if sla_id not in self.sla_definitions: raise ValueError(f"SLA '{sla_id}' not found. Define it first.")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "actual_uptime_percent": actual_uptime_percent,
            "actual_response_time_ms": actual_response_time_ms
        }
        self.performance_records.setdefault(sla_id, []).append(log_entry)
        self._save_performance()
        return {"status": "success", "message": f"Performance for SLA '{sla_id}' tracked."
}

    def generate_report(self, sla_id: str) -> Dict[str, Any]:
        """Generates a compliance report for a specific SLA."""
        sla = self.sla_definitions.get(sla_id)
        if not sla: raise ValueError(f"SLA '{sla_id}' not found.")
        
        performance_history = self.performance_records.get(sla_id, [])
        if not performance_history: return {"status": "info", "message": f"No performance data found for SLA '{sla_id}'."}
        
        uptime_compliant_count = 0
        response_time_compliant_count = 0
        
        for record in performance_history:
            if record["actual_uptime_percent"] >= sla["target_uptime_percent"]:
                uptime_compliant_count += 1
            if record["actual_response_time_ms"] <= sla["target_response_time_ms"]:
                response_time_compliant_count += 1
        
        total_records = len(performance_history)
        uptime_compliance_percent = round((uptime_compliant_count / total_records) * 100, 2)
        response_time_compliance_percent = round((response_time_compliant_count / total_records) * 100, 2)
        
        overall_compliance_status = "compliant"
        if uptime_compliance_percent < 99 or response_time_compliance_percent < 99: # Example threshold
            overall_compliance_status = "non-compliant"

        report_id = f"sla_report_{sla_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "sla_id": sla_id, "service_name": sla["service_name"],
            "target_uptime_percent": sla["target_uptime_percent"],
            "target_response_time_ms": sla["target_response_time_ms"],
            "uptime_compliance_percent": uptime_compliance_percent,
            "response_time_compliance_percent": response_time_compliance_percent,
            "overall_compliance_status": overall_compliance_status,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def list_slas(self) -> List[Dict[str, Any]]:
        """Lists all defined SLAs."""
        return list(self.sla_definitions.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "define_sla":
            sla_id = kwargs.get('sla_id')
            service_name = kwargs.get('service_name')
            target_uptime_percent = kwargs.get('target_uptime_percent')
            target_response_time_ms = kwargs.get('target_response_time_ms')
            if not all([sla_id, service_name, target_uptime_percent is not None, target_response_time_ms is not None]):
                raise ValueError("Missing 'sla_id', 'service_name', 'target_uptime_percent', or 'target_response_time_ms' for 'define_sla' operation.")
            return self.define_sla(sla_id, service_name, target_uptime_percent, target_response_time_ms)
        elif operation == "track_performance":
            sla_id = kwargs.get('sla_id')
            actual_uptime_percent = kwargs.get('actual_uptime_percent')
            actual_response_time_ms = kwargs.get('actual_response_time_ms')
            if not all([sla_id, actual_uptime_percent is not None, actual_response_time_ms is not None]):
                raise ValueError("Missing 'sla_id', 'actual_uptime_percent', or 'actual_response_time_ms' for 'track_performance' operation.")
            return self.track_performance(sla_id, actual_uptime_percent, actual_response_time_ms)
        elif operation == "generate_report":
            sla_id = kwargs.get('sla_id')
            if not sla_id:
                raise ValueError("Missing 'sla_id' for 'generate_report' operation.")
            return self.generate_report(sla_id)
        elif operation == "list_slas":
            # No additional kwargs required for list_slas
            return self.list_slas()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SLATrackerSimulatorTool functionality...")
    temp_dir = "temp_sla_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sla_tool = SLATrackerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define an SLA
        print("\n--- Defining SLA 'web_app_sla' ---")
        sla_tool.execute(operation="define_sla", sla_id="web_app_sla", service_name="WebApp Frontend", target_uptime_percent=99.9, target_response_time_ms=200)
        print("SLA defined.")

        # 2. Track performance (compliant)
        print("\n--- Tracking compliant performance for 'web_app_sla' ---")
        sla_tool.execute(operation="track_performance", sla_id="web_app_sla", actual_uptime_percent=99.95, actual_response_time_ms=150)
        sla_tool.execute(operation="track_performance", sla_id="web_app_sla", actual_uptime_percent=99.92, actual_response_time_ms=180)
        print("Compliant performance tracked.")

        # 3. Track performance (non-compliant)
        print("\n--- Tracking non-compliant performance for 'web_app_sla' ---")
        sla_tool.execute(operation="track_performance", sla_id="web_app_sla", actual_uptime_percent=99.8, actual_response_time_ms=250)
        print("Non-compliant performance tracked.")

        # 4. Generate a report
        print("\n--- Generating report for 'web_app_sla' ---")
        report = sla_tool.execute(operation="generate_report", sla_id="web_app_sla")
        print(json.dumps(report, indent=2))

        # 5. List all SLAs
        print("\n--- Listing all SLAs ---")
        all_slas = sla_tool.execute(operation="list_slas", sla_id="any") # sla_id is not used for list_slas
        print(json.dumps(all_slas, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")