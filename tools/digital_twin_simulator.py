import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DigitalTwinSimulatorTool(BaseTool):
    """
    A tool for simulating the creation and operation of digital twins for physical assets.
    """

    def __init__(self, tool_name: str = "digital_twin_simulator"):
        super().__init__(tool_name)
        self.twins_file = "digital_twins_assets.json"
        self.digital_twins: Dict[str, Dict[str, Any]] = self._load_twins()

    @property
    def description(self) -> str:
        return "Simulates digital twins for physical assets: creates twins, updates their state, runs simulations, and retrieves details."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The digital twin operation to perform.",
                    "enum": ["create_twin", "update_twin_state", "run_simulation", "get_twin_details", "list_twins"]
                },
                "twin_id": {"type": "string"},
                "twin_name": {"type": "string"},
                "asset_id": {"type": "string"},
                "asset_type": {"type": "string"},
                "initial_state": {"type": "object"},
                "new_state_data": {"type": "object"},
                "simulation_duration_minutes": {"type": "integer", "minimum": 1}
            },
            "required": ["operation"]
        }

    def _load_twins(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.twins_file):
            with open(self.twins_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted twins file '{self.twins_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_twins(self) -> None:
        with open(self.twins_file, 'w') as f:
            json.dump(self.digital_twins, f, indent=4)

    def _create_twin(self, twin_id: str, twin_name: str, asset_id: str, asset_type: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        if not all([twin_id, twin_name, asset_id, asset_type, initial_state]):
            raise ValueError("Twin ID, name, asset ID, asset type, and initial state cannot be empty.")
        if twin_id in self.digital_twins: raise ValueError(f"Digital twin '{twin_id}' already exists.")

        new_twin = {
            "twin_id": twin_id, "twin_name": twin_name, "asset_id": asset_id,
            "asset_type": asset_type, "current_state": initial_state,
            "state_history": [{"timestamp": datetime.now().isoformat(), "state": initial_state.copy(), "event": "initialization"}],
            "created_at": datetime.now().isoformat()
        }
        self.digital_twins[twin_id] = new_twin
        self._save_twins()
        return new_twin

    def _update_twin_state(self, twin_id: str, new_state_data: Dict[str, Any]) -> Dict[str, Any]:
        twin = self.digital_twins.get(twin_id)
        if not twin: raise ValueError(f"Digital twin '{twin_id}' not found.")
        
        twin["current_state"].update(new_state_data)
        twin["state_history"].append({
            "timestamp": datetime.now().isoformat(), "state": twin["current_state"].copy(), "event": "state_update"
        })
        self._save_twins()
        return twin

    def _run_simulation(self, twin_id: str, simulation_duration_minutes: int) -> Dict[str, Any]:
        twin = self.digital_twins.get(twin_id)
        if not twin: raise ValueError(f"Digital twin '{twin_id}' not found.")
        if simulation_duration_minutes <= 0: raise ValueError("Simulation duration must be a positive integer.")

        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=simulation_duration_minutes)
        
        num_updates = random.randint(1, simulation_duration_minutes // 5 + 1)  # nosec B311
        for _ in range(num_updates):
            updated_params = {}
            for key, value in twin["current_state"].items():
                if isinstance(value, (int, float)):
                    change = random.uniform(-0.1, 0.1) * value  # nosec B311
                    updated_params[key] = round(value + change, 2)
                elif isinstance(value, str) and key == "status":
                    updated_params[key] = random.choice(["running", "idle", "warning"])  # nosec B311
            self._update_twin_state(twin_id, updated_params)
        
        simulation_summary = {
            "twin_id": twin_id, "simulation_start": start_time.isoformat(), "simulation_end": end_time.isoformat(),
            "duration_minutes": simulation_duration_minutes, "final_state": twin["current_state"],
            "total_state_updates": len(twin["state_history"]) - 1
        }
        return simulation_summary

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_twin":
            return self._create_twin(kwargs.get("twin_id"), kwargs.get("twin_name"), kwargs.get("asset_id"), kwargs.get("asset_type"), kwargs.get("initial_state"))
        elif operation == "update_twin_state":
            return self._update_twin_state(kwargs.get("twin_id"), kwargs.get("new_state_data"))
        elif operation == "run_simulation":
            return self._run_simulation(kwargs.get("twin_id"), kwargs.get("simulation_duration_minutes"))
        elif operation == "get_twin_details":
            return self.digital_twins.get(kwargs.get("twin_id"))
        elif operation == "list_twins":
            return [{k: v for k, v in twin.items() if k not in ["current_state", "state_history"]} for twin in self.digital_twins.values()]
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DigitalTwinSimulatorTool functionality...")
    tool = DigitalTwinSimulatorTool()
    
    try:
        print("\n--- Creating Twin ---")
        tool.execute(operation="create_twin", twin_id="pump_001", twin_name="Water Pump 001", asset_id="PUMP-001", asset_type="pump", initial_state={"temperature": 25.0, "pressure": 100.0})
        
        print("\n--- Updating Twin State ---")
        tool.execute(operation="update_twin_state", twin_id="pump_001", new_state_data={"temperature": 25.8, "pressure": 101.5})

        print("\n--- Running Simulation ---")
        simulation_summary = tool.execute(operation="run_simulation", twin_id="pump_001", simulation_duration_minutes=5)
        print(json.dumps(simulation_summary, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.twins_file): os.remove(tool.twins_file)
        print("\nCleanup complete.")