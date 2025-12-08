import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RMASimulatorTool(BaseTool):
    """
    A tool that simulates Return Merchandise Authorization (RMA) processes,
    allowing for creating RMAs, tracking their status, and processing returns.
    """

    def __init__(self, tool_name: str = "RMASimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.rmas_file = os.path.join(self.data_dir, "rma_records.json")
        # RMA records structure: {rma_id: {order_id: ..., customer_id: ..., product_id: ..., status: ..., reason: ...}}
        self.rma_records: Dict[str, Dict[str, Any]] = self._load_data(self.rmas_file, default={})

    @property
    def description(self) -> str:
        return "Simulates RMA: create, track status, and process returns for merchandise."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_rma", "track_status", "process_return", "list_rmas"]},
                "rma_id": {"type": "string"},
                "order_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "product_id": {"type": "string"},
                "reason": {"type": "string"},
                "outcome": {"type": "string", "enum": ["approved", "rejected", "refunded", "replaced"]},
                "filter_status": {"type": "string", "enum": ["pending", "approved", "rejected", "refunded", "replaced"]}
            },
            "required": ["operation", "rma_id"]
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
        with open(self.rmas_file, 'w') as f: json.dump(self.rma_records, f, indent=2)

    def create_rma(self, rma_id: str, order_id: str, customer_id: str, product_id: str, reason: str) -> Dict[str, Any]:
        """Creates a new RMA record."""
        if rma_id in self.rma_records: raise ValueError(f"RMA '{rma_id}' already exists.")
        
        new_rma = {
            "id": rma_id, "order_id": order_id, "customer_id": customer_id,
            "product_id": product_id, "reason": reason, "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        self.rma_records[rma_id] = new_rma
        self._save_data()
        return new_rma

    def track_status(self, rma_id: str) -> Dict[str, Any]:
        """Retrieves the current status of an RMA."""
        rma = self.rma_records.get(rma_id)
        if not rma: raise ValueError(f"RMA '{rma_id}' not found.")
        return rma

    def process_return(self, rma_id: str, outcome: str) -> Dict[str, Any]:
        """Processes a return, updating the RMA status."""
        rma = self.rma_records.get(rma_id)
        if not rma: raise ValueError(f"RMA '{rma_id}' not found.")
        if rma["status"] != "pending": raise ValueError(f"RMA '{rma_id}' is not pending. Current status: {rma['status']}.")
        
        rma["status"] = outcome
        rma["processed_at"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"RMA '{rma_id}' processed with outcome '{outcome}'."}

    def list_rmas(self, filter_status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all RMAs, optionally filtered by status."""
        filtered_list = list(self.rma_records.values())
        if filter_status:
            filtered_list = [rma for rma in filtered_list if rma["status"] == filter_status]
        return filtered_list

    def execute(self, operation: str, rma_id: str, **kwargs: Any) -> Any:
        if operation == "create_rma":
            order_id = kwargs.get('order_id')
            customer_id = kwargs.get('customer_id')
            product_id = kwargs.get('product_id')
            reason = kwargs.get('reason')
            if not all([order_id, customer_id, product_id, reason]):
                raise ValueError("Missing 'order_id', 'customer_id', 'product_id', or 'reason' for 'create_rma' operation.")
            return self.create_rma(rma_id, order_id, customer_id, product_id, reason)
        elif operation == "track_status":
            # No additional kwargs required for track_status
            return self.track_status(rma_id)
        elif operation == "process_return":
            outcome = kwargs.get('outcome')
            if not outcome:
                raise ValueError("Missing 'outcome' for 'process_return' operation.")
            return self.process_return(rma_id, outcome)
        elif operation == "list_rmas":
            # filter_status is optional, so no strict check needed here
            return self.list_rmas(kwargs.get('filter_status'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RMASimulatorTool functionality...")
    temp_dir = "temp_rma_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    rma_tool = RMASimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create an RMA
        print("\n--- Creating RMA 'RMA-001' ---")
        rma_tool.execute(operation="create_rma", rma_id="RMA-001", order_id="ORD-123", customer_id="CUST-ABC", product_id="PROD-XYZ", reason="Defective item")
        print("RMA created.")

        # 2. Track status
        print("\n--- Tracking status for 'RMA-001' ---")
        status = rma_tool.execute(operation="track_status", rma_id="RMA-001")
        print(json.dumps(status, indent=2))

        # 3. Process return (approve)
        print("\n--- Processing return for 'RMA-001' (approved) ---")
        process_result = rma_tool.execute(operation="process_return", rma_id="RMA-001", outcome="approved")
        print(json.dumps(process_result, indent=2))

        # 4. List all RMAs
        print("\n--- Listing all RMAs ---")
        all_rmas = rma_tool.execute(operation="list_rmas", rma_id="any") # rma_id is not used for list_rmas
        print(json.dumps(all_rmas, indent=2))

        # 5. Create another RMA and reject it
        print("\n--- Creating RMA 'RMA-002' and rejecting it ---")
        rma_tool.execute(operation="create_rma", rma_id="RMA-002", order_id="ORD-456", customer_id="CUST-DEF", product_id="PROD-UVW", reason="Customer changed mind")
        rma_tool.execute(operation="process_return", rma_id="RMA-002", outcome="rejected")
        print("RMA-002 rejected.")

        # 6. List pending RMAs
        print("\n--- Listing pending RMAs ---")
        pending_rmas = rma_tool.execute(operation="list_rmas", rma_id="any", filter_status="pending")
        print(json.dumps(pending_rmas, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")