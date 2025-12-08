import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

DISASTER_EVENTS_FILE = "disaster_events.json"

class DisasterResponseManager:
    """
    A tool for simulating disaster response and management actions.
    It allows for declaring disaster events, allocating resources, and coordinating response tasks.
    Disaster event data and resource allocations are persisted in a local JSON file.
    """

    def __init__(self):
        """
        Initializes the DisasterResponseManager.
        Loads existing disaster event data or creates new ones.
        """
        self.events: Dict[str, Dict[str, Any]] = self._load_events()

    def _load_events(self) -> Dict[str, Dict[str, Any]]:
        """Loads disaster event data from a JSON file."""
        if os.path.exists(DISASTER_EVENTS_FILE):
            with open(DISASTER_EVENTS_FILE, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted events file '{DISASTER_EVENTS_FILE}'. Starting with empty events.")
                    return {}
        return {}

    def _save_events(self) -> None:
        """Saves current disaster event data to a JSON file."""
        with open(DISASTER_EVENTS_FILE, 'w') as f:
            json.dump(self.events, f, indent=4)

    def declare_disaster(self, event_id: str, event_type: str, location: str,
                         severity: str, affected_population: int, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Declares a new simulated disaster event.

        Args:
            event_id: A unique identifier for the disaster event.
            event_type: The type of disaster (e.g., 'earthquake', 'flood', 'hurricane').
            location: The geographical location of the disaster.
            severity: The severity level of the disaster ('low', 'medium', 'high', 'critical').
            affected_population: The estimated number of people affected.
            description: An optional description for the event.

        Returns:
            A dictionary containing the details of the newly declared disaster event.
        """
        if not event_id or not event_type or not location or not severity or affected_population <= 0:
            raise ValueError("Event ID, type, location, severity, and affected population cannot be empty.")
        if event_id in self.events:
            raise ValueError(f"Disaster event with ID '{event_id}' already exists.")
        if severity not in ["low", "medium", "high", "critical"]:
            raise ValueError(f"Invalid severity: '{severity}'.")

        new_event = {
            "event_id": event_id,
            "event_type": event_type,
            "location": location,
            "severity": severity,
            "affected_population": affected_population,
            "description": description,
            "status": "active", # active, resolved, ongoing
            "declared_at": datetime.now().isoformat(),
            "resources_allocated": [],
            "response_tasks": []
        }
        self.events[event_id] = new_event
        self._save_events()
        logger.info(f"Disaster event '{event_id}' ({event_type}) declared at '{location}'.")
        return new_event

    def allocate_resources(self, event_id: str, resource_type: str, quantity: int, destination: str) -> Dict[str, Any]:
        """
        Simulates allocating resources to a disaster event.

        Args:
            event_id: The ID of the disaster event.
            resource_type: The type of resource to allocate (e.g., 'medical_supplies', 'personnel', 'shelter').
            quantity: The quantity of the resource.
            destination: The destination for the allocated resources.

        Returns:
            A dictionary containing the details of the resource allocation.
        """
        event = self.events.get(event_id)
        if not event:
            raise ValueError(f"Disaster event with ID '{event_id}' not found.")
        if event["status"] != "active":
            raise ValueError(f"Cannot allocate resources to inactive event '{event_id}'.")
        if quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        allocation_id = f"ALLOC-{event_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_allocation = {
            "allocation_id": allocation_id,
            "resource_type": resource_type,
            "quantity": quantity,
            "destination": destination,
            "allocated_at": datetime.now().isoformat()
        }
        event["resources_allocated"].append(new_allocation)
        self._save_events()
        logger.info(f"Allocated {quantity} of '{resource_type}' to '{destination}' for event '{event_id}'.")
        return new_allocation

    def coordinate_response(self, event_id: str, task: str, assigned_to: str) -> Dict[str, Any]:
        """
        Simulates coordinating a response task for a disaster event.

        Args:
            event_id: The ID of the disaster event.
            task: The description of the response task (e.g., 'evacuate residents', 'set_up_medical_camp').
            assigned_to: The team or individual assigned to the task.

        Returns:
            A dictionary containing the details of the coordinated task.
        """
        event = self.events.get(event_id)
        if not event:
            raise ValueError(f"Disaster event with ID '{event_id}' not found.")
        if event["status"] != "active":
            raise ValueError(f"Cannot coordinate response for inactive event '{event_id}'.")

        task_id = f"TASK-{event_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(4).hex()}"
        new_task = {
            "task_id": task_id,
            "task_description": task,
            "assigned_to": assigned_to,
            "status": "pending", # pending, in_progress, completed, cancelled
            "coordinated_at": datetime.now().isoformat()
        }
        event["response_tasks"].append(new_task)
        self._save_events()
        logger.info(f"Response task '{task}' assigned to '{assigned_to}' for event '{event_id}'.")
        return new_task

    def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the current status and details of a disaster event.

        Args:
            event_id: The ID of the disaster event.

        Returns:
            A dictionary containing the event's details, or None if not found.
        """
        return self.events.get(event_id)

    def list_disaster_events(self) -> List[Dict[str, Any]]:
        """
        Lists all declared disaster events.

        Returns:
            A list of dictionaries, each representing a disaster event (summary).
        """
        return list(self.events.values())

# Example usage (for direct script execution)
if __name__ == '__main__':
    print("Demonstrating DisasterResponseManager functionality...")

    manager = DisasterResponseManager()

    # Clean up previous state for a fresh demo
    if os.path.exists(DISASTER_EVENTS_FILE):
        os.remove(DISASTER_EVENTS_FILE)
        manager = DisasterResponseManager() # Re-initialize to clear loaded state
        print(f"\nCleaned up {DISASTER_EVENTS_FILE} for fresh demo.")

    # --- Declare Disaster ---
    print("\n--- Declaring Disaster Event 'flood_city_a' ---")
    try:
        event1 = manager.declare_disaster(
            event_id="flood_city_a",
            event_type="flood",
            location="City A",
            severity="high",
            affected_population=10000,
            description="Severe flooding due to heavy rainfall."
        )
        print(json.dumps(event1, indent=2))
    except Exception as e:
        print(f"Declare disaster failed: {e}")

    # --- Allocate Resources ---
    print("\n--- Allocating Resources for 'flood_city_a' ---")
    try:
        alloc1 = manager.allocate_resources("flood_city_a", "medical_supplies", 500, "Central Shelter")
        print(json.dumps(alloc1, indent=2))
        alloc2 = manager.allocate_resources("flood_city_a", "personnel", 20, "Rescue Operations Base")
        print(json.dumps(alloc2, indent=2))
    except Exception as e:
        print(f"Allocate resources failed: {e}")

    # --- Coordinate Response ---
    print("\n--- Coordinating Response for 'flood_city_a' ---")
    try:
        task1 = manager.coordinate_response("flood_city_a", "Evacuate residents from Zone 3", "Rescue Team Alpha")
        print(json.dumps(task1, indent=2))
        task2 = manager.coordinate_response("flood_city_a", "Set up temporary medical camp", "Medical Aid International")
        print(json.dumps(task2, indent=2))
    except Exception as e:
        print(f"Coordinate response failed: {e}")

    # --- Get Event Status ---
    print("\n--- Getting Status for 'flood_city_a' ---")
    event_status = manager.get_event_status("flood_city_a")
    print(json.dumps(event_status, indent=2))

    # --- List Disaster Events ---
    print("\n--- Listing All Disaster Events ---")
    all_events = manager.list_disaster_events()
    print(json.dumps(all_events, indent=2))

    # Clean up
    if os.path.exists(DISASTER_EVENTS_FILE):
        os.remove(DISASTER_EVENTS_FILE)
        print(f"\nCleaned up {DISASTER_EVENTS_FILE}")