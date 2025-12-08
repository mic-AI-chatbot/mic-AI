import logging
import random
import json
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PIDController:
    """A simple PID controller."""
    def __init__(self, Kp: float, Ki: float, Kd: float):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.previous_error = 0.0
        self.integral = 0.0

    def update(self, error: float, dt: float) -> float:
        self.integral += error * dt
        derivative = (error - self.previous_error) / dt
        self.previous_error = error
        return self.Kp * error + self.Ki * self.integral + self.Kd * derivative

class SimulatedSystem:
    """A simple simulated system (e.g., a thermostat)."""
    def __init__(self, system_id: str, setpoint: float, initial_value: float = 20.0):
        self.system_id = system_id
        self.setpoint = setpoint
        self.current_value = initial_value
        self.pid = PIDController(Kp=0.5, Ki=0.1, Kd=0.05)
        self.last_control_output = 0.0

    def update(self, dt: float = 1.0):
        """Updates the system state based on the PID controller."""
        error = self.setpoint - self.current_value
        control_output = self.pid.update(error, dt)
        self.last_control_output = control_output
        
        # Simulate system dynamics (e.g., temperature change)
        # The control output affects the rate of change.
        self.current_value += control_output * dt * 0.1 + random.uniform(-0.1, 0.1) # Add some noise  # nosec B311

# In-memory storage for simulated systems
systems: Dict[str, SimulatedSystem] = {
    "thermostat_1": SimulatedSystem("thermostat_1", setpoint=22.0)
}

class CreateControlSystemTool(BaseTool):
    """Tool to create a new simulated control system."""
    def __init__(self, tool_name="create_control_system"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new simulated control system (e.g., a thermostat) with a specified setpoint."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "system_id": {"type": "string", "description": "The unique identifier for the new system."},
                "setpoint": {"type": "number", "description": "The target setpoint for the system (e.g., desired temperature)."}
            },
            "required": ["system_id", "setpoint"]
        }

    def execute(self, system_id: str, setpoint: float, **kwargs: Any) -> str:
        if system_id in systems:
            return json.dumps({"error": f"System with ID '{system_id}' already exists."}, indent=2)
        
        systems[system_id] = SimulatedSystem(system_id, setpoint)
        return json.dumps({"message": f"System '{system_id}' created with setpoint {setpoint}."}, indent=2)

class MonitorControlSystemTool(BaseTool):
    """Tool to monitor a control system's performance."""
    def __init__(self, tool_name="monitor_control_system"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Monitors the performance of a control system, returning its current state, error, and control output."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "system_id": {"type": "string", "description": "The ID of the control system to monitor."}
            },
            "required": ["system_id"]
        }

    def execute(self, system_id: str, **kwargs: Any) -> str:
        if system_id not in systems:
            return json.dumps({"error": f"System with ID '{system_id}' not found."}, indent=2)
            
        system = systems[system_id]
        system.update() # Simulate one time step
        
        report = {
            "system_id": system.system_id,
            "setpoint": system.setpoint,
            "current_value": round(system.current_value, 2),
            "error": round(system.setpoint - system.current_value, 2),
            "control_output": round(system.last_control_output, 2)
        }
        return json.dumps(report, indent=2)

class AdaptControlParametersTool(BaseTool):
    """Tool to adapt the PID control parameters for a system."""
    def __init__(self, tool_name="adapt_control_parameters"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adapts the PID control parameters (Kp, Ki, Kd) for a specified system."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "system_id": {"type": "string", "description": "The ID of the control system."},
                "kp": {"type": "number", "description": "The new Proportional gain."},
                "ki": {"type": "number", "description": "The new Integral gain."},
                "kd": {"type": "number", "description": "The new Derivative gain."}
            },
            "required": ["system_id", "kp", "ki", "kd"]
        }

    def execute(self, system_id: str, kp: float, ki: float, kd: float, **kwargs: Any) -> str:
        if system_id not in systems:
            return json.dumps({"error": f"System with ID '{system_id}' not found."}, indent=2)
            
        system = systems[system_id]
        system.pid.Kp = kp
        system.pid.Ki = ki
        system.pid.Kd = kd
        
        report = {
            "message": f"PID parameters for system '{system_id}' updated.",
            "new_gains": {"Kp": kp, "Ki": ki, "Kd": kd}
        }
        return json.dumps(report, indent=2)