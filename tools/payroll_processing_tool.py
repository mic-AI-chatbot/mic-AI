import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PayrollProcessingSimulatorTool(BaseTool):
    """
    A tool that simulates payroll processing, including managing employee records,
    calculating salaries, generating pay stubs, and processing tax deductions.
    """

    def __init__(self, tool_name: str = "PayrollProcessingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.employees_file = os.path.join(self.data_dir, "employee_records.json")
        self.payroll_file = os.path.join(self.data_dir, "payroll_records.json")
        
        # Employee records: {employee_id: {name: ..., hourly_rate: ..., tax_rate: ...}}
        self.employees: Dict[str, Dict[str, Any]] = self._load_data(self.employees_file, default={})
        # Payroll records: {employee_id: {pay_period_id: {gross_pay: ..., net_pay: ..., deductions: ...}}}
        self.payroll: Dict[str, Dict[str, Any]] = self._load_data(self.payroll_file, default={})

    @property
    def description(self) -> str:
        return "Simulates payroll processing: manage employees, calculate salaries, generate pay stubs, process deductions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_employee", "calculate_salary", "generate_pay_stub", "process_tax_deductions", "get_employee_details"]},
                "employee_id": {"type": "string"},
                "name": {"type": "string"},
                "hourly_rate": {"type": "number", "minimum": 0},
                "tax_rate": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.2},
                "hours_worked": {"type": "number", "minimum": 0},
                "pay_period_id": {"type": "string", "description": "Unique ID for the pay period (e.g., '2025-11-15')."}
            },
            "required": ["operation", "employee_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_employees(self):
        with open(self.employees_file, 'w') as f: json.dump(self.employees, f, indent=2)

    def _save_payroll(self):
        with open(self.payroll_file, 'w') as f: json.dump(self.payroll, f, indent=2)

    def add_employee(self, employee_id: str, name: str, hourly_rate: float, tax_rate: float = 0.2) -> Dict[str, Any]:
        """Adds a new employee record."""
        if employee_id in self.employees: raise ValueError(f"Employee '{employee_id}' already exists.")
        
        new_employee = {
            "id": employee_id, "name": name, "hourly_rate": hourly_rate, "tax_rate": tax_rate,
            "hired_at": datetime.now().isoformat()
        }
        self.employees[employee_id] = new_employee
        self._save_employees()
        return new_employee

    def calculate_salary(self, employee_id: str, hours_worked: float, pay_period_id: str) -> Dict[str, Any]:
        """Calculates gross and net pay for an employee for a given pay period."""
        employee = self.employees.get(employee_id)
        if not employee: raise ValueError(f"Employee '{employee_id}' not found.")
        
        if employee_id not in self.payroll: self.payroll[employee_id] = {}
        if pay_period_id in self.payroll[employee_id]: raise ValueError(f"Pay stub for '{employee_id}' for period '{pay_period_id}' already exists.")

        gross_pay = hours_worked * employee["hourly_rate"]
        tax_deduction = gross_pay * employee["tax_rate"]
        net_pay = gross_pay - tax_deduction
        
        pay_stub = {
            "pay_period_id": pay_period_id, "hours_worked": hours_worked,
            "hourly_rate": employee["hourly_rate"], "gross_pay": round(gross_pay, 2),
            "tax_rate": employee["tax_rate"], "tax_deduction": round(tax_deduction, 2),
            "net_pay": round(net_pay, 2), "calculated_at": datetime.now().isoformat()
        }
        self.payroll[employee_id][pay_period_id] = pay_stub
        self._save_payroll()
        return pay_stub

    def generate_pay_stub(self, employee_id: str, pay_period_id: str) -> Dict[str, Any]:
        """Retrieves and formats a pay stub."""
        if employee_id not in self.payroll or pay_period_id not in self.payroll[employee_id]:
            raise ValueError(f"Pay stub for employee '{employee_id}' for period '{pay_period_id}' not found.")
        
        pay_stub = self.payroll[employee_id][pay_period_id]
        employee = self.employees[employee_id]
        
        formatted_stub = {
            "employee_name": employee["name"],
            "employee_id": employee_id,
            "pay_period": pay_period_id,
            "hours_worked": pay_stub["hours_worked"],
            "hourly_rate": f"${pay_stub['hourly_rate']:.2f}",
            "gross_pay": f"${pay_stub['gross_pay']:.2f}",
            "tax_deduction": f"${pay_stub['tax_deduction']:.2f}",
            "net_pay": f"${pay_stub['net_pay']:.2f}",
            "calculated_at": pay_stub["calculated_at"]
        }
        return formatted_stub

    def process_tax_deductions(self, employee_id: str, pay_period_id: str) -> Dict[str, Any]:
        """Simulates processing tax deductions for a pay period."""
        if employee_id not in self.payroll or pay_period_id not in self.payroll[employee_id]:
            raise ValueError(f"Pay stub for employee '{employee_id}' for period '{pay_period_id}' not found.")
        
        return {"status": "success", "message": f"Simulated: Tax deductions for employee '{employee_id}' for period '{pay_period_id}' processed."}

    def get_employee_details(self, employee_id: str) -> Dict[str, Any]:
        """Retrieves an employee's details."""
        employee = self.employees.get(employee_id)
        if not employee: raise ValueError(f"Employee '{employee_id}' not found.")
        return employee

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_employee": self.add_employee,
            "calculate_salary": self.calculate_salary,
            "generate_pay_stub": self.generate_pay_stub,
            "process_tax_deductions": self.process_tax_deductions,
            "get_employee_details": self.get_employee_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating PayrollProcessingSimulatorTool functionality...")
    temp_dir = "temp_payroll_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    payroll_tool = PayrollProcessingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add an employee
        print("\n--- Adding employee 'emp_001' ---")
        payroll_tool.execute(operation="add_employee", employee_id="emp_001", name="Alice Smith", hourly_rate=25.0, tax_rate=0.25)
        print("Employee added.")

        # 2. Calculate salary for a pay period
        print("\n--- Calculating salary for 'emp_001' for '2025-11-15' ---")
        pay_stub_data = payroll_tool.execute(operation="calculate_salary", employee_id="emp_001", hours_worked=80, pay_period_id="2025-11-15")
        print(json.dumps(pay_stub_data, indent=2))

        # 3. Generate pay stub
        print("\n--- Generating pay stub for 'emp_001' for '2025-11-15' ---")
        pay_stub = payroll_tool.execute(operation="generate_pay_stub", employee_id="emp_001", pay_period_id="2025-11-15")
        print(json.dumps(pay_stub, indent=2))

        # 4. Process tax deductions
        print("\n--- Processing tax deductions for 'emp_001' for '2025-11-15' ---")
        tax_process_result = payroll_tool.execute(operation="process_tax_deductions", employee_id="emp_001", pay_period_id="2025-11-15")
        print(json.dumps(tax_process_result, indent=2))

        # 5. Get employee details
        print("\n--- Getting employee details for 'emp_001' ---")
        employee_details = payroll_tool.execute(operation="get_employee_details", employee_id="emp_001")
        print(json.dumps(employee_details, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")