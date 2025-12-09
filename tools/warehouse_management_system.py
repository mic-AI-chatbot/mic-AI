import logging
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated inventory and orders
inventory: Dict[str, Dict[str, Any]] = {}
orders: Dict[str, Dict[str, Any]] = {}

class WarehouseManagementSystemTool(BaseTool):
    """
    A tool to simulate a warehouse management system (WMS).
    """
    def __init__(self, tool_name: str = "warehouse_management_system_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates WMS actions: manage inventory, process orders, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'add_inventory', 'remove_inventory', 'create_order', 'update_order_status', 'get_inventory_report', 'list_orders'."
                },
                "item_id": {"type": "string", "description": "The unique ID of the item."},
                "quantity": {"type": "integer", "description": "The quantity of the item."},
                "location": {"type": "string", "description": "The location in the warehouse (e.g., 'A1', 'B2')."},
                "order_id": {"type": "string", "description": "The unique ID of the order."},
                "customer_id": {"type": "string", "description": "The ID of the customer for the order."},
                "items_in_order": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "item_id": {"type": "string"},
                            "quantity": {"type": "integer"}
                        },
                        "required": ["item_id", "quantity"]
                    },
                    "description": "A list of items and their quantities for an order."
                },
                "new_status": {
                    "type": "string",
                    "description": "The new status for an order ('pending', 'processing', 'shipped', 'delivered', 'cancelled')."
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            item_id = kwargs.get("item_id")
            order_id = kwargs.get("order_id")

            if action in ['add_inventory', 'remove_inventory'] and not item_id:
                raise ValueError(f"'item_id' is required for the '{action}' action.")
            if action in ['create_order', 'update_order_status'] and not order_id:
                raise ValueError(f"'order_id' is required for the '{action}' action.")

            actions = {
                "add_inventory": self._add_inventory,
                "remove_inventory": self._remove_inventory,
                "create_order": self._create_order,
                "update_order_status": self._update_order_status,
                "get_inventory_report": self._get_inventory_report,
                "list_orders": self._list_orders,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WarehouseManagementSystemTool: {e}")
            return {"error": str(e)}

    def _add_inventory(self, item_id: str, quantity: int, location: str = "unknown", **kwargs) -> Dict:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        
        if item_id not in inventory:
            inventory[item_id] = {"quantity": 0, "locations": {}}
        
        inventory[item_id]["quantity"] += quantity
        inventory[item_id]["locations"][location] = inventory[item_id]["locations"].get(location, 0) + quantity
        
        logger.info(f"Added {quantity} of item '{item_id}' to inventory at {location}.")
        return {"message": "Inventory updated.", "item_id": item_id, "total_quantity": inventory[item_id]["quantity"]}

    def _remove_inventory(self, item_id: str, quantity: int, **kwargs) -> Dict:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if item_id not in inventory or inventory[item_id]["quantity"] < quantity:
            raise ValueError(f"Not enough stock for item '{item_id}'. Available: {inventory.get(item_id, {}).get('quantity', 0)}")
        
        inventory[item_id]["quantity"] -= quantity
        # Simple location removal: just reduce total, not specific locations
        # A real WMS would manage specific bin locations
        
        logger.info(f"Removed {quantity} of item '{item_id}' from inventory.")
        return {"message": "Inventory updated.", "item_id": item_id, "total_quantity": inventory[item_id]["quantity"]}

    def _create_order(self, order_id: str, customer_id: str, items_in_order: List[Dict[str, Any]], **kwargs) -> Dict:
        if not all([customer_id, items_in_order]):
            raise ValueError("'customer_id' and 'items_in_order' are required.")
        if order_id in orders:
            raise ValueError(f"Order '{order_id}' already exists.")
        
        # Check inventory before creating order
        for item in items_in_order:
            item_id = item["item_id"]
            quantity = item["quantity"]
            if item_id not in inventory or inventory[item_id]["quantity"] < quantity:
                raise ValueError(f"Not enough stock for item '{item_id}' to create order '{order_id}'.")
        
        new_order = {
            "id": order_id,
            "customer_id": customer_id,
            "items": items_in_order,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "tracking_number": f"TRK-{random.randint(100000, 999999)}"  # nosec B311
        }
        orders[order_id] = new_order
        logger.info(f"Order '{order_id}' created for customer '{customer_id}'.")
        return {"message": "Order created successfully.", "details": new_order}

    def _update_order_status(self, order_id: str, new_status: str, **kwargs) -> Dict:
        if order_id not in orders:
            raise ValueError(f"Order '{order_id}' not found.")
        if new_status not in ["pending", "processing", "shipped", "delivered", "cancelled"]:
            raise ValueError(f"Invalid order status '{new_status}'.")
            
        order = orders[order_id]
        
        # If order is being shipped, deduct from inventory
        if new_status == "shipped" and order["status"] != "shipped":
            for item in order["items"]:
                item_id = item["item_id"]
                quantity = item["quantity"]
                if item_id not in inventory or inventory[item_id]["quantity"] < quantity:
                    raise ValueError(f"Not enough stock for item '{item_id}' to ship order '{order_id}'.")
                inventory[item_id]["quantity"] -= quantity
                # Also update location quantities if needed in a real system
        
        order["status"] = new_status
        order["last_updated"] = datetime.now().isoformat()
        logger.info(f"Order '{order_id}' status updated to '{new_status}'.")
        return {"message": "Order status updated successfully.", "order_id": order_id, "new_status": new_status}

    def _get_inventory_report(self, **kwargs) -> Dict:
        if not inventory:
            return {"message": "Inventory is empty."}
        
        report = []
        for item_id, details in inventory.items():
            report.append({
                "item_id": item_id,
                "total_quantity": details["quantity"],
                "locations": details["locations"]
            })
        return {"inventory_report": report}

    def _list_orders(self, **kwargs) -> Dict:
        if not orders:
            return {"message": "No orders have been created."}
        return {"orders": list(orders.values())}