import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DigitalTwinOfAPersonTool(BaseTool):
    """
    A tool for simulating a digital twin of a person, modeling health choices and their impacts.
    """

    def __init__(self, tool_name: str = "digital_twin_of_a_person"):
        super().__init__(tool_name)
        self.twins_file = "digital_twins.json"
        self.digital_twins: Dict[str, Dict[str, Any]] = self._load_twins()

    @property
    def description(self) -> str:
        return "Simulates a digital twin of a person: creates twins, simulates health choices, and generates health reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The digital twin operation to perform.",
                    "enum": ["create_twin", "simulate_health_choice", "get_health_report", "list_twins", "get_twin_details"]
                },
                "twin_id": {"type": "string"},
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "initial_health_params": {"type": "object"},
                "choice_type": {"type": "string", "enum": ["exercise", "diet", "stress_reduction"]},
                "intensity": {"type": "number", "minimum": 0.0, "maximum": 1.0}
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

    def _create_twin(self, twin_id: str, name: str, age: int, initial_health_params: Dict[str, Any]) -> Dict[str, Any]:
        if not all([twin_id, name, age, initial_health_params]):
            raise ValueError("Twin ID, name, age, and initial health parameters cannot be empty.")
        if twin_id in self.digital_twins: raise ValueError(f"Digital twin '{twin_id}' already exists.")
        if not all(k in initial_health_params for k in ["weight_kg", "blood_pressure_systolic", "blood_pressure_diastolic"]):
            raise ValueError("Initial health parameters must include 'weight_kg', 'blood_pressure_systolic', 'blood_pressure_diastolic'.")

        new_twin = {
            "twin_id": twin_id, "name": name, "age": age,
            "health_params": {
                "weight_kg": initial_health_params["weight_kg"],
                "blood_pressure_systolic": initial_health_params["blood_pressure_systolic"],
                "blood_pressure_diastolic": initial_health_params["blood_pressure_diastolic"],
                "fitness_level": 5, "stress_level": 5
            },
            "history": [{"event": "creation", "timestamp": datetime.now().isoformat(), "params": initial_health_params.copy()}]
        }
        self.digital_twins[twin_id] = new_twin
        self._save_twins()
        return new_twin

    def _simulate_health_choice(self, twin_id: str, choice_type: str, intensity: float) -> Dict[str, Any]:
        twin = self.digital_twins.get(twin_id)
        if not twin: raise ValueError(f"Digital twin '{twin_id}' not found.")
        if not (0.0 <= intensity <= 1.0): raise ValueError("Intensity must be between 0.0 and 1.0.")
        if choice_type not in ["exercise", "diet", "stress_reduction"]: raise ValueError(f"Unsupported choice type: '{choice_type}'.")

        message = f"Simulating '{choice_type}' with intensity {intensity:.1f} for twin '{twin_id}'. "
        
        if choice_type == "exercise":
            twin["health_params"]["fitness_level"] = min(10, twin["health_params"]["fitness_level"] + int(intensity * 3))
            twin["health_params"]["weight_kg"] = max(30.0, twin["health_params"]["weight_kg"] - intensity * 2)
            message += "Fitness level improved, weight decreased."
        elif choice_type == "diet":
            twin["health_params"]["weight_kg"] = max(30.0, twin["health_params"]["weight_kg"] - intensity * 3)
            twin["health_params"]["blood_pressure_systolic"] = max(70, twin["health_params"]["blood_pressure_systolic"] - int(intensity * 5))
            message += "Weight decreased, blood pressure improved."
        elif choice_type == "stress_reduction":
            twin["health_params"]["stress_level"] = max(1, twin["health_params"]["stress_level"] - int(intensity * 4))
            twin["health_params"]["blood_pressure_diastolic"] = max(40, twin["health_params"]["blood_pressure_diastolic"] - int(intensity * 3))
            message += "Stress level decreased, blood pressure improved."
        
        current_params = twin["health_params"].copy()
        twin["history"].append({
            "event": choice_type, "intensity": intensity, "timestamp": datetime.now().isoformat(),
            "params_after_choice": current_params
        })
        self._save_twins()
        return {"twin_id": twin_id, "updated_health_params": current_params, "message": message}

    def _get_health_report(self, twin_id: str) -> Dict[str, Any]:
        twin = self.digital_twins.get(twin_id)
        if not twin: raise ValueError(f"Digital twin '{twin_id}' not found.")
        
        report = {
            "twin_id": twin_id, "name": twin["name"], "age": twin["age"],
            "current_health_params": twin["health_params"], "health_history": twin["history"],
            "generated_at": datetime.now().isoformat()
        }
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_twin":
            return self._create_twin(kwargs.get("twin_id"), kwargs.get("name"), kwargs.get("age"), kwargs.get("initial_health_params"))
        elif operation == "simulate_health_choice":
            return self._simulate_health_choice(kwargs.get("twin_id"), kwargs.get("choice_type"), kwargs.get("intensity"))
        elif operation == "get_health_report":
            return self._get_health_report(kwargs.get("twin_id"))
        elif operation == "list_twins":
            return [{k: v for k, v in twin.items() if k not in ["health_params", "history"]} for twin in self.digital_twins.values()]
        elif operation == "get_twin_details":
            return self.digital_twins.get(kwargs.get("twin_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DigitalTwinOfAPersonTool functionality...")
    tool = DigitalTwinOfAPersonTool()
    
    try:
        print("\n--- Creating Twin ---")
        tool.execute(operation="create_twin", twin_id="alice_twin", name="Alice", age=30, initial_health_params={"weight_kg": 70.0, "blood_pressure_systolic": 120, "blood_pressure_diastolic": 80})
        
        print("\n--- Simulating Health Choice ---")
        tool.execute(operation="simulate_health_choice", twin_id="alice_twin", choice_type="exercise", intensity=0.8)

        print("\n--- Getting Health Report ---")
        report = tool.execute(operation="get_health_report", twin_id="alice_twin")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.twins_file): os.remove(tool.twins_file)
        print("\nCleanup complete.")
