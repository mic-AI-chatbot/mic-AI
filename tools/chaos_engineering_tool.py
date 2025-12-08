import logging
import json
import random
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ChaosExperiment:
    """Represents a single chaos engineering experiment with detailed status, observations, and injected fault details."""
    def __init__(self, experiment_name: str, target_system: str, fault_type: str, duration_seconds: int):
        self.experiment_name = experiment_name
        self.target_system = target_system
        self.fault_type = fault_type
        self.duration_seconds = duration_seconds
        self.status = "initiated" # initiated, running, completed, stopped, failed
        self.start_time = datetime.now()
        self.end_time = None
        self.observations: List[Dict[str, Any]] = []
        self.injected_fault_details: Dict[str, Any] = {}

    def update_status(self, status: str, message: str = None, details: Dict[str, Any] = None):
        self.status = status
        self.observations.append({"timestamp": datetime.now().isoformat() + "Z", "status": status, "message": message, "details": details})
        if status in ["completed", "stopped", "failed"]:
            self.end_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_name": self.experiment_name,
            "target_system": self.target_system,
            "fault_type": self.fault_type,
            "duration_seconds": self.duration_seconds,
            "status": self.status,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "last_observation": self.observations[-1] if self.observations else None,
            "injected_fault_details": self.injected_fault_details
        }

class ExperimentManager:
    """Manages all chaos engineering experiments, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ExperimentManager, cls).__new__(cls)
            cls._instance.experiments: Dict[str, ChaosExperiment] = {}
        return cls._instance

    def create_experiment(self, experiment_name: str, target_system: str, fault_type: str, duration_seconds: int) -> ChaosExperiment:
        experiment = ChaosExperiment(experiment_name, target_system, fault_type, duration_seconds)
        self.experiments[experiment_name] = experiment
        return experiment

    def get_experiment(self, experiment_name: str) -> ChaosExperiment:
        return self.experiments.get(experiment_name)

experiment_manager = ExperimentManager()

class StartChaosExperimentTool(BaseTool):
    """Starts a new chaos engineering experiment."""
    def __init__(self, tool_name="start_chaos_experiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Starts a new chaos engineering experiment on a specified target system with a defined fault type (e.g., 'cpu_spike', 'network_latency', 'service_failure')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "experiment_name": {"type": "string", "description": "A unique name for the chaos experiment."},
                "target_system": {"type": "string", "description": "The system or service to target with the experiment."},
                "fault_type": {"type": "string", "description": "The type of fault to inject.", "enum": ["cpu_spike", "network_latency", "service_failure"]},
                "duration_seconds": {"type": "integer", "description": "The simulated duration of the fault injection in seconds.", "default": 60}
            },
            "required": ["experiment_name", "target_system", "fault_type"]
        }

    def execute(self, experiment_name: str, target_system: str, fault_type: str, duration_seconds: int = 60, **kwargs: Any) -> str:
        if experiment_name in experiment_manager.experiments and experiment_manager.experiments[experiment_name].status == "running":
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' is already running. Please stop it first."})
        
        experiment = experiment_manager.create_experiment(experiment_name, target_system, fault_type, duration_seconds)
        
        # Simulate fault injection details
        fault_details = {}
        if fault_type == "cpu_spike":
            fault_details["simulated_cpu_load"] = "80-95%"
            fault_details["message"] = "Simulated CPU spike injected into target system."
        elif fault_type == "network_latency":
            fault_details["simulated_latency_ms"] = "200-500ms"
            fault_details["message"] = "Simulated network latency injected between target and dependencies."
        elif fault_type == "service_failure":
            fault_details["simulated_service_status"] = "degraded/unavailable"
            fault_details["message"] = "Simulated service failure injected into target system."
        
        experiment.injected_fault_details = fault_details
        experiment.update_status("running", "Fault injected.", fault_details)
        
        report = {
            "message": f"Chaos experiment '{experiment_name}' started on '{target_system}' with fault type '{fault_type}'.",
            "experiment_details": experiment.to_dict()
        }
        return json.dumps(report, indent=2)

class ObserveChaosImpactTool(BaseTool):
    """Observes the impact of a running chaos engineering experiment."""
    def __init__(self, tool_name="observe_chaos_impact"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Observes the impact of a running chaos engineering experiment on the target system, returning simulated metrics and observations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"experiment_name": {"type": "string", "description": "The name of the chaos experiment to observe."}},
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, **kwargs: Any) -> str:
        experiment = experiment_manager.get_experiment(experiment_name)
        if not experiment:
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' not found."})
        if experiment.status != "running":
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' is not running. Current status: {experiment.status}. Cannot observe impact."})

        # Simulate impact metrics based on fault type
        impact_metrics = {}
        observations = "System showed some degradation but remained operational."
        
        if experiment.fault_type == "cpu_spike":
            impact_metrics["cpu_utilization_increase_percent"] = round(random.uniform(10, 50), 2)  # nosec B311
            impact_metrics["response_time_increase_ms"] = round(random.uniform(50, 200), 2)  # nosec B311
            if impact_metrics["cpu_utilization_increase_percent"] > 40:
                observations = "Significant CPU degradation observed. System response times increased, indicating performance bottleneck."
        elif experiment.fault_type == "network_latency":
            impact_metrics["latency_increase_ms"] = round(random.uniform(100, 500), 2)  # nosec B311
            impact_metrics["packet_loss_percent"] = round(random.uniform(0, 10), 2)  # nosec B311
            if impact_metrics["latency_increase_ms"] > 300:
                observations = "High network latency observed. Some services might be experiencing timeouts or slow responses."
        elif experiment.fault_type == "service_failure":
            impact_metrics["error_rate_increase_percent"] = round(random.uniform(5, 20), 2)  # nosec B311
            impact_metrics["service_availability_percent"] = round(random.uniform(80, 95), 2)  # nosec B311
            if impact_metrics["service_availability_percent"] < 90:
                observations = "Service availability degraded. Critical errors detected, indicating potential service outage."
        
        experiment.update_status("running", "Impact observed.", {"metrics": impact_metrics, "observations": observations})
        
        report = {
            "experiment_name": experiment_name,
            "impact_metrics": impact_metrics,
            "observations": observations
        }
        return json.dumps(report, indent=2)

class StopChaosExperimentTool(BaseTool):
    """Stops a running chaos engineering experiment."""
    def __init__(self, tool_name="stop_chaos_experiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Stops a running chaos engineering experiment and cleans up any injected faults."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"experiment_name": {"type": "string", "description": "The name of the chaos experiment to stop."}},
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, **kwargs: Any) -> str:
        experiment = experiment_manager.get_experiment(experiment_name)
        if not experiment:
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' not found."})
        if experiment.status != "running":
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' is not running. Current status: {experiment.status}. Cannot stop a non-running experiment."})
        
        # Simulate fault cleanup
        cleanup_message = f"Fault '{experiment.fault_type}' cleaned up from '{experiment.target_system}'. System returning to normal."
        experiment.update_status("stopped", cleanup_message)
        
        report = {
            "message": f"Chaos experiment '{experiment_name}' stopped successfully. Faults cleaned up.",
            "experiment_details": experiment.to_dict()
        }
        return json.dumps(report, indent=2)

class GetChaosExperimentStatusTool(BaseTool):
    """Retrieves the current status and observations of a chaos experiment."""
    def __init__(self, tool_name="get_chaos_experiment_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current status, fault type, target system, and latest observations of a chaos engineering experiment."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"experiment_name": {"type": "string", "description": "The name of the chaos experiment to retrieve status for."}},
            "required": ["experiment_name"]
        }

    def execute(self, experiment_name: str, **kwargs: Any) -> str:
        experiment = experiment_manager.get_experiment(experiment_name)
        if not experiment:
            return json.dumps({"error": f"Chaos experiment '{experiment_name}' not found."})
            
        return json.dumps(experiment.to_dict(), indent=2)