import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated schedules and employees
schedules: Dict[str, Dict[str, Any]] = {}
employees: Dict[str, Dict[str, Any]] = {
    "emp_001": {"name": "Alice", "skills": ["cashier"], "availability": ["Mon", "Wed", "Fri"]},
    "emp_002": {"name": "Bob", "skills": ["stocker"], "availability": ["Tue", "Thu", "Sat"]},
    "emp_003": {"name": "Charlie", "skills": ["cashier", "stocker"], "availability": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]}
}

class WorkforceSchedulingTool(BaseTool):
    """
    A tool to simulate workforce scheduling, including creating, optimizing,
    and managing employee shifts and attendance.
    """
    def __init__(self, tool_name: str = "workforce_scheduling_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates workforce scheduling: create, optimize, assign shifts, track attendance, and list schedules."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_schedule', 'optimize_schedule', 'assign_shift', 'track_attendance', 'get_employee_schedule', 'list_schedules'."
                },
                "schedule_name": {"type": "string", "description": "The unique name for the schedule."},
                "start_date": {"type": "string", "description": "The start date of the schedule (YYYY-MM-DD)."},
                "end_date": {"type": "string", "description": "The end date of the schedule (YYYY-MM-DD)."},
                "required_roles": {
                    "type": "object",
                    "description": "Required roles per day (e.g., {'Monday': {'cashier': 2, 'stocker': 1}})."
                },
                "employee_id": {"type": "string", "description": "The ID of the employee."},
                "shift_date": {"type": "string", "description": "The date of the shift (YYYY-MM-DD)."},
                "shift_time": {"type": "string", "description": "The time of the shift (e.g., '09:00-17:00')."},
                "role": {"type": "string", "description": "The role for the shift (e.g., 'cashier')."},
                "attendance_status": {"type": "string", "description": "Attendance status ('present', 'absent', 'late')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            schedule_name = kwargs.get("schedule_name")
            employee_id = kwargs.get("employee_id")

            if action in ['create_schedule', 'optimize_schedule', 'assign_shift', 'get_employee_schedule'] and not schedule_name:
                raise ValueError(f"'schedule_name' is required for the '{action}' action.")
            if action in ['assign_shift', 'track_attendance', 'get_employee_schedule'] and not employee_id:
                raise ValueError(f"'employee_id' is required for the '{action}' action.")

            actions = {
                "create_schedule": self._create_schedule,
                "optimize_schedule": self._optimize_schedule,
                "assign_shift": self._assign_shift,
                "track_attendance": self._track_attendance,
                "get_employee_schedule": self._get_employee_schedule,
                "list_schedules": self._list_schedules,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WorkforceSchedulingTool: {e}")
            return {"error": str(e)}

    def _create_schedule(self, schedule_name: str, start_date: str, end_date: str, required_roles: Dict[str, Any], **kwargs) -> Dict:
        if not all([start_date, end_date, required_roles]):
            raise ValueError("'start_date', 'end_date', and 'required_roles' are required.")
        if schedule_name in schedules:
            raise ValueError(f"Schedule '{schedule_name}' already exists.")
            
        new_schedule = {
            "name": schedule_name,
            "start_date": start_date,
            "end_date": end_date,
            "required_roles": required_roles,
            "shifts": {}, # {date: {shift_time: {role: employee_id}}}
            "status": "created"
        }
        schedules[schedule_name] = new_schedule
        logger.info(f"Schedule '{schedule_name}' created.")
        return {"message": "Schedule created successfully.", "details": new_schedule}

    def _optimize_schedule(self, schedule_name: str, **kwargs) -> Dict:
        if schedule_name not in schedules:
            raise ValueError(f"Schedule '{schedule_name}' not found.")
            
        schedule = schedules[schedule_name]
        required_roles = schedule["required_roles"]
        
        # Simple optimization: assign available employees to required roles
        optimized_shifts = {}
        for day, roles_needed in required_roles.items():
            optimized_shifts[day] = {}
            for role, count in roles_needed.items():
                assigned_count = 0
                for emp_id, emp_details in employees.items():
                    if role in emp_details["skills"] and day in emp_details["availability"] and assigned_count < count:
                        # Simulate a fixed shift time for simplicity
                        shift_time = "09:00-17:00" 
                        if shift_time not in optimized_shifts[day]:
                            optimized_shifts[day][shift_time] = {}
                        optimized_shifts[day][shift_time][role] = emp_id
                        assigned_count += 1
        
        schedule["shifts"] = optimized_shifts
        schedule["status"] = "optimized"
        logger.info(f"Schedule '{schedule_name}' optimized.")
        return {"message": "Schedule optimized successfully.", "details": schedule}

    def _assign_shift(self, schedule_name: str, employee_id: str, shift_date: str, shift_time: str, role: str, **kwargs) -> Dict:
        if schedule_name not in schedules:
            raise ValueError(f"Schedule '{schedule_name}' not found.")
        if employee_id not in employees:
            raise ValueError(f"Employee '{employee_id}' not found.")
            
        schedule = schedules[schedule_name]
        if shift_date not in schedule["shifts"]:
            schedule["shifts"][shift_date] = {}
        if shift_time not in schedule["shifts"][shift_date]:
            schedule["shifts"][shift_date][shift_time] = {}
        
        schedule["shifts"][shift_date][shift_time][role] = employee_id
        logger.info(f"Employee '{employee_id}' assigned to {role} shift on {shift_date} {shift_time}.")
        return {"message": "Shift assigned successfully.", "schedule": schedule_name, "employee_id": employee_id}

    def _track_attendance(self, employee_id: str, shift_date: str, attendance_status: str, **kwargs) -> Dict:
        if employee_id not in employees:
            raise ValueError(f"Employee '{employee_id}' not found.")
        if attendance_status not in ["present", "absent", "late"]:
            raise ValueError(f"Invalid attendance status '{attendance_status}'.")
            
        # This is a simple simulation. In a real system, attendance would be linked to a specific shift.
        employees[employee_id]["attendance"] = employees[employee_id].get("attendance", {})
        employees[employee_id]["attendance"][shift_date] = attendance_status
        logger.info(f"Attendance for '{employee_id}' on {shift_date} marked as '{attendance_status}'.")
        return {"message": "Attendance tracked successfully.", "employee_id": employee_id, "date": shift_date, "status": attendance_status}

    def _get_employee_schedule(self, schedule_name: str, employee_id: str, **kwargs) -> Dict:
        if schedule_name not in schedules:
            raise ValueError(f"Schedule '{schedule_name}' not found.")
        if employee_id not in employees:
            raise ValueError(f"Employee '{employee_id}' not found.")
            
        employee_schedule = {}
        for date, shifts_on_day in schedules[schedule_name]["shifts"].items():
            for shift_time, roles_on_shift in shifts_on_day.items():
                for role, assigned_emp_id in roles_on_shift.items():
                    if assigned_emp_id == employee_id:
                        if date not in employee_schedule:
                            employee_schedule[date] = []
                        employee_schedule[date].append({"shift_time": shift_time, "role": role})
        
        return {"employee_id": employee_id, "schedule": employee_schedule}

    def _list_schedules(self, **kwargs) -> Dict:
        if not schedules:
            return {"message": "No schedules created yet."}
        return {"schedules": list(schedules.values())}