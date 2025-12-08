

import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import Counter

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LobbyingActivityTrackerTool(BaseTool):
    """
    A tool for tracking lobbying activities, recording expenditures, and generating reports.
    This tool provides a more realistic and robust implementation for managing lobbying data.
    """

    def __init__(self, tool_name: str = "LobbyingActivityTracker", data_dir: str = ".", **kwargs):
        """
        Initializes the LobbyingActivityTrackerTool.

        Args:
            tool_name: The name of the tool.
            data_dir: The directory to store lobbying data files.
        """
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.activities_file = os.path.join(self.data_dir, "lobbying_activities.json")
        self.reports_file = os.path.join(self.data_dir, "lobbying_reports.json")
        self.activities: Dict[str, Dict[str, Any]] = self._load_data(self.activities_file)
        self.reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file)

    @property
    def description(self) -> str:
        return "A tool to record, track, and report lobbying activities and expenditures."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The operation to perform.",
                    "enum": ["record_activity", "generate_report", "list_activities", "get_activity_details"]
                },
                "activity_id": {"type": "string", "description": "Unique ID for an activity."},
                "name": {"type": "string", "description": "Name of the lobbying activity."},
                "lobbyist_name": {"type": "string", "description": "Name of the lobbyist."},
                "topic": {"type": "string", "description": "Topic of the lobbying activity."},
                "date": {"type": "string", "description": "Date of the activity (YYYY-MM-DD)."},
                "expenditure": {"type": "number", "description": "Expenditure for the activity."},
                "report_id": {"type": "string", "description": "Unique ID for a report."},
                "start_date": {"type": "string", "description": "Start date for a report (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "End date for a report (YYYY-MM-DD)."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str) -> Dict[str, Dict[str, Any]]:
        """Loads data from a JSON file."""
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Starting with empty data.")
                    return {}
        return {}

    def _save_data(self, data: Dict, file_path: str) -> None:
        """Saves data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def record_activity(self, activity_id: str, name: str, lobbyist_name: str,
                        topic: str, date: str, expenditure: float) -> Dict[str, Any]:
        """Records a new lobbying activity."""
        if not all([activity_id, name, lobbyist_name, topic, date]) or expenditure < 0:
            raise ValueError("Activity ID, name, lobbyist name, topic, date, and non-negative expenditure are required.")
        if activity_id in self.activities:
            raise ValueError(f"Lobbying activity with ID '{activity_id}' already exists.")
        
        try:
            datetime.fromisoformat(date)
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD.")

        new_activity = {
            "activity_id": activity_id, "name": name, "lobbyist_name": lobbyist_name,
            "topic": topic, "date": date, "expenditure": expenditure,
            "recorded_at": datetime.now().isoformat()
        }
        self.activities[activity_id] = new_activity
        self._save_data(self.activities, self.activities_file)
        self.logger.info(f"Lobbying activity '{name}' ({activity_id}) recorded successfully.")
        return new_activity

    def generate_report(self, report_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generates a lobbying report for a specific time period."""
        if not all([report_id, start_date, end_date]):
            raise ValueError("Report ID, start date, and end date are required.")
        if report_id in self.reports:
            raise ValueError(f"Lobbying report with ID '{report_id}' already exists.")

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        activities_in_period = [
            act for act in self.activities.values() 
            if start <= datetime.fromisoformat(act["date"]) <= end
        ]

        total_expenditure = sum(act["expenditure"] for act in activities_in_period)
        lobbyist_counts = Counter(act["lobbyist_name"] for act in activities_in_period)
        topic_counts = Counter(act["topic"] for act in activities_in_period)

        report_content = {
            "report_id": report_id,
            "time_period": f"{start_date} to {end_date}",
            "total_expenditure": round(total_expenditure, 2),
            "total_activities": len(activities_in_period),
            "top_lobbyist": lobbyist_counts.most_common(1)[0][0] if lobbyist_counts else "N/A",
            "top_topic": topic_counts.most_common(1)[0][0] if topic_counts else "N/A",
            "generated_at": datetime.now().isoformat()
        }
        self.reports[report_id] = report_content
        self._save_data(self.reports, self.reports_file)
        self.logger.info(f"Lobbying report '{report_id}' generated for {start_date} to {end_date}.")
        return report_content

    def list_activities(self, lobbyist_name: Optional[str] = None, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists recorded lobbying activities, with optional filters."""
        filtered = list(self.activities.values())
        if lobbyist_name:
            filtered = [act for act in filtered if act.get("lobbyist_name") == lobbyist_name]
        if topic:
            filtered = [act for act in filtered if act.get("topic") == topic]
        
        self.logger.info(f"Listed {len(filtered)} lobbying activities.")
        return filtered

    def get_activity_details(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a specific lobbying activity."""
        return self.activities.get(activity_id)

    def execute(self, **kwargs: Any) -> Any:
        """Executes a specified operation."""
        operation = kwargs.get("operation")
        if not operation:
            raise ValueError("'operation' is a required parameter.")

        op_map = {
            "record_activity": self.record_activity,
            "generate_report": self.generate_report,
            "list_activities": self.list_activities,
            "get_activity_details": self.get_activity_details,
        }

        if operation not in op_map:
            raise ValueError(f"Unsupported operation: {operation}")

        # Filter kwargs for the specific operation
        import inspect
        sig = inspect.signature(op_map[operation])
        op_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
        
        return op_map[operation](**op_kwargs)

if __name__ == '__main__':
    print("Demonstrating LobbyingActivityTrackerTool functionality...")
    
    # Use a temporary directory for the demo
    temp_dir = "temp_lobbying_data"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    tracker_tool = LobbyingActivityTrackerTool(data_dir=temp_dir)
    
    # Clean up previous state for a fresh demo
    if os.path.exists(tracker_tool.activities_file):
        os.remove(tracker_tool.activities_file)
    if os.path.exists(tracker_tool.reports_file):
        os.remove(tracker_tool.reports_file)
    tracker_tool = LobbyingActivityTrackerTool(data_dir=temp_dir) # Re-initialize
    print(f"\nCleaned up data files in '{temp_dir}' for fresh demo.")

    try:
        # --- Record Activities ---
        print("\n--- Recording Activities ---")
        activity1 = tracker_tool.execute(
            operation="record_activity", activity_id="meet_jones", name="Meeting with Senator Jones",
            lobbyist_name="Alice Lobbyist", topic="Healthcare Reform", date="2023-10-26", expenditure=500.00
        )
        print(json.dumps(activity1, indent=2))
        
        activity2 = tracker_tool.execute(
            operation="record_activity", activity_id="donate_smith", name="Donation to Rep. Smith",
            lobbyist_name="Bob Lobbyist", topic="Environmental Policy", date="2023-11-15", expenditure=1000.00
        )
        print(json.dumps(activity2, indent=2))

        # --- Generate a real report ---
        print("\n--- Generating Report for Q4 2023 ---")
        report = tracker_tool.execute(
            operation="generate_report", report_id="Q4_2023_report", 
            start_date="2023-10-01", end_date="2023-12-31"
        )
        print(json.dumps(report, indent=2))

        # --- List Activities ---
        print("\n--- Listing all activities for 'Bob Lobbyist' ---")
        bob_activities = tracker_tool.execute(operation="list_activities", lobbyist_name="Bob Lobbyist")
        print(json.dumps(bob_activities, indent=2))

        # --- Get Details ---
        print(f"\n--- Getting details for '{activity1['activity_id']}' ---")
        details = tracker_tool.execute(operation="get_activity_details", activity_id=activity1['activity_id'])
        print(json.dumps(details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        # Clean up the temporary directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")

