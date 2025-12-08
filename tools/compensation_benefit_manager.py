import logging
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

DB_FILE = "hr_manager.db"

class HRDBManager:
    """Manages employee compensation and benefits data in a SQLite database."""
    _instance = None

    def __new__(cls, db_file):
        if cls._instance is None:
            cls._instance = super(HRDBManager, cls).__new__(cls)
            cls._instance.db_file = db_file
            cls._instance._create_tables()
        return cls._instance

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def _create_tables(self):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        employee_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        job_title TEXT,
                        department TEXT,
                        base_salary REAL,
                        bonus_percent REAL,
                        total_salary REAL,
                        hire_date TEXT,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS benefits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id TEXT NOT NULL,
                        benefit_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        details TEXT, -- Stored as JSON string
                        enrolled_at TEXT NOT NULL,
                        FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE,
                        UNIQUE(employee_id, benefit_type)
                    )
                """)
        except sqlite3.Error as e:
            logger.error(f"Database table creation error: {e}")

    def add_employee(self, employee_id: str, name: str, job_title: str, department: str, base_salary: float, hire_date: str) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                now = datetime.now().isoformat() + "Z"
                cursor.execute(
                    "INSERT INTO employees (employee_id, name, job_title, department, base_salary, bonus_percent, total_salary, hire_date, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (employee_id, name, job_title, department, base_salary, 0.0, base_salary, hire_date, now)
                )
                return True
            except sqlite3.IntegrityError: # Handles PRIMARY KEY constraint failure
                return False

    def get_employee(self, employee_id: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE employee_id = ?", (employee_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_employees(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT employee_id, name, job_title, department FROM employees ORDER BY name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def update_employee_salary(self, employee_id: str, base_salary: float, bonus_percent: float, total_salary: float) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE employees SET base_salary = ?, bonus_percent = ?, total_salary = ? WHERE employee_id = ?",
                (base_salary, bonus_percent, total_salary, employee_id)
            )
            return cursor.rowcount > 0

    def enroll_benefit(self, employee_id: str, benefit_type: str, details: Dict[str, Any]) -> bool:
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                now = datetime.now().isoformat() + "Z"
                cursor.execute(
                    "INSERT INTO benefits (employee_id, benefit_type, status, details, enrolled_at) VALUES (?, ?, ?, ?, ?)",
                    (employee_id, benefit_type, "enrolled", json.dumps(details), now)
                )
                return True
            except sqlite3.IntegrityError: # Handles UNIQUE constraint failure
                return False

    def update_benefit(self, employee_id: str, benefit_type: str, details: Dict[str, Any]) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE benefits SET details = ? WHERE employee_id = ? AND benefit_type = ?",
                (json.dumps(details), employee_id, benefit_type)
            )
            return cursor.rowcount > 0

    def remove_benefit(self, employee_id: str, benefit_type: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM benefits WHERE employee_id = ? AND benefit_type = ?", (employee_id, benefit_type))
            return cursor.rowcount > 0

    def get_employee_benefits(self, employee_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT benefit_type, status, details, enrolled_at FROM benefits WHERE employee_id = ?", (employee_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

hr_db_manager = HRDBManager(DB_FILE)

class AddEmployeeTool(BaseTool):
    """Adds a new employee to the HR system."""
    def __init__(self, tool_name="add_employee"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new employee to the HR system with their basic information and base salary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "A unique ID for the employee."},
                "name": {"type": "string", "description": "The full name of the employee."},
                "job_title": {"type": "string", "description": "The employee's job title."},
                "department": {"type": "string", "description": "The employee's department."},
                "base_salary": {"type": "number", "description": "The employee's base salary."},
                "hire_date": {"type": "string", "description": "The employee's hire date (YYYY-MM-DD)."}
            },
            "required": ["employee_id", "name", "job_title", "department", "base_salary", "hire_date"]
        }

    def execute(self, employee_id: str, name: str, job_title: str, department: str, base_salary: float, hire_date: str, **kwargs: Any) -> str:
        success = hr_db_manager.add_employee(employee_id, name, job_title, department, base_salary, hire_date)
        if success:
            report = {"message": f"Employee '{name}' (ID: {employee_id}) added successfully."}
        else:
            report = {"error": f"Employee with ID '{employee_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class CalculateEmployeeSalaryTool(BaseTool):
    """Calculates an employee's total salary including bonus."""
    def __init__(self, tool_name="calculate_employee_salary"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Calculates an employee's total salary based on their base salary and an optional bonus percentage, and updates it in the system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "The ID of the employee."},
                "base_salary": {"type": "number", "description": "The employee's current base salary."},
                "bonus_percent": {"type": "number", "description": "The bonus percentage (e.g., 0.10 for 10%).", "default": 0.0}
            },
            "required": ["employee_id", "base_salary"]
        }

    def execute(self, employee_id: str, base_salary: float, bonus_percent: float = 0.0, **kwargs: Any) -> str:
        employee = hr_db_manager.get_employee(employee_id)
        if not employee:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found. Please add the employee first."})
        
        total_salary = base_salary * (1 + bonus_percent)
        success = hr_db_manager.update_employee_salary(employee_id, base_salary, bonus_percent, total_salary)
        
        if success:
            report = {
                "message": f"Salary for employee '{employee_id}' calculated and updated.",
                "base_salary": round(base_salary, 2),
                "bonus_percent": round(bonus_percent * 100, 2),
                "total_salary": round(total_salary, 2)
            }
        else:
            report = {"error": f"Failed to update salary for employee '{employee_id}'. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class ManageEmployeeBenefitsTool(BaseTool):
    """Manages employee benefits (enroll, update, remove)."""
    def __init__(self, tool_name="manage_employee_benefits"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Manages employee benefits (e.g., health insurance, retirement plans) for a specified employee, allowing for enrollment, updates, or removal."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "employee_id": {"type": "string", "description": "The ID of the employee."},
                "benefit_type": {"type": "string", "description": "The type of benefit to manage (e.g., 'health_insurance', '401k', 'dental')."},
                "action": {"type": "string", "description": "The action to perform.", "enum": ["enroll", "update", "remove"]},
                "details": {
                    "type": "object",
                    "description": "Optional: Details for the benefit (e.g., {'provider': 'Blue Cross', 'plan': 'PPO'})."
                }
            },
            "required": ["employee_id", "benefit_type", "action"]
        }

    def execute(self, employee_id: str, benefit_type: str, action: str, details: Dict[str, Any] = None, **kwargs: Any) -> str:
        employee = hr_db_manager.get_employee(employee_id)
        if not employee:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found. Please add the employee first."})
        
        success = False
        message = ""
        if action == "enroll":
            success = hr_db_manager.enroll_benefit(employee_id, benefit_type, details if details else {})
            message = f"Employee '{employee_id}' enrolled in '{benefit_type}' benefits."
        elif action == "update":
            success = hr_db_manager.update_benefit(employee_id, benefit_type, details if details else {})
            message = f"Employee '{employee_id}' '{benefit_type}' benefits updated."
        elif action == "remove":
            success = hr_db_manager.remove_benefit(employee_id, benefit_type)
            message = f"Employee '{employee_id}' '{benefit_type}' benefits removed."
        
        if success:
            report = {"message": message}
        else:
            report = {"error": f"Failed to perform '{action}' action for '{benefit_type}' benefits for employee '{employee_id}'. Check if employee is enrolled/not enrolled as expected."}
        return json.dumps(report, indent=2)

class GetEmployeeCompensationTool(BaseTool):
    """Retrieves an employee's compensation details."""
    def __init__(self, tool_name="get_employee_compensation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves an employee's compensation details, including base salary, bonus percentage, and total salary."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"employee_id": {"type": "string", "description": "The ID of the employee to retrieve compensation for."}},
            "required": ["employee_id"]
        }

    def execute(self, employee_id: str, **kwargs: Any) -> str:
        employee = hr_db_manager.get_employee(employee_id)
        if not employee:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found."})
            
        report = {
            "employee_id": employee_id,
            "name": employee["name"],
            "base_salary": employee["base_salary"],
            "bonus_percent": employee["bonus_percent"],
            "total_salary": employee["total_salary"]
        }
        return json.dumps(report, indent=2)

class GetEmployeeBenefitsTool(BaseTool):
    """Retrieves an employee's benefits details."""
    def __init__(self, tool_name="get_employee_benefits"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves an employee's benefits details, including enrolled benefits and their configurations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"employee_id": {"type": "string", "description": "The ID of the employee to retrieve benefits for."}},
            "required": ["employee_id"]
        }

    def execute(self, employee_id: str, **kwargs: Any) -> str:
        employee = hr_db_manager.get_employee(employee_id)
        if not employee:
            return json.dumps({"error": f"Employee with ID '{employee_id}' not found."})
        
        benefits = hr_db_manager.get_employee_benefits(employee_id)
        report = {
            "employee_id": employee_id,
            "name": employee["name"],
            "benefits": benefits
        }
        return json.dumps(report, indent=2)

class ListEmployeesTool(BaseTool):
    """Lists all employees in the HR system."""
    def __init__(self, tool_name="list_employees"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all employees in the HR system, showing their ID, name, job title, and department."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        employees = hr_db_manager.list_employees()
        report = {
            "total_employees": len(employees),
            "employees": employees
        }
        return json.dumps(report, indent=2)