
import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SleepPatternAnalyzerSimulatorTool(BaseTool):
    """
    A tool that simulates a sleep pattern analyzer, allowing for adding sleep
    records, analyzing patterns, and generating reports with insights and suggestions.
    """

    def __init__(self, tool_name: str = "SleepPatternAnalyzerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.records_file = os.path.join(self.data_dir, "sleep_records.json")
        self.reports_file = os.path.join(self.data_dir, "sleep_analysis_reports.json")
        
        # Sleep records: {user_id: [{date: ..., sleep_duration_hours: ..., wake_up_time: ..., sleep_quality_score: ...}]}
        self.sleep_records: Dict[str, List[Dict[str, Any]]] = self._load_data(self.records_file, default={})
        # Analysis reports: {report_id: {user_id: ..., average_sleep_duration: ..., potential_issues: []}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sleep pattern analysis: add records, analyze patterns, and generate reports with insights."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_sleep_record", "analyze_sleep_patterns", "get_analysis_report"]},
                "user_id": {"type": "string"},
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "sleep_duration_hours": {"type": "number", "minimum": 0},
                "wake_up_time": {"type": "string", "description": "HH:MM (24-hour format)"},
                "sleep_quality_score": {"type": "integer", "minimum": 1, "maximum": 5},
                "period_days": {"type": "integer", "minimum": 1, "default": 7},
                "report_id": {"type": "string", "description": "ID of the analysis report to retrieve."}
            },
            "required": ["operation", "user_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_records(self):
        with open(self.records_file, 'w') as f: json.dump(self.sleep_records, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def add_sleep_record(self, user_id: str, date: str, sleep_duration_hours: float, wake_up_time: str, sleep_quality_score: int) -> Dict[str, Any]:
        """Adds a new sleep record for a user."""
        try: datetime.strptime(date, "%Y-%m-%d")
        except ValueError: raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        try: datetime.strptime(wake_up_time, "%H:%M")
        except ValueError: raise ValueError("Invalid wake_up_time format. Please use HH:MM (24-hour).")
        
        new_record = {
            "date": date, "sleep_duration_hours": sleep_duration_hours,
            "wake_up_time": wake_up_time, "sleep_quality_score": sleep_quality_score,
            "recorded_at": datetime.now().isoformat()
        }
        self.sleep_records.setdefault(user_id, []).append(new_record)
        self._save_records()
        return new_record

    def analyze_sleep_patterns(self, user_id: str, period_days: int = 7) -> Dict[str, Any]:
        """Analyzes sleep patterns for a user over a specified period."""
        records = self.sleep_records.get(user_id)
        if not records: return {"status": "info", "message": f"No sleep records found for user '{user_id}'."}
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        recent_records = [r for r in records if datetime.fromisoformat(r["date"]).date() >= start_date]
        if not recent_records: return {"status": "info", "message": f"No sleep records found for user '{user_id}' in the last {period_days} days."}

        total_duration = sum(r["sleep_duration_hours"] for r in recent_records)
        average_sleep_duration = round(total_duration / len(recent_records), 2)
        
        # Consistency of wake-up times
        wake_up_times = [datetime.strptime(r["wake_up_time"], "%H:%M").time() for r in recent_records]
        # Simple consistency: check if all wake-up times are within a 1-hour window
        consistent_wake_up = True
        if len(wake_up_times) > 1:
            min_time = min(wake_up_times)
            max_time = max(wake_up_times)
            if (datetime.combine(datetime.min, max_time) - datetime.combine(datetime.min, min_time)).total_seconds() > 3600:
                consistent_wake_up = False
        
        average_sleep_quality = round(sum(r["sleep_quality_score"] for r in recent_records) / len(recent_records), 2)
        
        potential_issues = []
        if average_sleep_duration < 7.0: potential_issues.append("Insufficient average sleep duration (less than 7 hours).")
        if not consistent_wake_up: potential_issues.append("Inconsistent wake-up times detected.")
        if average_sleep_quality < 3.0: potential_issues.append("Low average sleep quality.")
        
        report_id = f"sleep_report_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "user_id": user_id, "period_days": period_days,
            "average_sleep_duration_hours": average_sleep_duration,
            "consistent_wake_up_times": consistent_wake_up,
            "average_sleep_quality_score": average_sleep_quality,
            "potential_issues": potential_issues,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def get_analysis_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated sleep analysis report."""
        report = self.analysis_reports.get(report_id)
        if not report: raise ValueError(f"Sleep analysis report '{report_id}' not found.")
        return report

    def execute(self, operation: str, user_id: str, **kwargs: Any) -> Any:
        if operation == "add_sleep_record":
            return self.add_sleep_record(user_id, kwargs['date'], kwargs['sleep_duration_hours'], kwargs['wake_up_time'], kwargs['sleep_quality_score'])
        elif operation == "analyze_sleep_patterns":
            return self.analyze_sleep_patterns(user_id, kwargs.get('period_days', 7))
        elif operation == "get_analysis_report":
            return self.get_analysis_report(kwargs['report_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SleepPatternAnalyzerSimulatorTool functionality...")
    temp_dir = "temp_sleep_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = SleepPatternAnalyzerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add some sleep records for user_alice
        print("\n--- Adding sleep records for 'user_alice' ---")
        today = datetime.now().date()
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=6)).strftime("%Y-%m-%d"), sleep_duration_hours=7.5, wake_up_time="07:00", sleep_quality_score=4)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=5)).strftime("%Y-%m-%d"), sleep_duration_hours=6.0, wake_up_time="08:30", sleep_quality_score=3)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=4)).strftime("%Y-%m-%d"), sleep_duration_hours=8.0, wake_up_time="07:15", sleep_quality_score=5)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=3)).strftime("%Y-%m-%d"), sleep_duration_hours=6.5, wake_up_time="08:00", sleep_quality_score=3)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=2)).strftime("%Y-%m-%d"), sleep_duration_hours=7.0, wake_up_time="07:30", sleep_quality_score=4)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=(today - timedelta(days=1)).strftime("%Y-%m-%d"), sleep_duration_hours=5.5, wake_up_time="09:00", sleep_quality_score=2)
        analyzer_tool.execute(operation="add_sleep_record", user_id="user_alice", date=today.strftime("%Y-%m-%d"), sleep_duration_hours=7.0, wake_up_time="07:45", sleep_quality_score=4)
        print("Sleep records added.")

        # 2. Analyze sleep patterns for user_alice
        print("\n--- Analyzing sleep patterns for 'user_alice' over 7 days ---")
        analysis_report = analyzer_tool.execute(operation="analyze_sleep_patterns", user_id="user_alice", period_days=7)
        print(json.dumps(analysis_report, indent=2))

        # 3. Get analysis report
        print(f"\n--- Getting analysis report for '{analysis_report['id']}' ---")
        retrieved_report = analyzer_tool.execute(operation="get_analysis_report", user_id="any", report_id=analysis_report["id"]) # user_id is not used for get_analysis_report
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
