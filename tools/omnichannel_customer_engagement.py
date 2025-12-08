import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class OmnichannelCustomerEngagementSimulatorTool(BaseTool):
    """
    A tool that simulates omnichannel customer engagement by managing customer
    interaction history and generating personalized experience suggestions.
    """

    def __init__(self, tool_name: str = "OmnichannelCustomerEngagementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.history_file = os.path.join(self.data_dir, "customer_history.json")
        # Customer history structure: {customer_id: [{type: "message_sent", channel: "email", message: "...", timestamp: "..."}]}
        self.customer_history: Dict[str, List[Dict[str, Any]]] = self._load_data(self.history_file, default={})

    @property
    def description(self) -> str:
        return "Simulates omnichannel customer engagement: send messages, retrieve history, personalize experiences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["send_message", "get_customer_history", "personalize_experience"]},
                "customer_id": {"type": "string"},
                "message": {"type": "string", "description": "The message content to send."},
                "channel": {"type": "string", "enum": ["email", "sms", "chat", "app_notification"], "default": "email"},
                "context": {"type": "object", "description": "Additional context for personalization (e.g., {'last_viewed_category': 'electronics'})."}
            },
            "required": ["operation", "customer_id"]
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
        with open(self.history_file, 'w') as f: json.dump(self.customer_history, f, indent=2)

    def send_message(self, customer_id: str, message: str, channel: str = "email") -> Dict[str, Any]:
        """Simulates sending a message to a customer and records it in their history."""
        self.customer_history.setdefault(customer_id, []).append({
            "type": "message_sent",
            "channel": channel,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
        self._save_data()
        return {"status": "success", "message": f"Simulated: Message sent to '{customer_id}' via '{channel}'."}

    def get_customer_history(self, customer_id: str) -> List[Dict[str, Any]]:
        """Retrieves a customer's interaction history."""
        history = self.customer_history.get(customer_id, [])
        if not history:
            return {"status": "info", "message": f"No history found for customer '{customer_id}'."}
        return history

    def personalize_experience(self, customer_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates a personalized experience suggestion based on history and context."""
        history = self.customer_history.get(customer_id, [])
        
        suggestion = "Based on your general activity, we recommend exploring new arrivals."
        
        # Rule-based personalization based on history
        last_message_channel = None
        last_product_viewed = None
        for entry in reversed(history): # Check recent history
            if entry.get("type") == "message_sent":
                last_message_channel = entry["channel"]
            # Add more sophisticated history analysis here (e.g., product views, purchases)
            # For this simulation, we'll keep it simple.

        if last_message_channel == "email":
            suggestion = "Since you recently interacted via email, we suggest sending a personalized email offer."
        elif last_message_channel == "chat":
            suggestion = "Consider a follow-up chat with a support agent to address recent queries."
        
        # Rule-based personalization based on context
        if context and context.get("last_viewed_category") == "electronics":
            suggestion = "Based on your interest in electronics, here are our latest gadgets."
        elif context and context.get("cart_abandoned"):
            suggestion = "You left items in your cart! Here's a reminder with a discount."

        return {"status": "success", "customer_id": customer_id, "personalization_suggestion": suggestion}

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "send_message": self.send_message,
            "get_customer_history": self.get_customer_history,
            "personalize_experience": self.personalize_experience
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating OmnichannelCustomerEngagementSimulatorTool functionality...")
    temp_dir = "temp_omnichannel_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    engagement_tool = OmnichannelCustomerEngagementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Simulate sending messages to a customer
        print("\n--- Simulating sending messages to 'customer_123' ---")
        engagement_tool.execute(operation="send_message", customer_id="customer_123", message="Welcome to our service!", channel="email")
        engagement_tool.execute(operation="send_message", customer_id="customer_123", message="Your order has shipped!", channel="app_notification")
        print("Messages sent.")

        # 2. Get customer history
        print("\n--- Getting history for 'customer_123' ---")
        history = engagement_tool.execute(operation="get_customer_history", customer_id="customer_123")
        print(json.dumps(history, indent=2))

        # 3. Personalize experience based on history
        print("\n--- Personalizing experience for 'customer_123' (based on history) ---")
        suggestion1 = engagement_tool.execute(operation="personalize_experience", customer_id="customer_123")
        print(json.dumps(suggestion1, indent=2))

        # 4. Personalize experience based on context
        print("\n--- Personalizing experience for 'customer_123' (based on context) ---")
        context = {"last_viewed_category": "electronics", "cart_abandoned": True}
        suggestion2 = engagement_tool.execute(operation="personalize_experience", customer_id="customer_123", context=context)
        print(json.dumps(suggestion2, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")