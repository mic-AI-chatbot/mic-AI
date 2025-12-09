import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated attendance records
# Structure: {employee_id: [{date: date, clock_in: datetime, clock_out: datetime}]}
attendance_records: Dict[str, List[Dict[str, Any]]] = {}

class TimeAttendanceTrackerTool(BaseTool):
    """
    A tool for simulating time and attendance tracking actions.
    """
    def __init__(self, tool_name: str = "time_attendance_tracker_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates time and attendance tracking: clocking in/out and generating reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string", 
                    "description": "The command to execute: 'clock_in', 'clock_out', 'get_employee_report', or 'get_summary_report'."
                },
                "employee_id": {"type": "string", "description": "The ID of the employee (required for clock_in, clock_out, get_employee_report)."},
                "target_date": {
                    "type": "string", 
                    "description": "The target date for the action (YYYY-MM-DD). Defaults to today.",
                    "default": str(date.today())
                }
            },
            "required": ["command"]
        }

    def execute(self, command: str, **kwargs: Any) -> str:
        try:
            employee_id = kwargs.get("employee_id")
            target_date_str = kwargs.get("target_date", str(date.today()))
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

            if command in ["clock_in", "clock_out", "get_employee_report"] and not employee_id:
                return f"Error: 'employee_id' is required for the '{command}' command."

            if command == "clock_in":
                return self._clock_in(employee_id, target_date)
            elif command == "clock_out":
                return self._clock_out(employee_id, target_date)
            elif command == "get_employee_report":
                return self._get_attendance_report(employee_id, target_date)
            elif command == "get_summary_report":
                return self._get_summary_report(target_date)
            else:
                return f"Error: Unknown command '{command}'. Available commands: clock_in, clock_out, get_employee_report, get_summary_report."
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            logger.error(f"An unexpected error occurred in TimeAttendanceTrackerTool: {e}")
            return f"An unexpected error occurred: {e}"

    def _clock_in(self, employee_id: str, target_date: date) -> str:
        logger.info(f"Attempting to clock in employee: {employee_id} on {target_date}")
        if employee_id not in attendance_records:
            attendance_records[employee_id] = []
        
        for record in attendance_records[employee_id]:
            if record["date"] == target_date and "clock_in" in record:
                raise ValueError(f"Employee '{employee_id}' already clocked in on {target_date}.")

        clock_in_time = datetime.now()
        attendance_records[employee_id].append({"date": target_date, "clock_in": clock_in_time})
        logger.info(f"Employee '{employee_id}' clocked in on {target_date}.")
        return f"Employee '{employee_id}' clocked in on {target_date} at {clock_in_time.strftime('%H:%M:%S')}."

    def _clock_out(self, employee_id: str, target_date: date) -> str:
        logger.info(f"Attempting to clock out employee: {employee_id} on {target_date}")
        if employee_id not in attendance_records:
            raise ValueError(f"Employee '{employee_id}' has no attendance records.")
        
        for record in reversed(attendance_records[employee_id]):
            if record["date"] == target_date and "clock_in" in record and "clock_out" not in record:
                clock_out_time = datetime.now()
                record["clock_out"] = clock_out_time
                logger.info(f"Employee '{employee_id}' clocked out on {target_date}.")
                
                duration = clock_out_time - record["clock_in"]
                return f"Employee '{employee_id}' clocked out on {target_date} at {clock_out_time.strftime('%H:%M:%S')}. Duration: {self._format_duration(duration)}."
        
        raise ValueError(f"Employee '{employee_id}' is not clocked in on {target_date} or has already clocked out.")

    def _get_attendance_report(self, employee_id: str, target_date: Optional[date] = None) -> str:
        logger.info(f"Generating attendance report for employee: {employee_id}")
        if employee_id not in attendance_records:
            return f"No attendance records found for employee '{employee_id}'."
        
        report_lines = [f"--- Attendance Report for Employee '{employee_id}' ---"]
        total_duration = timedelta()

        records_to_report = [r for r in attendance_records[employee_id] if not target_date or r["date"] == target_date]

        if not records_to_report:
            return f"No records found for employee '{employee_id}' on {target_date}."

        for record in records_to_report:
            clock_in = record["clock_in"]
            clock_out = record.get("clock_out")
            duration = clock_out - clock_in if clock_out else timedelta()
            total_duration += duration
            
            report_lines.append(
                f"Date: {record['date'].strftime('%Y-%m-%d')}, "
                f"Clock In: {clock_in.strftime('%H:%M:%S')}, "
                f"Clock Out: {clock_out.strftime('%H:%M:%S') if clock_out else 'N/A'}, "
                f"Duration: {self._format_duration(duration)}"
            )
        
        report_lines.append(f"Total Hours Tracked: {self._format_duration(total_duration)}")
        return "\n".join(report_lines)

    def _get_summary_report(self, target_date: date) -> str:
        logger.info(f"Generating summary report for date: {target_date}")
        report_lines = [f"--- Daily Attendance Summary for {target_date.strftime('%Y-%m-%d')} ---"]
        
        present_employees = 0
        absent_employees = set(attendance_records.keys())

        for emp_id, records in attendance_records.items():
            for record in records:
                if record["date"] == target_date:
                    present_employees += 1
                    absent_employees.discard(emp_id)
                    status = "Clocked Out" if "clock_out" in record else "Clocked In"
                    report_lines.append(f"- Employee {emp_id}: {status}")
                    break
        
        if not report_lines:
            return f"No attendance activity recorded for {target_date}."

        summary = (
            f"Total Employees Present: {present_employees}\n"
            f"Total Employees Absent: {len(absent_employees)} (IDs: {', '.join(absent_employees) if absent_employees else 'None'})"
        )
        report_lines.insert(1, summary)
        return "\n".join(report_lines)

    def _format_duration(self, duration: timedelta) -> str:
        """Formats a timedelta object into a human-readable string H:M:S."""
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02}"