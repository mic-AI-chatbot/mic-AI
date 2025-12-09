import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ShippingTrackingSimulatorTool(BaseTool):
    """
    A tool that simulates shipping tracking integration, allowing for creating
    shipments, tracking their status, and getting delivery updates.
    """

    def __init__(self, tool_name: str = "ShippingTrackingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.shipments_file = os.path.join(self.data_dir, "shipment_records.json")
        
        # Shipment records: {tracking_number: {carrier: ..., origin: ..., destination: ..., status: ..., current_location: ..., estimated_delivery_date: ...}}
        self.shipment_records: Dict[str, Dict[str, Any]] = self._load_data(self.shipments_file, default={})

    @property
    def description(self) -> str:
        return "Simulates shipping tracking: create shipments, track status, and get delivery updates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_shipment", "track_shipment", "get_delivery_status", "list_shipments"]},
                "tracking_number": {"type": "string"},
                "carrier": {"type": "string", "enum": ["UPS", "FedEx", "DHL", "USPS"]},
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "status": {"type": "string", "enum": ["pending", "in_transit", "out_for_delivery", "delivered", "exception"]},
                "filter_status": {"type": "string", "enum": ["pending", "in_transit", "out_for_delivery", "delivered", "exception"]}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.shipments_file, 'w') as f: json.dump(self.shipment_records, f, indent=2)

    def create_shipment(self, tracking_number: str, carrier: str, origin: str, destination: str, status: str = "pending") -> Dict[str, Any]:
        """Creates a new shipment record."""
        if tracking_number in self.shipment_records: raise ValueError(f"Shipment '{tracking_number}' already exists.")
        
        estimated_delivery_date = (datetime.now() + timedelta(days=random.randint(3, 10))).strftime("%Y-%m-%d")  # nosec B311
        
        new_shipment = {
            "id": tracking_number, "carrier": carrier, "origin": origin, "destination": destination,
            "status": status, "current_location": origin, "estimated_delivery_date": estimated_delivery_date,
            "created_at": datetime.now().isoformat()
        }
        self.shipment_records[tracking_number] = new_shipment
        self._save_data()
        return new_shipment

    def track_shipment(self, tracking_number: str) -> Dict[str, Any]:
        """Simulates tracking a shipment and updates its status and location."""
        shipment = self.shipment_records.get(tracking_number)
        if not shipment: raise ValueError(f"Shipment '{tracking_number}' not found. Create it first.")
        
        # Simulate status progression
        if shipment["status"] == "pending":
            shipment["status"] = "in_transit"
            shipment["current_location"] = "Transit Hub A"
        elif shipment["status"] == "in_transit":
            if random.random() < 0.7: # 70% chance to move to next hub  # nosec B311
                shipment["current_location"] = random.choice(["Transit Hub B", "Regional Sort Facility"])  # nosec B311
            else: # 30% chance to go out for delivery
                shipment["status"] = "out_for_delivery"
                shipment["current_location"] = shipment["destination"]
        elif shipment["status"] == "out_for_delivery":
            shipment["status"] = "delivered"
            shipment["current_location"] = shipment["destination"]
            shipment["actual_delivery_date"] = datetime.now().strftime("%Y-%m-%d")
        
        shipment["last_tracked_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"Shipment '{tracking_number}' status updated to '{shipment['status']}'."}

    def get_delivery_status(self, tracking_number: str) -> Dict[str, Any]:
        """Retrieves the current delivery status of a shipment."""
        shipment = self.shipment_records.get(tracking_number)
        if not shipment: raise ValueError(f"Shipment '{tracking_number}' not found.")
        
        return {
            "status": "success", "tracking_number": tracking_number,
            "current_status": shipment["status"],
            "current_location": shipment["current_location"],
            "estimated_delivery_date": shipment["estimated_delivery_date"],
            "actual_delivery_date": shipment.get("actual_delivery_date", "N/A")
        }

    def list_shipments(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all shipments, optionally filtered by status."""
        filtered_list = list(self.shipment_records.values())
        if filter_status:
            filtered_list = [s for s in filtered_list if s["status"] == filter_status]
        return filtered_list

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_shipment":
            tracking_number = kwargs.get('tracking_number')
            carrier = kwargs.get('carrier')
            origin = kwargs.get('origin')
            destination = kwargs.get('destination')
            if not all([tracking_number, carrier, origin, destination]):
                raise ValueError("Missing 'tracking_number', 'carrier', 'origin', or 'destination' for 'create_shipment' operation.")
            return self.create_shipment(tracking_number, carrier, origin, destination, kwargs.get('status', 'pending'))
        elif operation == "track_shipment":
            tracking_number = kwargs.get('tracking_number')
            if not tracking_number:
                raise ValueError("Missing 'tracking_number' for 'track_shipment' operation.")
            return self.track_shipment(tracking_number)
        elif operation == "get_delivery_status":
            tracking_number = kwargs.get('tracking_number')
            if not tracking_number:
                raise ValueError("Missing 'tracking_number' for 'get_delivery_status' operation.")
            return self.get_delivery_status(tracking_number)
        elif operation == "list_shipments":
            # filter_status is optional, so no strict check needed here
            return self.list_shipments(kwargs.get('filter_status'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating ShippingTrackingSimulatorTool functionality...")
    temp_dir = "temp_shipping_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    shipping_tool = ShippingTrackingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a shipment
        print("\n--- Creating shipment 'TRK-001' ---")
        shipping_tool.execute(operation="create_shipment", tracking_number="TRK-001", carrier="UPS", origin="New York", destination="Los Angeles")
        print("Shipment created.")

        # 2. Track the shipment multiple times
        print("\n--- Tracking shipment 'TRK-001' (multiple times) ---")
        for _ in range(3):
            track_result = shipping_tool.execute(operation="track_shipment", tracking_number="TRK-001")
            print(json.dumps(track_result, indent=2))

        # 3. Get delivery status
        print("\n--- Getting delivery status for 'TRK-001' ---")
        status = shipping_tool.execute(operation="get_delivery_status", tracking_number="TRK-001")
        print(json.dumps(status, indent=2))

        # 4. Create another shipment
        print("\n--- Creating shipment 'TRK-002' ---")
        shipping_tool.execute(operation="create_shipment", tracking_number="TRK-002", carrier="FedEx", origin="Chicago", destination="Miami", status="in_transit")
        print("Shipment created.")

        # 5. List all shipments
        print("\n--- Listing all shipments ---")
        all_shipments = shipping_tool.execute(operation="list_shipments", tracking_number="any") # tracking_number is not used for list_shipments
        print(json.dumps(all_shipments, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")