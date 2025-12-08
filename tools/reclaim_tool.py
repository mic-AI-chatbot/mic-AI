import logging
import json
import re
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simulated user calendar and task data
SIMULATED_CALENDAR = {
    "meetings": [
        {"title": "Team Standup", "start": datetime(2025, 11, 14, 9, 0), "end": datetime(2025, 11, 14, 9, 30)},
        {"title": "Client Demo", "start": datetime(2025, 11, 14, 14, 0), "end": datetime(2025, 11, 14, 15, 0)}
    ],
    "tasks": [
        {"title": "Review Code", "duration_minutes": 60, "scheduled_slot": None},
        {"title": "Prepare Report", "duration_minutes": 90, "scheduled_slot": None}
    ],
    "habits": [
        {"title": "Meditation", "duration_minutes": 15, "frequency": "daily", "scheduled_slots": []}
    ]
}

class ReclaimSimulatorTool(BaseTool):
    """
    A tool that simulates interactions with Reclaim.ai, an AI-powered scheduling
    assistant, for scheduling tasks, habits, and meetings.
    """

    def __init__(self, tool_name: str = "ReclaimSimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates Reclaim.ai: AI-powered scheduling for tasks, habits, and meetings to optimize your day."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The natural language prompt for Reclaim.ai (e.g., 'schedule task \"Prepare Q4 Report\" for 2 hours')."
                }
            },
            "required": ["prompt"]
        }

    def _find_available_slot(self, duration_minutes: int) -> Optional[Dict[str, datetime]]:
        """Simulates finding an available slot in the calendar."""
        now = datetime.now()
        search_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
        search_end = now.replace(hour=17, minute=0, second=0, microsecond=0) + timedelta(days=2) # Search next 2 days
        
        current_time = search_start
        while current_time < search_end:
            slot_end = current_time + timedelta(minutes=duration_minutes)
            is_free = True
            for meeting in SIMULATED_CALENDAR["meetings"]:
                if max(current_time, meeting["start"]) < min(slot_end, meeting["end"]):
                    is_free = False
                    break
            if is_free:
                return {"start": current_time, "end": slot_end}
            current_time += timedelta(minutes=15) # Check every 15 minutes
        return None

    def _simulate_schedule_task(self, prompt: str) -> Dict:
        task_match = re.search(r'task\s+([\'"]?)(.*?)\1(?:$|\s+for)', prompt, re.IGNORECASE)
        task_name = task_match.group(2) if task_match else "New Task"
        
        duration_match = re.search(r'for\s+(\d+)\s+hours?', prompt, re.IGNORECASE)
        duration_minutes = int(duration_match.group(1)) * 60 if duration_match else 60 # Default 60 min
        
        scheduled_slot = self._find_available_slot(duration_minutes)
        
        if scheduled_slot:
            SIMULATED_CALENDAR["tasks"].append({"title": task_name, "duration_minutes": duration_minutes, "scheduled_slot": scheduled_slot})
            SIMULATED_CALENDAR["meetings"].append({"title": task_name, "start": scheduled_slot["start"], "end": scheduled_slot["end"]}) # Block calendar
            return {
                "action": "schedule_task",
                "task_name": task_name,
                "duration_minutes": duration_minutes,
                "scheduled_slot": {"start": scheduled_slot["start"].isoformat(), "end": scheduled_slot["end"].isoformat()},
                "status": "scheduled"
            }
        else:
            return {"status": "error", "message": "Could not find an available slot for the task."}

    def _simulate_block_habit_time(self, prompt: str) -> Dict:
        habit_match = re.search(r'habit\s+([\'"]?)(.*?)\1(?:$|\s+daily|\s+for)', prompt, re.IGNORECASE)
        habit_name = habit_match.group(2) if habit_match else "New Habit"
        
        duration_match = re.search(r'for\s+(\d+)\s+minutes?', prompt, re.IGNORECASE)
        duration_minutes = int(duration_match.group(1)) if duration_match else 30 # Default 30 min
        
        frequency = "daily" if "daily" in prompt.lower() else "weekly"
        
        scheduled_slot = self._find_available_slot(duration_minutes)
        
        if scheduled_slot:
            SIMULATED_CALENDAR["habits"].append({"title": habit_name, "duration_minutes": duration_minutes, "frequency": frequency, "scheduled_slots": [scheduled_slot]})
            SIMULATED_CALENDAR["meetings"].append({"title": habit_name, "start": scheduled_slot["start"], "end": scheduled_slot["end"]}) # Block calendar
            return {
                "action": "block_habit_time",
                "habit_name": habit_name,
                "duration_minutes": duration_minutes,
                "frequency": frequency,
                "scheduled_slot": {"start": scheduled_slot["start"].isoformat(), "end": scheduled_slot["end"].isoformat()},
                "status": "blocked"
            }
        else:
            return {"status": "error", "message": "Could not find an available slot for the habit."}

    def _simulate_find_meeting_time(self, prompt: str) -> Dict:
        attendees_match = re.search(r'meeting with\s+([\'"]?)(.*?)\1(?:$|\s+tomorrow|\s+for)', prompt, re.IGNORECASE)
        attendees_str = attendees_match.group(2) if attendees_match else "Alice"
        attendees = [a.strip() for a in attendees_str.split(',')]
        
        duration_match = re.search(r'for\s+(\d+)\s+minutes?', prompt, re.IGNORECASE)
        duration_minutes = int(duration_match.group(1)) if duration_match else 60 # Default 60 min
        
        # For simplicity, we'll just use the general find_available_slot logic
        suggested_slot = self._find_available_slot(duration_minutes)
        
        if suggested_slot:
            return {
                "action": "find_meeting_time",
                "attendees": attendees,
                "duration_minutes": duration_minutes,
                "suggested_slot": {"start": suggested_slot["start"].isoformat(), "end": suggested_slot["end"].isoformat()},
                "status": "found_slot"
            }
        else:
            return {"status": "error", "message": "Could not find a common available slot for the meeting."}

    def execute(self, prompt: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Parses the prompt for keywords and routes to the appropriate Reclaim.ai simulation.
        """
        prompt_lower = prompt.lower()
        
        # --- This is where a real API call to Reclaim.ai would be made ---
        # For now, we simulate the response.
        
        response_data = {}

        if "schedule task" in prompt_lower or "add task" in prompt_lower:
            response_data = self._simulate_schedule_task(prompt)
        elif "block time for habit" in prompt_lower or "add habit" in prompt_lower:
            response_data = self._simulate_block_habit_time(prompt)
        elif "find time for meeting" in prompt_lower or "schedule meeting" in prompt_lower:
            response_data = self._simulate_find_meeting_time(prompt)
        else:
            response_data = {
                "action": "generic_response",
                "response_text": f"This is a generic simulated response from Reclaim.ai for the prompt: '{prompt}'"
            }
            
        response_data["disclaimer"] = "This is a simulated response and not a real interaction with Reclaim.ai."
        return response_data

if __name__ == '__main__':
    print("Demonstrating ReclaimSimulatorTool functionality...")
    
    reclaim_sim = ReclaimSimulatorTool()
    
    try:
        # 1. Schedule a task
        print("\n--- Simulating: Schedule task 'Prepare Q4 Report' for 2 hours ---")
        prompt1 = "schedule task 'Prepare Q4 Report' for 2 hours"
        result1 = reclaim_sim.execute(prompt=prompt1)
        print(json.dumps(result1, indent=2))

        # 2. Block time for a habit
        print("\n--- Simulating: Block time for 'meditation' habit daily for 30 minutes ---")
        prompt2 = "block time for 'meditation' habit daily for 30 minutes"
        result2 = reclaim_sim.execute(prompt=prompt2)
        print(json.dumps(result2, indent=2))

        # 3. Find time for a meeting
        print("\n--- Simulating: Find time for meeting with Alice tomorrow for 60 minutes ---")
        prompt3 = "find time for meeting with Alice tomorrow for 60 minutes"
        result3 = reclaim_sim.execute(prompt=prompt3)
        print(json.dumps(result3, indent=2))
        
        # 4. Generic query
        print("\n--- Simulating: Generic query ---")
        prompt4 = "What is the weather like?"
        result4 = reclaim_sim.execute(prompt=prompt4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")