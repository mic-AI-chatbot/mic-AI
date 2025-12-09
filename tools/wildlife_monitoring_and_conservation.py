import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated species populations and observations
species_populations: Dict[str, Dict[str, Any]] = {
    "lion": {"count": 150, "habitat": "savanna", "conservation_status": "vulnerable", "observations": []},
    "elephant": {"count": 500, "habitat": "forest", "conservation_status": "endangered", "observations": []},
    "zebra": {"count": 1200, "habitat": "grassland", "conservation_status": "least_concern", "observations": []}
}

class WildlifePopulationTrackerTool(BaseTool):
    """
    A tool to simulate tracking wildlife populations and reporting on their status.
    """
    def __init__(self, tool_name: str = "wildlife_population_tracker_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates tracking wildlife populations: record observations, get reports, and list species."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'record_observation', 'get_report', 'list_species'."
                },
                "species_name": {"type": "string", "description": "The name of the species (e.g., 'lion', 'elephant')."},
                "count": {"type": "integer", "description": "The number of individuals observed."},
                "location": {"type": "string", "description": "The location of the observation (e.g., 'Serengeti National Park')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            species_name = kwargs.get("species_name")

            if action in ['record_observation', 'get_report'] and not species_name:
                raise ValueError(f"'species_name' is required for the '{action}' action.")

            actions = {
                "record_observation": self._record_observation,
                "get_report": self._get_population_report,
                "list_species": self._list_species,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WildlifePopulationTrackerTool: {e}")
            return {"error": str(e)}

    def _record_observation(self, species_name: str, count: int, location: str, **kwargs) -> Dict:
        if species_name not in species_populations:
            raise ValueError(f"Species '{species_name}' not tracked. Use 'list_species' to see available species.")
        if count <= 0:
            raise ValueError("Observation count must be positive.")
            
        species = species_populations[species_name]
        species["count"] += count # Simple update
        species["observations"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "count": count,
            "location": location
        })
        logger.info(f"Recorded {count} '{species_name}' at '{location}'.")
        return {"message": "Observation recorded successfully.", "species_name": species_name, "new_count": species["count"]}

    def _get_population_report(self, species_name: str, **kwargs) -> Dict:
        if species_name not in species_populations:
            raise ValueError(f"Species '{species_name}' not tracked.")
            
        species = species_populations[species_name]
        
        # Simulate trend based on recent observations
        trend = "stable"
        if len(species["observations"]) > 1:
            latest_obs_count = species["observations"][-1]["count"]
            previous_obs_count = species["observations"][-2]["count"]
            if latest_obs_count > previous_obs_count:
                trend = "increasing"
            elif latest_obs_count < previous_obs_count:
                trend = "decreasing"

        return {
            "species_name": species_name,
            "current_count": species["count"],
            "habitat": species["habitat"],
            "conservation_status": species["conservation_status"],
            "population_trend": trend,
            "last_5_observations": species["observations"][-5:]
        }

    def _list_species(self, **kwargs) -> Dict:
        return {"tracked_species": species_populations}