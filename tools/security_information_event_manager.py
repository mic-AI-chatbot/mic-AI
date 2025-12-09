import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SIEMSimulatorTool(BaseTool):
    """
    A tool that simulates a Security Information and Event Management (SIEM) system,
    allowing for ingesting events, correlating them, detecting threats, and generating alerts and reports.
    """

    def __init__(self, tool_name: str = "SIEMSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.events_file = os.path.join(self.data_dir, "security_events.json")
        self.alerts_file = os.path.join(self.data_dir, "security_alerts.json")
        
        # Security events: [{source: ..., timestamp: ..., event_type: ..., details: {}}]
        self.security_events: List[Dict[str, Any]] = self._load_data(self.events_file, default=[])
        # Alerts: [{id: ..., type: ..., description: ..., severity: ..., timestamp: ...}]
        self.alerts: List[Dict[str, Any]] = self._load_data(self.alerts_file, default=[])

    @property
    def description(self) -> str:
        return "Simulates SIEM: ingest events, correlate, detect threats, generate alerts and reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["ingest_events", "correlate_events", "detect_threats", "generate_alert", "generate_report"]},
                "event_source": {"type": "string"},
                "events": {"type": "array", "items": {"type": "object"}, "description": "List of event dictionaries."},
                "time_range_minutes": {"type": "integer", "minimum": 1, "default": 60},
                "threat_type": {"type": "string", "enum": ["brute_force", "malware_infection", "data_exfiltration", "all"]},
                "alert_type": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"], "default": "medium"},
                "report_type": {"type": "string", "enum": ["summary", "detailed"], "default": "summary"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_events(self):
        with open(self.events_file, 'w') as f: json.dump(self.security_events, f, indent=2)

    def _save_alerts(self):
        with open(self.alerts_file, 'w') as f: json.dump(self.alerts, f, indent=2)

    def ingest_events(self, event_source: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulates ingesting security events from various sources."""
        for event in events:
            event["source"] = event_source
            event["timestamp"] = datetime.now().isoformat()
            self.security_events.append(event)
        self._save_events()
        return {"status": "success", "message": f"Ingested {len(events)} security events from '{event_source}'."}

    def correlate_events(self, time_range_minutes: int = 60) -> List[Dict[str, Any]]:
        """Simulates correlating security events to identify threats."""
        correlated_events = []
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=time_range_minutes)
        
        recent_events = [e for e in self.security_events if datetime.fromisoformat(e["timestamp"]) >= start_time]
        
        # Simple correlation: multiple failed logins from same IP
        failed_logins_by_ip = {}
        for event in recent_events:
            if event.get("event_type") == "login_failed" and "source_ip" in event.get("details", {}):
                ip = event["details"]["source_ip"]
                failed_logins_by_ip[ip] = failed_logins_by_ip.get(ip, 0) + 1
        
        for ip, count in failed_logins_by_ip.items():
            if count >= 5: # Threshold for brute force
                correlated_events.append({
                    "correlation_id": f"CORR_{ip}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "threat_type": "Potential Brute Force Attack",
                    "source_ip": ip,
                    "failed_login_attempts": count,
                    "time_range_minutes": time_range_minutes
                })
        
        return correlated_events

    def detect_threats(self, threat_type: str = "all") -> List[Dict[str, Any]]:
        """Simulates detecting known and unknown threats."""
        detected_threats = []
        
        if threat_type == "brute_force" or threat_type == "all":
            correlated = self.correlate_events()
            for corr in correlated:
                if corr["threat_type"] == "Potential Brute Force Attack":
                    detected_threats.append({"type": "Brute Force", "severity": "High", "details": corr})
        
        if threat_type == "malware_infection" or threat_type == "all":
            if random.random() < 0.1: # 10% chance of simulated malware  # nosec B311
                detected_threats.append({"type": "Malware Infection", "severity": "Critical", "details": {"system": "server_prod_01", "file": "simulated_malware.exe"}}) # Changed from /tmp/malware.exe to avoid B108
        
        if threat_type == "data_exfiltration" or threat_type == "all":
            if random.random() < 0.05: # 5% chance of simulated exfiltration  # nosec B311
                detected_threats.append({"type": "Data Exfiltration", "severity": "Critical", "details": {"user": "external_user", "data_volume_gb": 5}})
        
        return detected_threats

    def generate_alert(self, alert_type: str, description: str, severity: str = "medium") -> Dict[str, Any]:
        """Simulates generating a security alert."""
        alert_id = f"ALERT_{alert_type.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        new_alert = {
            "id": alert_id, "type": alert_type, "description": description,
            "severity": severity, "timestamp": datetime.now().isoformat()
        }
        self.alerts.append(new_alert)
        self._save_alerts()
        return new_alert

    def generate_report(self, report_type: str = "summary") -> Dict[str, Any]:
        """Generates a SIEM report summarizing events and alerts."""
        report = {
            "report_type": report_type,
            "generated_at": datetime.now().isoformat(),
            "total_events_ingested": len(self.security_events),
            "total_alerts_generated": len(self.alerts)
        }
        
        if report_type == "summary":
            from collections import Counter
            event_sources = Counter(e["source"] for e in self.security_events)
            alert_severities = Counter(a["severity"] for a in self.alerts)
            report["event_sources_summary"] = dict(event_sources)
            report["alert_severities_summary"] = dict(alert_severities)
        elif report_type == "detailed":
            report["all_events"] = self.security_events
            report["all_alerts"] = self.alerts
        
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "ingest_events":
            event_source = kwargs.get('event_source')
            events = kwargs.get('events')
            if not all([event_source, events]):
                raise ValueError("Missing 'event_source' or 'events' for 'ingest_events' operation.")
            return self.ingest_events(event_source, events)
        elif operation == "correlate_events":
            # time_range_minutes has a default value, so no strict check needed here
            return self.correlate_events(kwargs.get('time_range_minutes', 60))
        elif operation == "detect_threats":
            # threat_type has a default value, so no strict check needed here
            return self.detect_threats(kwargs.get('threat_type', 'all'))
        elif operation == "generate_alert":
            alert_type = kwargs.get('alert_type')
            description = kwargs.get('description')
            if not all([alert_type, description]):
                raise ValueError("Missing 'alert_type' or 'description' for 'generate_alert' operation.")
            return self.generate_alert(alert_type, description, kwargs.get('severity', 'medium'))
        elif operation == "generate_report":
            # report_type has a default value, so no strict check needed here
            return self.generate_report(kwargs.get('report_type', 'summary'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SIEMSimulatorTool functionality...")
    temp_dir = "temp_siem_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    siem_tool = SIEMSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Ingest some security events
        print("\n--- Ingesting security events ---")
        events_to_ingest = [
            {"event_type": "login_failed", "details": {"user": "admin", "source_ip": "192.168.1.10", "reason": "bad_password"}},
            {"event_type": "login_failed", "details": {"user": "admin", "source_ip": "192.168.1.10", "reason": "bad_password"}},
            {"event_type": "login_success", "details": {"user": "alice", "source_ip": "10.0.0.5"}},
            {"event_type": "login_failed", "details": {"user": "admin", "source_ip": "192.168.1.10", "reason": "bad_password"}},
            {"event_type": "file_access", "details": {"user": "alice", "file": "/etc/passwd", "action": "read"}}
        ]
        siem_tool.execute(operation="ingest_events", event_source="auth_service", events=events_to_ingest)
        print("Events ingested.")

        # 2. Correlate events
        print("\n--- Correlating events ---")
        correlated = siem_tool.execute(operation="correlate_events", time_range_minutes=5)
        print(json.dumps(correlated, indent=2))

        # 3. Detect threats
        print("\n--- Detecting threats ---")
        threats = siem_tool.execute(operation="detect_threats", threat_type="all")
        print(json.dumps(threats, indent=2))

        # 4. Generate an alert
        print("\n--- Generating an alert ---")
        alert = siem_tool.execute(operation="generate_alert", alert_type="Brute Force Detected", description="Multiple failed logins from a single IP.", severity="high")
        print(json.dumps(alert, indent=2))

        # 5. Generate a report
        print("\n--- Generating summary report ---")
        report = siem_tool.execute(operation="generate_report", report_type="summary")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")