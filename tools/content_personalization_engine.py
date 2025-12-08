import logging
import json
import random
import os
from datetime import datetime
from typing import Union, List, Dict, Any, Optional
from pathlib import Path
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

USER_PROFILES_FILE = Path("user_profiles.json")
CONTENT_ITEMS_FILE = Path("content_items.json")

class UserProfileManager:
    """Manages user profiles, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = USER_PROFILES_FILE):
        if cls._instance is None:
            cls._instance = super(UserProfileManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.profiles: Dict[str, Any] = cls._instance._load_profiles()
        return cls._instance

    def _load_profiles(self) -> Dict[str, Any]:
        """Loads user profiles from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty profiles.")
                return {}
            except Exception as e:
                logger.error(f"Error loading profiles from {self.file_path}: {e}")
                return {}
        return {}

    def _save_profiles(self) -> None:
        """Saves user profiles to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving profiles to {self.file_path}: {e}")

    def create_profile(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        if user_id in self.profiles:
            return False
        self.profiles[user_id] = {
            "preferences": preferences,
            "engagement_history": [],
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_profiles()
        return True

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.profiles.get(user_id)

    def track_engagement(self, user_id: str, item_id: str, engagement_type: str, item_topics: List[str], item_sentiment: str) -> bool:
        if user_id not in self.profiles:
            return False
        
        self.profiles[user_id]["engagement_history"].append({
            "item_id": item_id,
            "engagement_type": engagement_type,
            "timestamp": datetime.now().isoformat() + "Z"
        })

        # Update user preferences based on engagement (simple simulation)
        if engagement_type in ["click", "like", "share"]:
            for topic in item_topics:
                if topic not in self.profiles[user_id]["preferences"].get("topics", []):
                    self.profiles[user_id]["preferences"].setdefault("topics", []).append(topic)
            # Simple sentiment update
            if item_sentiment == "positive":
                self.profiles[user_id]["preferences"]["sentiment"] = "positive"
            elif item_sentiment == "negative":
                self.profiles[user_id]["preferences"]["sentiment"] = "negative"

        self._save_profiles()
        return True

user_profile_manager = UserProfileManager()

class ContentItemManager:
    """Manages content items, with JSON file persistence."""
    _instance = None

    def __new__(cls, file_path: Path = CONTENT_ITEMS_FILE):
        if cls._instance is None:
            cls._instance = super(ContentItemManager, cls).__new__(cls)
            cls._instance.file_path = file_path
            cls._instance.items: Dict[str, Any] = cls._instance._load_items()
        return cls._instance

    def _load_items(self) -> Dict[str, Any]:
        """Loads content items from a JSON file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {self.file_path}. Returning empty items.")
                return {}
            except Exception as e:
                logger.error(f"Error loading items from {self.file_path}: {e}")
                return {}
        # Initial dummy data if file doesn't exist
        return {
            "article_1": {"title": "The Future of AI", "topics": ["AI", "Technology"], "sentiment": "positive", "type": "article"},
            "article_2": {"title": "Healthy Eating Tips", "topics": ["Health", "Lifestyle"], "sentiment": "neutral", "type": "article"},
            "ad_1": {"title": "New Smartphone Launch", "topics": ["Technology", "Gadgets"], "sentiment": "positive", "type": "ad"},
            "article_3": {"title": "Cooking with Python", "topics": ["Technology", "Food"], "sentiment": "neutral", "type": "article"},
            "recommendation_1": {"title": "Top 10 Travel Destinations", "topics": ["Travel", "Lifestyle"], "sentiment": "positive", "type": "recommendation"}
        }

    def _save_items(self) -> None:
        """Saves content items to a JSON file."""
        try:
            os.makedirs(self.file_path.parent, exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.items, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving items to {self.file_path}: {e}")

    def add_item(self, item_id: str, title: str, topics: List[str], sentiment: str, item_type: str) -> bool:
        if item_id in self.items:
            return False
        self.items[item_id] = {
            "title": title,
            "topics": topics,
            "sentiment": sentiment,
            "type": item_type,
            "created_at": datetime.now().isoformat() + "Z"
        }
        self._save_items()
        return True

    def get_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self.items.get(item_id)

    def list_items(self, item_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not item_type:
            return [{"item_id": item_id, "title": details['title'], "type": details['type'], "topics": details['topics']} for item_id, details in self.items.items()]
        
        filtered_list = []
        for item_id, details in self.items.items():
            if details['type'] == item_type:
                filtered_list.append({"item_id": item_id, "title": details['title'], "type": details['type'], "topics": details['topics']})
        return filtered_list

content_item_manager = ContentItemManager()

class CreateUserProfileTool(BaseTool):
    """Creates a new user profile for content personalization."""
    def __init__(self, tool_name="create_user_profile"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new user profile with specified preferences for content personalization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "A unique ID for the user."},
                "preferred_topics": {"type": "array", "items": {"type": "string"}, "description": "A list of topics the user prefers (e.g., ['AI', 'Technology']).", "default": []},
                "preferred_sentiment": {"type": "string", "description": "The user's preferred sentiment for content.", "enum": ["positive", "negative", "neutral"], "default": "neutral"}
            },
            "required": ["user_id"]
        }

    def execute(self, user_id: str, preferred_topics: List[str] = None, preferred_sentiment: str = "neutral", **kwargs: Any) -> str:
        if preferred_topics is None: preferred_topics = []
        preferences = {"topics": preferred_topics, "sentiment": preferred_sentiment}
        success = user_profile_manager.create_profile(user_id, preferences)
        if success:
            report = {"message": f"User profile for '{user_id}' created successfully."}
        else:
            report = {"error": f"User profile for '{user_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class AddContentItemTool(BaseTool):
    """Adds a new content item to the personalization engine."""
    def __init__(self, tool_name="add_content_item"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Adds a new content item (e.g., article, ad, recommendation) to the personalization engine with its title, topics, sentiment, and type."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "item_id": {"type": "string", "description": "A unique ID for the content item."},
                "title": {"type": "string", "description": "The title of the content item."},
                "topics": {"type": "array", "items": {"type": "string"}, "description": "A list of topics covered by the content."},
                "sentiment": {"type": "string", "description": "The sentiment of the content.", "enum": ["positive", "negative", "neutral"]},
                "item_type": {"type": "string", "description": "The type of content item.", "enum": ["article", "ad", "recommendation"]}
            },
            "required": ["item_id", "title", "topics", "sentiment", "item_type"]
        }

    def execute(self, item_id: str, title: str, topics: List[str], sentiment: str, item_type: str, **kwargs: Any) -> str:
        success = content_item_manager.add_item(item_id, title, topics, sentiment, item_type)
        if success:
            report = {"message": f"Content item '{item_id}' ('{title}') added successfully."}
        else:
            report = {"error": f"Content item '{item_id}' already exists. Please choose a unique ID."}
        return json.dumps(report, indent=2)

class PersonalizeContentTool(BaseTool):
    """Personalizes content for a user based on their profile and preferences."""
    def __init__(self, tool_name="personalize_content"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Personalizes content (e.g., articles, ads, recommendations) for a specific user based on their profile and preferences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user for whom to personalize content."},
                "content_type": {"type": "string", "description": "The type of content to personalize.", "enum": ["article", "ad", "recommendation"], "default": "article"}
            },
            "required": ["user_id"]
        }

    def execute(self, user_id: str, content_type: str = "article", **kwargs: Any) -> str:
        user_profile = user_profile_manager.get_profile(user_id)
        if not user_profile:
            return json.dumps({"error": f"User profile for '{user_id}' not found. Please create it first."})
        
        eligible_content = content_item_manager.list_items(content_type)
        if not eligible_content:
            return json.dumps({"message": f"No content items of type '{content_type}' found."})

        user_preferences = user_profile["preferences"]
        
        ranked_content = []
        for item_data in eligible_content:
            score = 0
            # Topic matching
            if "topics" in user_preferences and "topics" in item_data:
                common_topics = set(user_preferences["topics"]).intersection(set(item_data["topics"]))
                score += len(common_topics) * 10
            
            # Sentiment matching
            if "sentiment" in user_preferences and user_preferences["sentiment"] == item_data.get("sentiment"):
                score += 5
            
            # Random boost to simulate other factors
            score += random.randint(0, 5)  # nosec B311

            ranked_content.append({"item_id": item_data["item_id"], "title": item_data["title"], "score": score})
        
        ranked_content.sort(key=lambda x: x["score"], reverse=True)
        
        return json.dumps({
            "user_id": user_id,
            "content_type": content_type,
            "personalized_recommendations": ranked_content[:5] # Return top 5
        }, indent=2)

class TrackUserContentEngagementTool(BaseTool):
    """Tracks a user's engagement with a specific content item, updating their profile."""
    def __init__(self, tool_name="track_user_content_engagement"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Tracks a user's engagement (e.g., 'view', 'click', 'like', 'share') with a specific content item, updating their profile based on engagement."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user."},
                "item_id": {"type": "string", "description": "The ID of the content item."},
                "engagement_type": {"type": "string", "description": "The type of engagement.", "enum": ["view", "click", "like", "share"]}
            },
            "required": ["user_id", "item_id", "engagement_type"]
        }

    def execute(self, user_id: str, item_id: str, engagement_type: str, **kwargs: Any) -> str:
        user_profile = user_profile_manager.get_profile(user_id)
        if not user_profile:
            return json.dumps({"error": f"User profile for '{user_id}' not found. Please create it first."})
        
        content_item = content_item_manager.get_item(item_id)
        if not content_item:
            return json.dumps({"error": f"Content item '{item_id}' not found. Please add it first."})

        success = user_profile_manager.track_engagement(user_id, item_id, engagement_type, content_item.get("topics", []), content_item.get("sentiment", "neutral"))
        
        if success:
            report = {"message": f"User '{user_id}' engagement '{engagement_type}' with item '{item_id}' tracked successfully. User profile updated."}
        else:
            report = {"error": f"Failed to track engagement for user '{user_id}' with item '{item_id}'. An unexpected error occurred."}
        return json.dumps(report, indent=2)