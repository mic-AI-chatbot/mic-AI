import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalHealthMonitorTool(BaseTool):
    """
    A tool for personal health monitoring, providing health advice and
    tracking daily metrics like steps, sleep, and water intake.
    """

    def __init__(self, tool_name: str = "PersonalHealthMonitor", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.metrics_file = os.path.join(self.data_dir, "daily_health_metrics.json")
        # Daily metrics structure: {date: {steps: int, sleep_hours: float, water_liters: float}}
        self.daily_metrics: Dict[str, Dict[str, Any]] = self._load_data(self.metrics_file, default={})
        self.advice = [
            "Remember to drink plenty of water throughout the day.",
            "Try to get at least 30 minutes of exercise each day.",
            "A balanced diet is key to good health.",
            "Don't forget to get enough sleep. Aim for 7-9 hours per night.",
            "Take breaks from sitting and stretch regularly.",
            "Incorporate mindfulness or meditation into your routine for stress reduction.",
            "Eat a variety of fruits and vegetables to ensure you get all essential nutrients.",
            "Limit processed foods and sugary drinks for better overall health.",
            "Prioritize strength training exercises to build and maintain muscle mass.",
            "Spend time outdoors to boost your mood and get some Vitamin D."
        ]

    @property
    def description(self) -> str:
        return "Monitors personal health: provides advice, tracks daily metrics (steps, sleep, water)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["get_random_advice", "track_daily_metrics", "get_daily_metrics"]},
                "date": {"type": "string", "description": "The date for metrics (YYYY-MM-DD)."},
                "steps": {"type": "integer", "minimum": 0},
                "sleep_hours": {"type": "number", "minimum": 0},
                "water_liters": {"type": "number", "minimum": 0}
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

    def _save_data(self):
        with open(self.metrics_file, 'w') as f: json.dump(self.daily_metrics, f, indent=2)

    def get_random_advice(self) -> Dict[str, Any]:
        """Returns a random piece of health advice."""
        return {"status": "success", "advice": random.choice(self.advice)}  # nosec B311

    def track_daily_metrics(self, date: str, steps: Optional[int] = None, sleep_hours: Optional[float] = None, water_liters: Optional[float] = None) -> Dict[str, Any]:
        """Tracks daily health metrics and provides feedback."""
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

        if date not in self.daily_metrics:
            self.daily_metrics[date] = {}

        feedback = f"Metrics for {date} updated."
        if steps is not None:
            self.daily_metrics[date]["steps"] = steps
            feedback += f" Steps: {steps}."
            if steps < 8000: feedback += " Consider increasing your steps for better cardiovascular health."
        if sleep_hours is not None:
            self.daily_metrics[date]["sleep_hours"] = sleep_hours
            feedback += f" Sleep: {sleep_hours} hours."
            if sleep_hours < 7: feedback += " Aim for more sleep to improve recovery and cognitive function."
        if water_liters is not None:
            self.daily_metrics[date]["water_liters"] = water_liters
            feedback += f" Water: {water_liters} liters."
            if water_liters < 2: feedback += " Stay hydrated by drinking more water throughout the day."
        
        self._save_data()
        return {"status": "success", "message": feedback, "metrics": self.daily_metrics[date]}

    def get_daily_metrics(self, date: str) -> Dict[str, Any]:
        """Retrieves tracked health metrics for a specific date."""
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-%d.")
        
        metrics = self.daily_metrics.get(date)
        if not metrics:
            return {"status": "info", "message": f"No metrics found for date '{date}'."}
        return {"status": "success", "date": date, "metrics": metrics}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "get_random_advice":
            return self.get_random_advice()
        elif operation == "track_daily_metrics":
            return self.track_daily_metrics(kwargs['date'], kwargs.get('steps'), kwargs.get('sleep_hours'), kwargs.get('water_liters'))
        elif operation == "get_daily_metrics":
            return self.get_daily_metrics(kwargs['date'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalHealthMonitorTool functionality...")
    temp_dir = "temp_health_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    health_monitor = PersonalHealthMonitorTool(data_dir=temp_dir)
    
    try:
        # 1. Get some random advice
        print("\n--- Getting random health advice ---")
        advice = health_monitor.execute(operation="get_random_advice")
        print(json.dumps(advice, indent=2))

        # 2. Track metrics for today
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\n--- Tracking metrics for {today} ---")
        track_result1 = health_monitor.execute(operation="track_daily_metrics", date=today, steps=7500, sleep_hours=6.5, water_liters=1.8)
        print(json.dumps(track_result1, indent=2))

        # 3. Update metrics for today
        print(f"\n--- Updating metrics for {today} (more steps) ---")
        track_result2 = health_monitor.execute(operation="track_daily_metrics", date=today, steps=9000)
        print(json.dumps(track_result2, indent=2))

        # 4. Get metrics for today
        print(f"\n--- Getting metrics for {today} ---")
        metrics_today = health_monitor.execute(operation="get_daily_metrics", date=today)
        print(json.dumps(metrics_today, indent=2))

        # 5. Track metrics for tomorrow
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"\n--- Tracking metrics for {tomorrow} ---")
        track_result3 = health_monitor.execute(operation="track_daily_metrics", date=tomorrow, steps=12000, sleep_hours=8.0, water_liters=2.5)
        print(json.dumps(track_result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")