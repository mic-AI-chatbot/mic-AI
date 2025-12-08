import logging
import json
import sqlite3
import random
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

DB_FILE = "vulnerability_scanner.db"

class VulnerabilityDBManager:
    """Manages vulnerability reports in a SQLite database."""
    _instance = None

    def __new__(cls, db_file):
        if cls._instance is None:
            cls._instance = super(VulnerabilityDBManager, cls).__new__(cls)
            cls._instance.db_file = db_file
            cls._instance._create_table()
        return cls._instance

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _create_table(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reports (
                        report_id TEXT PRIMARY KEY,
                        image_name TEXT NOT NULL,
                        scan_timestamp TEXT NOT NULL,
                        status TEXT NOT NULL,
                        vulnerabilities TEXT, -- Stored as JSON string
                        summary TEXT
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database table creation error: {e}")

    def add_report(self, report_id: str, image_name: str, scan_timestamp: str, status: str, vulnerabilities: List[Dict[str, Any]], summary: str) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO reports (report_id, image_name, scan_timestamp, status, vulnerabilities, summary) VALUES (?, ?, ?, ?, ?, ?)",
                    (report_id, image_name, scan_timestamp, status, json.dumps(vulnerabilities), summary)
                )
                return True
            except sqlite3.IntegrityError: # Handles PRIMARY KEY constraint failure
                return False

    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reports WHERE report_id = ?", (report_id,))
            row = cursor.fetchone()
            if row:
                report = dict(row)
                report["vulnerabilities"] = json.loads(report["vulnerabilities"])
                return report
            return None

    def list_reports(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT report_id, image_name, status, scan_timestamp FROM reports ORDER BY scan_timestamp DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

vulnerability_db_manager = VulnerabilityDBManager(DB_FILE)

class ScanContainerImageTool(BaseTool):
    """Scans a container image for vulnerabilities and stores the report persistently."""
    def __init__(self, tool_name="scan_container_image"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Scans a container image for vulnerabilities (simulated) and stores the report persistently."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_name": {"type": "string", "description": "The name of the container image to scan (e.g., 'my-app:latest')."},
                "num_vulnerabilities_to_simulate": {"type": "integer", "description": "Number of vulnerabilities to simulate in the scan.", "default": 5}
            },
            "required": ["image_name"]
        }

    def execute(self, image_name: str, num_vulnerabilities_to_simulate: int = 5, **kwargs: Any) -> str:
        report_id = f"scan_{image_name.replace(':', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate vulnerabilities
        vulnerabilities = []
        for i in range(num_vulnerabilities_to_simulate):
            severity = random.choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"])  # nosec B311
            cve_id = f"CVE-{random.randint(2020, 2024)}-{random.randint(1000, 9999)}"  # nosec B311
            vulnerabilities.append({
                "cve_id": cve_id,
                "severity": severity,
                "description": f"Vulnerability {cve_id} found in package X version {random.randint(1,5)}.{random.randint(0,9)}.",  # nosec B311
                "recommended_fix": f"Update package X to latest version {random.randint(6,10)}.{random.randint(0,9)}."  # nosec B311
            })
        
        status = "completed"
        summary = f"Scan completed. Found {num_vulnerabilities_to_simulate} vulnerabilities."
        if num_vulnerabilities_to_simulate > 0:
            summary += f" {sum(1 for v in vulnerabilities if v['severity'] == 'CRITICAL')} critical, {sum(1 for v in vulnerabilities if v['severity'] == 'HIGH')} high."

        success = vulnerability_db_manager.add_report(report_id, image_name, datetime.now().isoformat() + "Z", status, vulnerabilities, summary)
        
        if success:
            report = {"message": f"Container image '{image_name}' scanned. Report ID: '{report_id}'.", "report_id": report_id, "summary": summary}
        else:
            report = {"error": f"Failed to record scan report for '{image_name}'. Report ID might already exist."}
        return json.dumps(report, indent=2)

class AnalyzeVulnerabilityReportTool(BaseTool):
    """Analyzes a vulnerability report to provide a summary of critical vulnerabilities and suggested remediations."""
    def __init__(self, tool_name="analyze_vulnerability_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a vulnerability report to provide a summary of critical vulnerabilities and suggested remediations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"report_id": {"type": "string", "description": "The ID of the vulnerability report to analyze."}},
            "required": ["report_id"]
        }

    def execute(self, report_id: str, **kwargs: Any) -> str:
        report = vulnerability_db_manager.get_report(report_id)
        if not report:
            return json.dumps({"error": f"Vulnerability report with ID '{report_id}' not found."})
        
        critical_vulnerabilities = [v for v in report["vulnerabilities"] if v["severity"] == "CRITICAL"]
        high_vulnerabilities = [v for v in report["vulnerabilities"] if v["severity"] == "HIGH"]

        remediations = []
        if critical_vulnerabilities:
            remediations.append("Immediate action required for critical vulnerabilities:")
            for v in critical_vulnerabilities:
                remediations.append(f"- {v['cve_id']}: {v['recommended_fix']}")
        if high_vulnerabilities:
            remediations.append("High priority action required for high vulnerabilities:")
            for v in high_vulnerabilities:
                remediations.append(f"- {v['cve_id']}: {v['recommended_fix']}")
        
        if not remediations:
            remediations.append("No critical or high vulnerabilities found. Continue monitoring.")

        return json.dumps({
            "report_id": report_id,
            "image_name": report["image_name"],
            "overall_status": report["status"],
            "summary": report["summary"],
            "critical_vulnerabilities_count": len(critical_vulnerabilities),
            "high_vulnerabilities_count": len(high_vulnerabilities),
            "remediation_suggestions": remediations
        }, indent=2)

class GetVulnerabilityReportTool(BaseTool):
    """Retrieves the full details of a specific vulnerability report."""
    def __init__(self, tool_name="get_vulnerability_report"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full details of a specific vulnerability report, including all identified vulnerabilities."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"report_id": {"type": "string", "description": "The ID of the vulnerability report to retrieve."}},
            "required": ["report_id"]
        }

    def execute(self, report_id: str, **kwargs: Any) -> str:
        report = vulnerability_db_manager.get_report(report_id)
        if not report:
            return json.dumps({"error": f"Vulnerability report with ID '{report_id}' not found."})
            
        return json.dumps(report, indent=2)

class ListVulnerabilityReportsTool(BaseTool):
    """Lists all stored vulnerability reports."""
    def __init__(self, tool_name="list_vulnerability_reports"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all stored vulnerability reports, showing their ID, image name, status, and scan timestamp."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        reports = vulnerability_db_manager.list_reports()
        if not reports:
            return json.dumps({"message": "No vulnerability reports found."})
        
        return json.dumps({"total_reports": len(reports), "vulnerability_reports": reports}, indent=2)