import logging
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class Schedule:
    """Represents a single schedule with tasks, resources, constraints, and assignments."""
    def __init__(self, schedule_id: str, tasks: List[Dict[str, Any]], resources: List[str], constraints: List[str]):
        self.schedule_id = schedule_id
        self.tasks = tasks # Each task: {"task_id": "T1", "duration": 2, "required_resource": "R1"}
        self.resources = resources
        self.constraints = constraints
        self.assignments: List[Dict[str, Any]] = [] # Each assignment: {"task_id": "T1", "resource": "R1", "start_time_unit": 0, "end_time_unit": 2}
        self.status = "created" # created, optimized

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "tasks": self.tasks,
            "resources": self.resources,
            "constraints": self.constraints,
            "assignments": self.assignments,
            "status": self.status
        }

class Scheduler:
    """Generates and optimizes schedules using simple heuristics."""
    def generate_initial_schedule(self, tasks: List[Dict[str, Any]], resources: List[str], constraints: List[str]) -> List[Dict[str, Any]]:
        assignments = []
        # Tracks when each resource becomes free. Using time units (e.g., hours).
        resource_availability = {res: 0 for res in resources} 

        # Simple greedy assignment: assign tasks to the first available resource that meets requirements
        # Sort tasks by duration to prioritize longer tasks, or by some other heuristic
        sorted_tasks = sorted(tasks, key=lambda x: x.get("duration", 0), reverse=True)

        for task in sorted_tasks:
            assigned = False
            # Find a resource that can handle this task and is available soonest
            best_resource = None
            earliest_available_time = float('inf')

            for res in resources:
                if task["required_resource"] == res:
                    if resource_availability[res] < earliest_available_time:
                        earliest_available_time = resource_availability[res]
                        best_resource = res
            
            if best_resource:
                start_time = earliest_available_time
                end_time = start_time + task["duration"]
                assignments.append({
                    "task_id": task["task_id"],
                    "resource": best_resource,
                    "start_time_unit": start_time,
                    "end_time_unit": end_time
                })
                resource_availability[best_resource] = end_time
                assigned = True
            
            if not assigned:
                logging.warning(f"Task {task['task_id']} could not be assigned to any available resource.")
        return assignments

    def optimize_schedule(self, schedule: Schedule, optimization_goals: List[str]) -> List[Dict[str, Any]]:
        # For simulation, we'll just re-shuffle tasks and re-assign them for "optimization".
        # A real optimizer would use complex algorithms (e.g., genetic algorithms, simulated annealing, constraint programming)
        # to minimize cost, maximize resource utilization, etc., based on the goals.
        
        # Example of a simple optimization heuristic: try to minimize total duration by re-sorting tasks
        if "minimize_total_duration" in optimization_goals:
            # Sort tasks by shortest duration first to try and fit more tasks earlier
            sorted_tasks = sorted(schedule.tasks, key=lambda x: x.get("duration", 0))
        else:
            # Default: random shuffle
            sorted_tasks = list(schedule.tasks)
            random.shuffle(sorted_tasks)

        optimized_assignments = self.generate_initial_schedule(sorted_tasks, schedule.resources, schedule.constraints)
        return optimized_assignments

class ScheduleManager:
    """Manages all created schedules, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScheduleManager, cls).__new__(cls)
            cls._instance.schedules: Dict[str, Schedule] = {}
        return cls._instance

    def create_schedule(self, schedule_id: str, tasks: List[Dict[str, Any]], resources: List[str], constraints: List[str]) -> Schedule:
        schedule = Schedule(schedule_id, tasks, resources, constraints)
        self.schedules[schedule_id] = schedule
        return schedule

    def get_schedule(self, schedule_id: str) -> Schedule:
        return self.schedules.get(schedule_id)

schedule_manager = ScheduleManager()
scheduler = Scheduler()

class CreateScheduleTool(BaseTool):
    """Creates a new schedule based on tasks, resources, and constraints."""
    def __init__(self, tool_name="create_schedule"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new schedule based on a list of tasks, available resources, and defined constraints, and generates an initial assignment."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "description": "A unique identifier for the new schedule."},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task_id": {"type": "string"},
                            "duration": {"type": "integer", "description": "Duration of the task in time units (e.g., hours)."},
                            "required_resource": {"type": "string", "description": "The type or name of the resource required for the task."}
                        },
                        "required": ["task_id", "duration", "required_resource"]
                    },
                    "description": "A list of tasks, each with an ID, duration, and required resource."
                },
                "resources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of available resources (e.g., ['developer_A', 'server_B']). Each resource can only handle one task at a time."
                },
                "constraints": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of scheduling constraints (e.g., ['task_A_before_task_B', 'max_hours_per_day_developer_A: 8']). (Currently for documentation only)."
                }
            },
            "required": ["schedule_id", "tasks", "resources", "constraints"]
        }

    def execute(self, schedule_id: str, tasks: List[Dict[str, Any]], resources: List[str], constraints: List[str], **kwargs: Any) -> str:
        if schedule_id in schedule_manager.schedules:
            return json.dumps({"error": f"Schedule with ID '{schedule_id}' already exists."})
        
        schedule = schedule_manager.create_schedule(schedule_id, tasks, resources, constraints)
        schedule.assignments = scheduler.generate_initial_schedule(tasks, resources, constraints)
        
        report = {
            "message": f"Schedule '{schedule_id}' created and initial assignments generated.",
            "schedule_details": schedule.to_dict()
        }
        return json.dumps(report, indent=2)

class OptimizeScheduleTool(BaseTool):
    """Optimizes an existing schedule based on specified goals."""
    def __init__(self, tool_name="optimize_schedule"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Optimizes an existing schedule to improve efficiency, reduce conflicts, or meet specific objectives (e.g., 'minimize_total_duration')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "schedule_id": {"type": "string", "description": "The ID of the schedule to optimize."},
                "optimization_goals": {
                    "type": "array",
                    "items": {"type": "string", "enum": ["minimize_total_duration", "maximize_resource_utilization"]},
                    "description": "A list of optimization goals."
                }
            },
            "required": ["schedule_id", "optimization_goals"]
        }

    def execute(self, schedule_id: str, optimization_goals: List[str], **kwargs: Any) -> str:
        schedule = schedule_manager.get_schedule(schedule_id)
        if not schedule:
            return json.dumps({"error": f"Schedule with ID '{schedule_id}' not found."})
        
        schedule.assignments = scheduler.optimize_schedule(schedule, optimization_goals)
        schedule.status = "optimized"
        
        report = {
            "message": f"Schedule '{schedule_id}' optimized successfully for goals: {', '.join(optimization_goals)}.",
            "schedule_details": schedule.to_dict()
        }
        return json.dumps(report, indent=2)

class GetScheduleDetailsTool(BaseTool):
    """Retrieves the full details of a generated schedule."""
    def __init__(self, tool_name="get_schedule_details"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the full details of a generated schedule, including tasks, resources, constraints, and current assignments."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"schedule_id": {"type": "string", "description": "The ID of the schedule to retrieve."}},
            "required": ["schedule_id"]
        }

    def execute(self, schedule_id: str, **kwargs: Any) -> str:
        schedule = schedule_manager.get_schedule(schedule_id)
        if not schedule:
            return json.dumps({"error": f"Schedule with ID '{schedule_id}' not found."})
        
        return json.dumps(schedule.to_dict(), indent=2)