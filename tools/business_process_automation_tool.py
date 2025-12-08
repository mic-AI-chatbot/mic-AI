import logging
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class BusinessProcess:
    """Represents a single business process with its steps, status, and execution history."""
    def __init__(self, process_name: str, steps: List[Dict[str, Any]]):
        self.process_name = process_name
        self.steps = steps # Each step: {"name": "Step A", "simulated_duration_hours": 1}
        self.status = "defined" # defined, running, completed, failed
        self.current_step_index = -1 # -1 for not started, 0 for first step
        self.execution_history: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.status = "running"
        self.current_step_index = 0
        self.start_time = datetime.now()
        self.execution_history.append({"timestamp": datetime.now().isoformat(), "event": "Process started", "step": self.steps[0]["name"] if self.steps else "N/A"})

    def advance_step(self) -> Dict[str, Any]:
        if self.status != "running":
            return {"error": "Process is not running."}
        if self.current_step_index >= len(self.steps):
            return {"error": "Process has no more steps to advance."}

        current_step = self.steps[self.current_step_index]
        
        # Simulate step execution
        outcome = random.choice(["success", "failure"])  # nosec B311
        message = f"Step '{current_step['name']}' executed with {outcome}."
        self.execution_history.append({"timestamp": datetime.now().isoformat(), "event": message, "step": current_step["name"], "outcome": outcome})

        if outcome == "success":
            self.current_step_index += 1
            if self.current_step_index >= len(self.steps):
                self.status = "completed"
                self.end_time = datetime.now()
                message = "Process completed successfully."
                self.execution_history.append({"timestamp": datetime.now().isoformat(), "event": message})
            else:
                message = f"Advanced to next step: '{self.steps[self.current_step_index]['name']}'."
        else:
            self.status = "failed"
            self.end_time = datetime.now()
            message = f"Process failed at step '{current_step['name']}'."
            self.execution_history.append({"timestamp": datetime.now().isoformat(), "event": message})
        
        return {"status": self.status, "current_step": current_step["name"], "outcome": outcome, "message": message}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "process_name": self.process_name,
            "steps": self.steps,
            "status": self.status,
            "current_step": self.steps[self.current_step_index]["name"] if 0 <= self.current_step_index < len(self.steps) else "Not Started",
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "execution_history_count": len(self.execution_history)
        }

class ProcessManager:
    """Manages all business processes, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProcessManager, cls).__new__(cls)
            cls._instance.processes: Dict[str, BusinessProcess] = {}
        return cls._instance

    def define_process(self, process_name: str, steps: List[Dict[str, Any]]) -> BusinessProcess:
        process = BusinessProcess(process_name, steps)
        self.processes[process_name] = process
        return process

    def get_process(self, process_name: str) -> BusinessProcess:
        return self.processes.get(process_name)

process_manager = ProcessManager()

class DefineBusinessProcessTool(BaseTool):
    """Defines a new business process with a sequence of steps."""
    def __init__(self, tool_name="define_business_process"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a new business process with a unique name and a sequence of steps, each with a name and simulated duration."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "process_name": {"type": "string", "description": "A unique name for the business process."},
                "steps": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "The name of the step."},
                            "simulated_duration_hours": {"type": "number", "description": "Simulated duration of the step in hours.", "default": 1}
                        },
                        "required": ["name"]
                    },
                    "description": "A list of steps in the process, each with a 'name' and optional 'simulated_duration_hours'."
                }
            },
            "required": ["process_name", "steps"]
        }

    def execute(self, process_name: str, steps: List[Dict[str, Any]], **kwargs: Any) -> str:
        if process_name in process_manager.processes:
            return json.dumps({"error": f"Business process '{process_name}' already exists. Please choose a unique name."})
        
        process = process_manager.define_process(process_name, steps)
        
        report = {
            "message": f"Business process '{process_name}' defined successfully with {len(steps)} steps.",
            "process_details": process.to_dict()
        }
        return json.dumps(report, indent=2)

class StartBusinessProcessTool(BaseTool):
    """Starts a defined business process, initiating its execution."""
    def __init__(self, tool_name="start_business_process"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a defined business process, initiating its execution from the first step."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"process_name": {"type": "string", "description": "The name of the business process to start."}},
            "required": ["process_name"]
        }

    def execute(self, process_name: str, **kwargs: Any) -> str:
        process = process_manager.get_process(process_name)
        if not process:
            return json.dumps({"error": f"Business process '{process_name}' not found. Please define it first."})
        if process.status != "defined":
            return json.dumps({"error": f"Business process '{process_name}' is already '{process.status}'. Cannot start a process that is not in 'defined' status."})
        
        process.start()
        
        report = {
            "message": f"Business process '{process_name}' started successfully.",
            "process_details": process.to_dict()
        }
        return json.dumps(report, indent=2)

class AdvanceProcessStepTool(BaseTool):
    """Advances a running business process to the next step."""
    def __init__(self, tool_name="advance_process_step"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Advances a running business process to the next step, simulating its execution and potential outcomes (success/failure)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"process_name": {"type": "string", "description": "The name of the business process to advance."}},
            "required": ["process_name"]
        }

    def execute(self, process_name: str, **kwargs: Any) -> str:
        process = process_manager.get_process(process_name)
        if not process:
            return json.dumps({"error": f"Business process '{process_name}' not found."})
        if process.status != "running":
            return json.dumps({"error": f"Business process '{process_name}' is not running. Current status: {process.status}. Cannot advance."})
        
        result = process.advance_step()
        
        report = {
            "message": f"Process '{process_name}' step advanced.",
            "step_outcome": result,
            "process_details": process.to_dict()
        }
        return json.dumps(report, indent=2)

class GetProcessStatusTool(BaseTool):
    """Retrieves the current status and progress of a business process."""
    def __init__(self, tool_name="get_process_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status, current step, and execution history summary of a business process."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"process_name": {"type": "string", "description": "The name of the business process to retrieve status for."}},
            "required": ["process_name"]
        }

    def execute(self, process_name: str, **kwargs: Any) -> str:
        process = process_manager.get_process(process_name)
        if not process:
            return json.dumps({"error": f"Business process '{process_name}' not found."})
            
        return json.dumps(process.to_dict(), indent=2)