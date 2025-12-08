import logging
import json
from typing import List, Dict, Any
from collections import Counter

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class UserInterfaceManager:
    """Manages the state of user interfaces and behavior history."""
    def __init__(self, tool_name):
        self.user_ui_data: Dict[str, Any] = {
            "user_1": {"theme": "dark", "layout": "compact", "shortcuts": []},
            "user_2": {"theme": "light", "layout": "spacious", "shortcuts": []},
        }
        self.user_behavior_history: Dict[str, List[Dict[str, Any]]] = {
            "user_1": [
                {"action": "click", "element": "button_1"},
                {"action": "click", "element": "button_1"},
                {"action": "click", "element": "button_3"},
            ],
            "user_2": [
                {"action": "click", "element": "button_2"},
                {"action": "scroll", "element": "list_2"},
            ],
        }

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        return self.user_ui_data.get(user_id, {"error": f"User with ID '{user_id}' not found."})

    def adapt_ui_for_context(self, user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if user_id not in self.user_ui_data:
            self.user_ui_data[user_id] = {"theme": "default", "layout": "default", "shortcuts": []}

        # Rule-based adaptation based on context
        if context.get("time_of_day") in ["evening", "night"]:
            self.user_ui_data[user_id]["theme"] = "dark"
        else:
            self.user_ui_data[user_id]["theme"] = "light"

        if context.get("device_type") == "mobile":
            self.user_ui_data[user_id]["layout"] = "compact"
        else:
            self.user_ui_data[user_id]["layout"] = "spacious"
            
        return self.user_ui_data[user_id]

    def get_behavior_history(self, user_id: str) -> List[Dict[str, Any]]:
        return self.user_behavior_history.get(user_id, [])

    def add_shortcut(self, user_id: str, shortcut: str):
        if user_id in self.user_ui_data:
            if shortcut not in self.user_ui_data[user_id]["shortcuts"]:
                self.user_ui_data[user_id]["shortcuts"].append(shortcut)

# Instantiate the manager to hold the state
ui_manager = UserInterfaceManager()

class AdaptUIForContextTool(BaseTool):
    """Adapts the UI based on the user's current context."""
    def __init__(self, tool_name="adapt_ui_for_context"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adapts the UI theme and layout for a user based on their current context (e.g., time of day, device)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user."},
                "context": {
                    "type": "object",
                    "properties": {
                        "time_of_day": {"type": "string", "enum": ["morning", "afternoon", "evening", "night"]},
                        "device_type": {"type": "string", "enum": ["desktop", "mobile"]}
                    },
                    "description": "The user's current context."
                }
            },
            "required": ["user_id", "context"]
        }

    def execute(self, user_id: str, context: Dict[str, Any], **kwargs: Any) -> str:
        new_preferences = ui_manager.adapt_ui_for_context(user_id, context)
        report = {
            "message": f"UI for user '{user_id}' adapted based on context.",
            "new_preferences": new_preferences
        }
        return json.dumps(report, indent=2)

class PersonalizeUIFromHistoryTool(BaseTool):
    """Personalizes the UI by adding shortcuts based on user's past behavior."""
    def __init__(self, tool_name="personalize_ui_from_history"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a user's behavior history to suggest and apply UI personalizations, like adding shortcuts for frequently used elements."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user to personalize the UI for."}
            },
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        history = ui_manager.get_behavior_history(user_id)
        if not history:
            return json.dumps({"message": "Not enough behavior history to personalize."}, indent=2)

        # Find the most frequently clicked element
        click_actions = [item["element"] for item in history if item["action"] == "click"]
        if not click_actions:
            return json.dumps({"message": "No click actions found in history to personalize."}, indent=2)

        most_common_element = Counter(click_actions).most_common(1)[0][0]
        
        # Add the most common element as a shortcut
        ui_manager.add_shortcut(user_id, most_common_element)
        
        report = {
            "message": f"Personalization applied for user '{user_id}'.",
            "suggestion": f"Added a shortcut for the frequently used element: '{most_common_element}'.",
            "new_preferences": ui_manager.get_preferences(user_id)
        }
        return json.dumps(report, indent=2)

class GetUserPreferencesTool(BaseTool):
    """Gets the current UI preferences for a user."""
    def __init__(self, tool_name="get_user_preferences"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current UI preferences for a specified user, including theme, layout, and shortcuts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user to get preferences for."}
            },
            "required": ["user_id"]
        }

    def execute(self, user_id: str, **kwargs: Any) -> str:
        preferences = ui_manager.get_preferences(user_id)
        return json.dumps(preferences, indent=2)