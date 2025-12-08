import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

CUSTOMER_LOYALTY_FILE = Path("customer_loyalty_data.json")
LOYALTY_REWARDS_FILE = Path("loyalty_rewards.json")

class LoyaltyProgramManager:
    """Manages customer loyalty data, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CUSTOMER_LOYALTY_FILE):
        if cls._instance is None:
            cls._instance = super(LoyaltyProgramManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.loyalty_data: Dict[str, Any] = cls._instance._load_loyalty_data()
        return cls._instance

    def _load_loyalty_data(self) -> Dict[str, Any]:
        """Loads customer loyalty data from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty loyalty data.")
                return {}
            except Exception as e:
                logger.error(f"Error loading loyalty data from {self.file_path}: {e}")
                return {}
        return {}

    def _save_loyalty_data(self) -> None:
        """Saves customer loyalty data to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.loyalty_data, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving loyalty data to {self.file_path}: {e}")

    def enroll_customer(self, customer_id: str, initial_points: int = 0) -> bool:
        if customer_id in self.loyalty_data:
            return False
        self.loyalty_data[customer_id] = {
            "points": initial_points,
            "tier": "bronze", # Default tier
            "enrolled_at": datetime.now().isoformat() + "Z"
        }
        self._save_loyalty_data()
        return True

    def add_points(self, customer_id: str, points: int) -> bool:
        if customer_id not in self.loyalty_data:
            return False
        self.loyalty_data[customer_id]["points"] += points
        self._save_loyalty_data()
        return True

    def deduct_points(self, customer_id: str, points: int) -> bool:
        if customer_id not in self.loyalty_data or self.loyalty_data[customer_id]["points"] < points:
            return False
        self.loyalty_data[customer_id]["points"] -= points
        self._save_loyalty_data()
        return True

    def get_customer_loyalty_status(self, customer_id: str) -> Optional[Dict[str, Any]]:
        return self.loyalty_data.get(customer_id)

loyalty_program_manager = LoyaltyProgramManager()

class RewardManager:
    """Manages loyalty rewards, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = LOYALTY_REWARDS_FILE):
        if cls._instance is None:
            cls._instance = super(RewardManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.rewards: Dict[str, Any] = cls._instance._load_rewards()
        return cls._instance

    def _load_rewards(self) -> Dict[str, Any]:
        """Loads loyalty rewards from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty rewards.")
                return {}
            except Exception as e:
                logger.error(f"Error loading rewards from {self.file_path}: {e}")
                return {}
        # Initial dummy data if file doesn't exist
        return {
            "discount_10": {"name": "10% Off Discount", "points_cost": 100, "description": "Get 10% off your next purchase."},
            "free_shipping": {"name": "Free Shipping", "points_cost": 50, "description": "Free standard shipping on your next order."},
            "gift_card_25": {"name": "$25 Gift Card", "points_cost": 500, "description": "A $25 gift card for future purchases."}
        }

    def _save_rewards(self) -> None:
        """Saves loyalty rewards to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.rewards, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving rewards to {self.file_path}: {e}")

    def define_reward(self, reward_id: str, name: str, points_cost: int, description: str) -> bool:
        if reward_id in self.rewards:
            return False
        self.rewards[reward_id] = {
            "name": name,
            "points_cost": points_cost,
            "description": description,
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_rewards()
        return True

    def get_reward(self, reward_id: str) -> Optional[Dict[str, Any]]:
        return self.rewards.get(reward_id)

    def list_rewards(self) -> List[Dict[str, Any]]:
        return [{"reward_id": r_id, "name": details['name'], "points_cost": details['points_cost'], "created_at": details['created_at']} for r_id, details in self.rewards.items()]

reward_manager = RewardManager()

class EnrollCustomerTool(BaseTool):
    """Enrolls a new customer in the loyalty program."""
    def __init__(self, tool_name="enroll_customer"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Enrolls a new customer in the loyalty program, optionally with initial points."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "A unique ID for the customer."},
                "initial_points": {"type": "integer", "description": "Initial points to grant the customer.", "default": 0}
            },
            "required": ["customer_id"]
        }

    def execute(self, customer_id: str, initial_points: int = 0, **kwargs: Any) -> str:
        success = loyalty_program_manager.enroll_customer(customer_id, initial_points)
        if success:
            report = {"message": f"Customer '{customer_id}' enrolled in loyalty program with {initial_points} points."}
        else:
            report = {"error": f"Customer '{customer_id}' is already enrolled. Cannot enroll again."}
        return json.dumps(report, indent=2)

class AddPointsTool(BaseTool):
    """Adds points to a customer's loyalty account."""
    def __init__(self, tool_name="add_points"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a specified number of points to a customer's loyalty account."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The ID of the customer."},
                "points": {"type": "integer", "description": "The number of points to add."}
            },
            "required": ["customer_id", "points"]
        }

    def execute(self, customer_id: str, points: int, **kwargs: Any) -> str:
        success = loyalty_program_manager.add_points(customer_id, points)
        if success:
            report = {"message": f"{points} points added to customer '{customer_id}'s account."}
        else:
            report = {"error": f"Customer '{customer_id}' not found or not enrolled in loyalty program."}
        return json.dumps(report, indent=2)

class DefineRewardTool(BaseTool):
    """Defines a new loyalty reward."""
    def __init__(self, tool_name="define_reward"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Defines a new loyalty reward with a unique ID, name, points cost, and description."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reward_id": {"type": "string", "description": "A unique ID for the reward."},
                "name": {"type": "string", "description": "The name of the reward."},
                "points_cost": {"type": "integer", "description": "The number of points required to redeem this reward."},
                "description": {"type": "string", "description": "A brief description of the reward."}
            },
            "required": ["reward_id", "name", "points_cost", "description"]
        }

    def execute(self, reward_id: str, name: str, points_cost: int, description: str, **kwargs: Any) -> str:
        success = reward_manager.define_reward(reward_id, name, points_cost, description)
        if success:
            report = {"message": f"Reward '{name}' (ID: {reward_id}) defined successfully."}
        else:
            report = {"error": f"Reward '{reward_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class ListRewardsTool(BaseTool):
    """Lists all available loyalty rewards."""
    def __init__(self, tool_name="list_rewards"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Lists all available loyalty rewards, showing their ID, name, and points cost."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        rewards = reward_manager.list_rewards()
        if not rewards:
            return json.dumps({"message": "No loyalty rewards found."})
        
        return json.dumps({"total_rewards": len(rewards), "rewards": rewards}, indent=2)

class RedeemRewardTool(BaseTool):
    """Redeems a loyalty reward for a customer."""
    def __init__(self, tool_name="redeem_reward"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Redeems a loyalty reward for a customer using their accumulated points."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "The ID of the customer redeeming the reward."},
                "reward_id": {"type": "string", "description": "The ID of the reward to redeem."}
            },
            "required": ["customer_id", "reward_id"]
        }

    def execute(self, customer_id: str, reward_id: str, **kwargs: Any) -> str:
        customer_loyalty = loyalty_program_manager.get_customer_loyalty_status(customer_id)
        if not customer_loyalty:
            return json.dumps({"error": f"Customer '{customer_id}' not found or not enrolled in loyalty program."})
        
        reward = reward_manager.get_reward(reward_id)
        if not reward:
            return json.dumps({"error": f"Reward '{reward_id}' not found."})
            
        reward_cost = reward["points_cost"]
        
        if customer_loyalty["points"] < reward_cost:
            return json.dumps({"error": f"Customer '{customer_id}' has insufficient points to redeem '{reward['name']}'. Required: {reward_cost}, Available: {customer_loyalty['points']}."})
            
        success = loyalty_program_manager.deduct_points(customer_id, reward_cost)
        if success:
            updated_loyalty = loyalty_program_manager.get_customer_loyalty_status(customer_id)
            report = {
                "message": f"Customer '{customer_id}' successfully redeemed '{reward['name']}'.",
                "reward_id": reward_id,
                "reward_name": reward["name"],
                "points_redeemed": reward_cost,
                "current_points": updated_loyalty["points"]
            }
        else:
            report = {"error": f"Failed to redeem reward for customer '{customer_id}'. An unexpected error occurred."}
        return json.dumps(report, indent=2)

class GetCustomerLoyaltyStatusTool(BaseTool):
    """Retrieves a customer's loyalty status."""
    def __init__(self, tool_name="get_customer_loyalty_status"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves a customer's loyalty status, including their current points and tier."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"customer_id": {"type": "string", "description": "The ID of the customer to retrieve loyalty status for."}},
            "required": ["customer_id"]
        }

    def execute(self, customer_id: str, **kwargs: Any) -> str:
        loyalty_status = loyalty_program_manager.get_customer_loyalty_status(customer_id)
        if not loyalty_status:
            return json.dumps({"error": f"Customer '{customer_id}' not found or not enrolled in loyalty program."})
            
        return json.dumps(loyalty_status, indent=2)
