import logging
import json
import random
from typing import Union, List, Dict, Any
from .base_tool import BaseTool

logger = logging.getLogger(__name__)

class SubscriptionManagementSystemTool(BaseTool):
    """
    A tool for simulating subscription management actions.
    """

    def __init__(self, tool_name):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates a subscription management system for creating, canceling, updating, and viewing subscriptions."
        self.subscriptions: Dict[str, Any] = {} # To store simulated subscriptions

    def _create_subscription(self, customer_id: str, plan_id: str, start_date: str) -> str:
        """
        Simulates creating a new subscription for a customer.
        """
        subscription_id = f"sub_{random.randint(1000, 9999)}"  # nosec B311
        self.subscriptions[subscription_id] = {"customer_id": customer_id, "plan_id": plan_id, "start_date": start_date, "status": "active"}
        return f"Simulated: Subscription '{subscription_id}' created for customer '{customer_id}' on plan '{plan_id}'."

    def _cancel_subscription(self, subscription_id: str) -> str:
        """
        Simulates canceling a subscription.
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription '{subscription_id}' not found.")
        self.subscriptions[subscription_id]["status"] = "cancelled"
        return f"Simulated: Subscription '{subscription_id}' cancelled."

    def _update_subscription(self, subscription_id: str, updates: Dict[str, Any]) -> str:
        """
        Simulates updating a subscription.
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription '{subscription_id}' not found.")
        self.subscriptions[subscription_id].update(updates)
        return f"Simulated: Subscription '{subscription_id}' updated."

    def _get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """
        Simulates getting the status of a subscription.
        """
        if subscription_id not in self.subscriptions:
            raise ValueError(f"Subscription '{subscription_id}' not found.")
        return self.subscriptions[subscription_id]

    def _list_subscriptions(self, customer_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """
        Simulates listing all subscriptions.
        """
        filtered_subscriptions = []
        for sub_id, details in self.subscriptions.items():
            if (customer_id is None or details["customer_id"] == customer_id) and \
               (status is None or details["status"] == status):
                filtered_subscriptions.append({"subscription_id": sub_id, **details})
        return filtered_subscriptions

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_subscription", "cancel_subscription", "update_subscription", "get_subscription_status", "list_subscriptions"]},
                "subscription_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "plan_id": {"type": "string"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "updates": {"type": "object", "description": "Key-value pairs for subscription updates."},
                "status": {"type": "string", "enum": ["active", "cancelled", "paused"]}
            },
            "required": ["operation"]
        }

    def execute(self, operation: str, **kwargs: Any) -> Union[str, Dict[str, Any], List[Dict[str, Any]]]:
        if operation == "create_subscription":
            customer_id = kwargs.get('customer_id')
            plan_id = kwargs.get('plan_id')
            start_date = kwargs.get('start_date')
            if not all([customer_id, plan_id, start_date]):
                raise ValueError("Missing 'customer_id', 'plan_id', or 'start_date' for 'create_subscription' operation.")
            return self._create_subscription(customer_id, plan_id, start_date)
        elif operation == "cancel_subscription":
            subscription_id = kwargs.get('subscription_id')
            if not subscription_id:
                raise ValueError("Missing 'subscription_id' for 'cancel_subscription' operation.")
            return self._cancel_subscription(subscription_id)
        elif operation == "update_subscription":
            subscription_id = kwargs.get('subscription_id')
            updates = kwargs.get('updates')
            if not all([subscription_id, updates]):
                raise ValueError("Missing 'subscription_id' or 'updates' for 'update_subscription' operation.")
            return self._update_subscription(subscription_id, updates)
        elif operation == "get_subscription_status":
            subscription_id = kwargs.get('subscription_id')
            if not subscription_id:
                raise ValueError("Missing 'subscription_id' for 'get_subscription_status' operation.")
            return self._get_subscription_status(subscription_id)
        elif operation == "list_subscriptions":
            return self._list_subscriptions(kwargs.get('customer_id'), kwargs.get('status'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SubscriptionManagementSystemTool functionality...")
    
    sub_manager = SubscriptionManagementSystemTool()
    
    try:
        # 1. Create a subscription
        print("\n--- Creating subscription for 'customer_1' ---")
        create_result = sub_manager.execute(operation="create_subscription", customer_id="customer_1", plan_id="premium_monthly", start_date="2025-01-01")
        print(create_result)
        subscription_id = create_result.split("'")[1] # Extract subscription ID

        # 2. Get subscription status
        print(f"\n--- Getting status for subscription '{subscription_id}' ---")
        status = sub_manager.execute(operation="get_subscription_status", subscription_id=subscription_id)
        print(json.dumps(status, indent=2))

        # 3. Update subscription
        print(f"\n--- Updating subscription '{subscription_id}' to paused ---")
        update_result = sub_manager.execute(operation="update_subscription", subscription_id=subscription_id, updates={"status": "paused"})
        print(update_result)

        # 4. List all subscriptions
        print("\n--- Listing all subscriptions ---")
        all_subs = sub_manager.execute(operation="list_subscriptions")
        print(json.dumps(all_subs, indent=2))

        # 5. Cancel subscription
        print(f"\n--- Cancelling subscription '{subscription_id}' ---")
        cancel_result = sub_manager.execute(operation="cancel_subscription", subscription_id=subscription_id)
        print(cancel_result)

    except Exception as e:
        print(f"\nAn error occurred: {e}")