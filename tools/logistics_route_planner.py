

import logging
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import math

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Pre-defined city coordinates for realistic distance calculation
CITY_COORDINATES = {
    "New York": (40.7128, -74.0060), "Los Angeles": (34.0522, -118.2437),
    "Chicago": (41.8781, -87.6298), "Houston": (29.7604, -95.3698),
    "Phoenix": (33.4484, -112.0740), "Philadelphia": (39.9526, -75.1652),
    "San Antonio": (29.4241, -98.4936), "San Diego": (32.7157, -117.1611),
    "Dallas": (32.7767, -96.7970), "San Jose": (37.3382, -121.8863),
    "London": (51.5074, -0.1278), "Paris": (48.8566, 2.3522),
    "Tokyo": (35.6895, 139.6917), "Denver": (39.7392, -104.9903),
    "Seattle": (47.6062, -122.3321), "San Francisco": (37.7749, -122.4194)
}

class LogisticsRoutePlannerTool(BaseTool):
    """
    A tool for intelligent logistics route planning using realistic distance calculations
    and route optimization heuristics.
    """

    def __init__(self, tool_name: str = "LogisticsRoutePlanner", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.routes_file = os.path.join(self.data_dir, "logistics_routes.json")
        self.routes: Dict[str, Dict[str, Any]] = self._load_data(self.routes_file, default={})

    @property
    def description(self) -> str:
        return "Optimizes logistics routes using realistic distance calculation and waypoint optimization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["optimize_route", "estimate_delivery_time", "list_routes", "get_route_details"]},
                "route_id": {"type": "string"}, "origin": {"type": "string"}, "destination": {"type": "string"},
                "waypoints": {"type": "array", "items": {"type": "string"}},
                "avg_speed_kmh": {"type": "integer", "default": 80}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_routes(self):
        with open(self.routes_file, 'w') as f: json.dump(self.routes, f, indent=4)

    def _haversine_distance(self, city1: str, city2: str) -> float:
        """Calculate distance between two cities using the Haversine formula."""
        lat1, lon1 = CITY_COORDINATES[city1]
        lat2, lon2 = CITY_COORDINATES[city2]
        R = 6371  # Earth radius in kilometers

        dLat, dLon = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def _optimize_waypoints(self, origin: str, destination: str, waypoints: List[str]) -> List[str]:
        """Optimizes waypoint order using a nearest-neighbor heuristic."""
        if not waypoints: return [origin, destination]
        
        path = [origin]
        remaining = set(waypoints)
        current_city = origin

        while remaining:
            next_city = min(remaining, key=lambda city: self._haversine_distance(current_city, city))
            path.append(next_city)
            remaining.remove(next_city)
            current_city = next_city
        
        path.append(destination)
        return path

    def optimize_route(self, route_id: str, origin: str, destination: str,
                       waypoints: Optional[List[str]] = None, avg_speed_kmh: int = 80) -> Dict[str, Any]:
        """Optimizes a route, calculating distance and duration realistically."""
        if not all([route_id, origin, destination]):
            raise ValueError("Route ID, origin, and destination are required.")
        if route_id in self.routes:
            raise ValueError(f"Route with ID '{route_id}' already exists.")
        
        for city in [origin, destination] + (waypoints or []):
            if city not in CITY_COORDINATES:
                raise ValueError(f"Unknown city: '{city}'. Please use one of {list(CITY_COORDINATES.keys())}")

        optimized_path = self._optimize_waypoints(origin, destination, waypoints or [])
        
        total_distance = 0
        for i in range(len(optimized_path) - 1):
            total_distance += self._haversine_distance(optimized_path[i], optimized_path[i+1])

        duration_hours = total_distance / avg_speed_kmh

        new_route = {
            "route_id": route_id, "origin": origin, "destination": destination,
            "waypoints": waypoints or [], "optimized_path": optimized_path,
            "distance_km": round(total_distance, 2),
            "estimated_duration_hours": round(duration_hours, 2),
            "planned_at": datetime.now().isoformat()
        }
        self.routes[route_id] = new_route
        self._save_routes()
        self.logger.info(f"Route '{route_id}' from '{origin}' to '{destination}' optimized.")
        return new_route

    def estimate_delivery_time(self, route_id: str) -> Dict[str, Any]:
        """Estimates delivery time for a planned route."""
        route = self.routes.get(route_id)
        if not route: raise ValueError(f"Route with ID '{route_id}' not found.")
        
        arrival = datetime.fromisoformat(route["planned_at"]) + timedelta(hours=route["estimated_duration_hours"])
        return {
            "route_id": route_id,
            "estimated_arrival_time": arrival.isoformat(),
            "estimated_duration_hours": route["estimated_duration_hours"]
        }

    def list_routes(self, origin: Optional[str] = None, destination: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists planned routes, with optional filters."""
        filtered = list(self.routes.values())
        if origin: filtered = [r for r in filtered if r.get("origin") == origin]
        if destination: filtered = [r for r in filtered if r.get("destination") == destination]
        return filtered

    def get_route_details(self, route_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves details of a specific route."""
        return self.routes.get(route_id)

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "optimize_route": self.optimize_route, "estimate_delivery_time": self.estimate_delivery_time,
            "list_routes": self.list_routes, "get_route_details": self.get_route_details
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating LogisticsRoutePlannerTool functionality...")
    temp_dir = "temp_logistics_data"
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    planner_tool = LogisticsRoutePlannerTool(data_dir=temp_dir)
    
    try:
        # --- Optimize a realistic route ---
        print("\n--- Optimizing route from New York to Los Angeles with waypoints ---")
        route1 = planner_tool.execute(
            operation="optimize_route", route_id="NY_to_LA_001",
            origin="New York", destination="Los Angeles",
            waypoints=["Chicago", "Denver"]
        )
        print(json.dumps(route1, indent=2))

        # --- Estimate Delivery ---
        print("\n--- Estimating delivery for the new route ---")
        estimate = planner_tool.execute(operation="estimate_delivery_time", route_id="NY_to_LA_001")
        print(json.dumps(estimate, indent=2))

        # --- List Routes ---
        print("\n--- Listing all routes originating from New York ---")
        ny_routes = planner_tool.execute(operation="list_routes", origin="New York")
        print(json.dumps(ny_routes, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        import shutil
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
