import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated virtual tours
virtual_tours: Dict[str, Dict[str, Any]] = {}

class VirtualTourCreatorTool(BaseTool):
    """
    A tool to simulate the creation and management of virtual tours.
    """
    def __init__(self, tool_name: str = "virtual_tour_creator_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates creating, getting details, and listing virtual tours with scenes."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_tour', 'get_details', 'list_tours'."
                },
                "tour_name": {"type": "string", "description": "The unique name for the virtual tour."},
                "locations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of key locations/points of interest for the tour."
                },
                "navigation_type": {
                    "type": "string",
                    "description": "The simulated navigation type (e.g., 'panoramic', 'walkthrough').",
                    "default": "panoramic"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            tour_name = kwargs.get("tour_name")

            if action in ['create_tour', 'get_details'] and not tour_name:
                raise ValueError(f"'tour_name' is required for the '{action}' action.")

            actions = {
                "create_tour": self._create_tour,
                "get_details": self._get_tour_details,
                "list_tours": self._list_tours,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VirtualTourCreatorTool: {e}")
            return {"error": str(e)}

    def _create_tour(self, tour_name: str, locations: List[str], navigation_type: str = "panoramic", **kwargs) -> Dict:
        if not locations:
            raise ValueError("'locations' cannot be empty for creating a tour.")
        
        if tour_name in virtual_tours:
            raise ValueError(f"A tour with the name '{tour_name}' already exists.")

        logger.info(f"Creating virtual tour '{tour_name}'.")
        
        # Simulate generating scenes for the tour
        scenes = []
        for i, loc in enumerate(locations):
            scenes.append({
                "scene_id": f"scene_{i+1}",
                "location": loc,
                "description": f"A panoramic view of {loc}.",
                "hotspots": [f"info_point_{random.randint(1,3)}", f"nav_to_scene_{random.randint(1, len(locations))}"],  # nosec B311
                "media_url": f"https://simulated.tour.com/media/{loc.replace(' ', '_')}.jpg"
            })

        simulated_preview_url = f"https://simulated.tour.com/{tour_name.replace(' ', '_')}"
        new_tour = {
            "tour_name": tour_name,
            "locations": locations,
            "navigation_type": navigation_type,
            "status": "created",
            "preview_url": simulated_preview_url,
            "scenes": scenes
        }
        virtual_tours[tour_name] = new_tour
        
        return {"message": "Virtual tour created successfully.", "details": new_tour}

    def _get_tour_details(self, tour_name: str, **kwargs) -> Dict:
        if tour_name not in virtual_tours:
            raise ValueError(f"Tour '{tour_name}' not found.")
        return {"tour_details": virtual_tours[tour_name]}

    def _list_tours(self, **kwargs) -> Dict:
        if not virtual_tours:
            return {"message": "No virtual tours have been created yet."}
        
        summary = {
            name: {
                "locations": tour["locations"],
                "navigation_type": tour["navigation_type"],
                "num_scenes": len(tour["scenes"])
            } for name, tour in virtual_tours.items()
        }
        return {"virtual_tours": summary}