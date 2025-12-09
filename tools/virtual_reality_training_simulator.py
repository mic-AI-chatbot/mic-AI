import logging
import random
import time
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated training data
training_scenarios = {
    "fire_safety_procedure": {
        "description": "A simulation of emergency fire evacuation procedures.",
        "steps": ["locate_fire_extinguisher", "pull_fire_alarm", "evacuate_building", "meet_at_assembly_point"]
    },
    "surgical_suturing": {
        "description": "A basic surgical task simulation for practicing suturing techniques.",
        "steps": ["sterilize_area", "make_incision", "apply_sutures", "tie_off_suture"]
    }
}
active_sessions: Dict[str, Dict[str, Any]] = {}

class VirtualRealityTrainingSimulatorTool(BaseTool):
    """
    A tool to simulate a virtual reality (VR) training session.
    """
    def __init__(self, tool_name: str = "virtual_reality_training_simulator_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a VR training session: start, end, and generate a performance report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'list_scenarios', 'start_session', 'end_session', 'get_report'."
                },
                "session_id": {"type": "string", "description": "The unique ID of a training session."},
                "scenario_name": {
                    "type": "string", 
                    "description": f"The training scenario to use. Available: {list(training_scenarios.keys())}"
                },
                "user_id": {"type": "string", "description": "The ID of the user in the training session."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            actions = {
                "list_scenarios": self._list_scenarios,
                "start_session": self._start_session,
                "end_session": self._end_session,
                "get_report": self._get_report,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VRTrainingSimulatorTool: {e}")
            return {"error": str(e)}

    def _list_scenarios(self, **kwargs) -> Dict:
        return {"available_scenarios": training_scenarios}

    def _start_session(self, scenario_name: str, user_id: str, **kwargs) -> Dict:
        if not scenario_name or not user_id:
            raise ValueError("'scenario_name' and 'user_id' are required.")
        if scenario_name not in training_scenarios:
            raise ValueError(f"Scenario '{scenario_name}' not found.")

        session_id = f"SESSION-{random.randint(1000, 9999)}"  # nosec B311
        
        new_session = {
            "session_id": session_id,
            "user_id": user_id,
            "scenario_name": scenario_name,
            "status": "active",
            "start_time": time.time(),
            "steps_completed": []
        }
        active_sessions[session_id] = new_session
        logger.info(f"Started training session '{session_id}' for user '{user_id}'.")
        return {"message": "Training session started.", "session_details": new_session}

    def _end_session(self, session_id: str, **kwargs) -> Dict:
        if not session_id:
            raise ValueError("'session_id' is required.")
        if session_id not in active_sessions:
            raise ValueError(f"Session '{session_id}' not found.")
            
        session = active_sessions[session_id]
        if session["status"] == "completed":
            return {"message": "Session was already completed."}

        session["status"] = "completed"
        session["end_time"] = time.time()
        
        # Simulate user performance
        scenario_steps = training_scenarios[session["scenario_name"]]["steps"]
        # Simulate completing a random number of steps correctly
        num_completed = random.randint(1, len(scenario_steps))  # nosec B311
        session["steps_completed"] = scenario_steps[:num_completed]
        
        logger.info(f"Ended training session '{session_id}'.")
        return {"message": "Session ended.", "session_id": session_id}

    def _get_report(self, session_id: str, **kwargs) -> Dict:
        if not session_id:
            raise ValueError("'session_id' is required.")
        if session_id not in active_sessions:
            raise ValueError(f"Session '{session_id}' not found.")
            
        session = active_sessions[session_id]
        if session["status"] != "completed":
            raise ValueError("Cannot generate a report for a session that is still active.")

        scenario = training_scenarios[session["scenario_name"]]
        total_steps = len(scenario["steps"])
        completed_steps = len(session["steps_completed"])
        score = (completed_steps / total_steps) * 100
        duration = session["end_time"] - session["start_time"]

        report = {
            "session_id": session_id,
            "user_id": session["user_id"],
            "scenario": session["scenario_name"],
            "duration_seconds": round(duration, 2),
            "performance_score": f"{score:.2f}%",
            "steps_missed": scenario["steps"][completed_steps:]
        }
        return {"performance_report": report}