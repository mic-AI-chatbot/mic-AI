import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated user schedule data
SIMULATED_SCHEDULE = {
    "appointments": [
        {"title": "Team Meeting", "start": datetime(2025, 11, 14, 10, 0), "end": datetime(2025, 11, 14, 11, 0)},
        {"title": "Lunch", "start": datetime(2025, 11, 14, 12, 0), "end": datetime(2025, 11, 14, 13, 0)}
    ],
    "tasks": [
        {"title": "Review PR", "deadline": datetime(2025, 11, 14, 17, 0), "priority": "high", "duration_minutes": 60, "scheduled_time": None},
        {"title": "Update Documentation", "deadline": datetime(2025, 11, 15, 17, 0), "priority": "medium", "duration_minutes": 90, "scheduled_time": None}
    ]
}

class MotionSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Motion's AI-powered planner,
    generating structured JSON responses for scheduling tasks and appointments.
    """

    def __init__(self, tool_name: str = "MotionSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Motion AI actions: scheduling tasks, appointments, and optimizing timelines."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt describing the scheduling action to perform."
                }
            },
            "required": ["prompt"]
        }

    def _parse_time_and_date(self, text: str) -> Optional[datetime]:
        """Simple parser for common date/time phrases."""
        now = datetime.now()
        if "tomorrow" in text:
            target_date = now + timedelta(days=1)
        elif "today" in text:
            target_date = now
        else:
            target_date = now # Default to today if no specific date mentioned

        time_match = re.search(r'at\s+(\d{1,2}(:\d{2})?\s*(am|pm)?)', text, re.IGNORECASE)
        if time_match:
            time_str = time_match.group(1)
            try:
                # Handle '10am', '10:30am', '2pm'
                if 'am' in time_str.lower() or 'pm' in time_str.lower():
                    return datetime.strptime(f"{target_date.strftime('%Y-%m-%d')} {time_str}", '%Y-%m-%d %I%M%p')
                else: # Assume 24-hour format if no am/pm
                    return datetime.strptime(f"{target_date.strftime('%Y-%m-%d')} {time_str}", '%Y-%m-%d %H:%M')
            except ValueError:
                pass # Fallback to just date if time parsing fails
        
        return target_date.replace(hour=9, minute=0, second=0, microsecond=0) # Default to 9 AM

    def _simulate_schedule_task(self, prompt: str) -> Dict:
        task_match = re.search(r'task\s+([\'\"]?)(.*?)\1(?:$|\s+by|\s+for)', prompt, re.IGNORECASE)
        task_name = task_match.group(2) if task_match else "New Task"
        
        deadline_match = re.search(r'by\s+([\'\"]?)(.*?)\1(?:$|\s+)', prompt, re.IGNORECASE)
        deadline_str = deadline_match.group(2) if deadline_match else "end of day"
        
        deadline = self._parse_time_and_date(deadline_str)
        
        # Simple scheduling logic: find first open 30-min slot after now
        scheduled_time = datetime.now() + timedelta(minutes=15)
        
        return {
            "action": "schedule_task",
            "task_name": task_name,
            "deadline": deadline.isoformat() if deadline else None,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "scheduled"
        }

    def _simulate_add_appointment(self, prompt: str) -> Dict:
        title_match = re.search(r'appointment\s+([\'\"]?)(.*?)\1(?:$|\s+tomorrow|\s+today|\s+at)', prompt, re.IGNORECASE)
        title = title_match.group(2) if title_match else "New Appointment"
        
        start_time = self._parse_time_and_date(prompt)
        end_time = start_time + timedelta(minutes=30)
        
        return {
            "action": "add_appointment",
            "title": title,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "status": "added"
        }

    def _simulate_optimize_day(self) -> Dict:
        # Very basic optimization: just list existing items
        optimized_plan = []
        for appt in SIMULATED_SCHEDULE["appointments"]:
            optimized_plan.append({"time": appt["start"].isoformat(), "event": appt["title"]})
        for task in SIMULATED_SCHEDULE["tasks"]:
            optimized_plan.append({"time": task["deadline"].isoformat(), "event": task["title"]})
        
        # Sort by time
        optimized_plan.sort(key=lambda x: x["time"])
        
        return {
            "action": "optimize_schedule",
            "optimized_plan": optimized_plan,
            "message": "This is a simulated optimized plan based on existing entries."
        }

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Motion simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Motion would be made ---
        # For now, we simulate the response.
        
        response_data = {}
        if "schedule task" in prompt_lower or "add task" in prompt_lower:
            response_data = self._simulate_schedule_task(prompt)
        elif "add appointment" in prompt_lower or "schedule meeting" in prompt_lower:
            response_data = self._simulate_add_appointment(prompt)
        elif "optimize my day" in prompt_lower or "optimize schedule" in prompt_lower:
            response_data = self._simulate_optimize_day()
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Motion AI for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Motion."
        return response_data

if __name__ == '__main__':
    print("Demonstrating MotionSimulatorTool functionality...")
    
    motion_sim = MotionSimulatorTool()
    
    try:
        # --- Scenario 1: Schedule a task ---
        print("\n--- Simulating: Schedule task 'Prepare Q4 Report' by Friday ---")
        prompt1 = "schedule task 'Prepare Q4 Report' by 2025-11-17"
        result1 = motion_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # --- Scenario 2: Add an appointment ---
        print("\n--- Simulating: Add appointment 'Dentist' tomorrow at 10:30am ---")
        prompt2 = "add appointment 'Dentist' tomorrow at 10:30am"
        result2 = motion_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # --- Scenario 3: Optimize the day ---
        print("\n--- Simulating: Optimize my day ---")
        prompt3 = "optimize my day"
        result3 = motion_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # --- Scenario 4: Generic query ---
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the best way to learn Python?"
        result4 = motion_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")