import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class WhatIfHistoricalSimulatorTool(BaseTool):
    """
    A tool to simulate alternate historical timelines based on hypothetical changes to key events.
    """
    def __init__(self, tool_name: str = "what_if_historical_simulator_tool"):
        super().__init__(tool_name)
        self.historical_events = {
            "WWII_outcome": {
                "original": "Allies win",
                "alternate_options": ["Axis wins", "Stalemate"],
                "description": "The outcome of World War II."
            },
            "Roman_Empire_fall": {
                "original": "476 CE",
                "alternate_options": ["Never falls", "Falls earlier"],
                "description": "The fall of the Western Roman Empire."
            },
            "Industrial_Revolution_start": {
                "original": "18th Century",
                "alternate_options": ["Earlier", "Later"],
                "description": "The start of the Industrial Revolution."
            }
        }
        self.current_timeline: Dict[str, Any] = {} # Stores the simulated timeline changes

    @property
    def description(self) -> str:
        return "Simulates alternate historical timelines by changing key events and their impacts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'simulate_event', 'get_summary', 'list_events', 'reset_timeline'."
                },
                "event_name": {
                    "type": "string", 
                    "description": f"The historical event to alter. Supported: {list(self.historical_events.keys())}"
                },
                "alternate_outcome": {"type": "string", "description": "The hypothetical alternate outcome for the event."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            event_name = kwargs.get("event_name")

            if action == 'simulate_event' and not event_name:
                raise ValueError("'event_name' is required for 'simulate_event' action.")

            actions = {
                "simulate_event": self._simulate_event_impact,
                "get_summary": self._get_timeline_summary,
                "list_events": self._list_historical_events,
                "reset_timeline": self._reset_timeline,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WhatIfHistoricalSimulatorTool: {e}")
            return {"error": str(e)}

    def _simulate_event_impact(self, event_name: str, alternate_outcome: str, **kwargs) -> Dict:
        if event_name not in self.historical_events:
            raise ValueError(f"Event '{event_name}' not recognized. Supported events: {list(self.historical_events.keys())}.")
        
        valid_outcomes = self.historical_events[event_name]["alternate_options"] + [self.historical_events[event_name]["original"]]
        if alternate_outcome not in valid_outcomes:
            raise ValueError(f"Alternate outcome '{alternate_outcome}' not valid for '{event_name}'. Options: {valid_outcomes}.")

        self.current_timeline[event_name] = alternate_outcome
        
        # Simulate cascading effects
        effects = self._generate_simulated_effects(event_name, alternate_outcome)
        self.current_timeline["simulated_effects"] = effects
        
        return {
            "message": f"Simulated impact of '{event_name}' changing to '{alternate_outcome}'.",
            "event_name": event_name,
            "alternate_outcome": alternate_outcome,
            "simulated_effects": effects
        }

    def _get_timeline_summary(self, **kwargs) -> Dict:
        if not self.current_timeline:
            return {"message": "No alternate timeline has been simulated yet. Use 'simulate_event' first."}
        
        summary_details = {
            "current_events": {k: v for k, v in self.current_timeline.items() if k != "simulated_effects"},
            "simulated_effects": self.current_timeline.get("simulated_effects", [])
        }
        return {"timeline_summary": summary_details}

    def _list_historical_events(self, **kwargs) -> Dict:
        return {"available_historical_events": self.historical_events}

    def _reset_timeline(self, **kwargs) -> Dict:
        self.current_timeline = {}
        return {"message": "Simulated timeline reset to original history."}

    def _generate_simulated_effects(self, event_name: str, outcome: str) -> List[str]:
        """Generates plausible simulated effects based on the event and outcome."""
        effects = []
        if event_name == "WWII_outcome":
            if outcome == "Axis wins":
                effects.append("Global political landscape drastically altered, new superpowers emerge.")
                effects.append("Technological advancements in certain fields accelerate, others stagnate.")
                effects.append("Different global alliances and economic systems.")
            elif outcome == "Stalemate":
                effects.append("Prolonged global conflict, leading to widespread instability and resource depletion.")
                effects.append("Emergence of new, powerful non-state actors.")
        elif event_name == "Roman_Empire_fall":
            if outcome == "Never falls":
                effects.append("Western civilization develops along a different path, potentially more unified and technologically advanced.")
                effects.append("Latin remains the dominant language across Europe.")
                effects.append("Different religious and philosophical developments.")
            elif outcome == "Falls earlier":
                effects.append("Earlier onset of the Dark Ages, with more fragmented European states.")
                effects.append("Rise of new regional powers in the Mediterranean.")
        elif event_name == "Industrial_Revolution_start":
            if outcome == "Earlier":
                effects.append("Accelerated technological progress, potentially leading to earlier space exploration.")
                effects.append("Earlier onset of environmental challenges.")
            elif outcome == "Later":
                effects.append("Slower technological development, prolonged agrarian societies.")
                effects.append("Different social and political structures persist longer.")
        
        if not effects:
            effects.append("No significant immediate effects simulated for this change.")
        
        return effects