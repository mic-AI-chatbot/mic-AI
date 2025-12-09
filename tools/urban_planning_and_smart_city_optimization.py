import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class UrbanPlanningTool(BaseTool):
    """
    A tool to simulate urban planning and smart city optimizations,
    focusing on traffic flow.
    """
    def __init__(self, tool_name: str = "urban_planning_and_smart_city_optimization_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates traffic flow optimization for a set of city intersections."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "intersections_data": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "intersection_id": {"type": "string"},
                            "traffic_volume": {"type": "number", "description": "Vehicles per hour."},
                            "current_green_light_seconds": {"type": "integer", "description": "Duration of green light for the main direction."}
                        },
                        "required": ["intersection_id", "traffic_volume", "current_green_light_seconds"]
                    },
                    "description": "A list of intersections with their current traffic data."
                },
                "optimization_goal": {
                    "type": "string",
                    "description": "The goal of the optimization ('reduce_congestion' or 'promote_pedestrian_flow').",
                    "default": "reduce_congestion"
                }
            },
            "required": ["intersections_data"]
        }

    def execute(self, intersections_data: List[Dict[str, Any]], optimization_goal: str = "reduce_congestion", **kwargs) -> Dict:
        """
        Analyzes traffic data and suggests optimized traffic light timings.
        """
        if not intersections_data:
            return {"error": "Intersections data cannot be empty."}

        try:
            logger.info(f"Running traffic optimization for {len(intersections_data)} intersections with goal: {optimization_goal}")
            
            optimized_timings = []
            for intersection in intersections_data:
                optimized_timing = self._simulate_optimization(intersection, optimization_goal)
                optimized_timings.append(optimized_timing)

            return {
                "message": "Traffic optimization simulation complete.",
                "optimization_goal": optimization_goal,
                "suggested_adjustments": optimized_timings
            }

        except Exception as e:
            logger.error(f"An error occurred in UrbanPlanningTool: {e}")
            return {"error": str(e)}

    def _simulate_optimization(self, intersection: Dict[str, Any], goal: str) -> Dict[str, Any]:
        """
        Simulates the optimization logic for a single intersection.
        """
        intersection_id = intersection["intersection_id"]
        volume = intersection["traffic_volume"]
        current_timing = intersection["current_green_light_seconds"]
        
        suggested_timing = current_timing
        
        if goal == 'reduce_congestion':
            # Simple logic: more traffic means longer green light
            if volume > 1000:
                suggested_timing = int(current_timing * 1.2) # Increase by 20%
            elif volume < 200:
                suggested_timing = int(current_timing * 0.8) # Decrease by 20%
        
        elif goal == 'promote_pedestrian_flow':
            # Shorter green lights for cars to allow more pedestrian crossing time
            suggested_timing = int(current_timing * 0.75) # Decrease by 25%
        
        # Ensure timings are within a reasonable range
        suggested_timing = max(20, min(120, suggested_timing))

        return {
            "intersection_id": intersection_id,
            "current_green_light_seconds": current_timing,
            "suggested_green_light_seconds": suggested_timing,
            "change_reason": f"Adjusted based on traffic volume ({volume} vph) and goal ('{goal}')."
        }