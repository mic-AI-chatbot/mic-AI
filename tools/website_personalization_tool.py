import logging
import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# In-memory storage for simulated user profiles
user_profiles: Dict[str, Dict[str, Any]] = {}

class WebsitePersonalizationTool(BaseTool):
    """
    A tool to simulate website personalization based on user profiles and actions.
    """
    def __init__(self, tool_name: str = "website_personalization_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates website personalization: manage user profiles, personalize content, and recommend products."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action: 'create_profile', 'update_profile', 'personalize_content', 'recommend_products', 'optimize_layout', 'get_profile'."
                },
                "user_id": {"type": "string", "description": "The unique ID of the user."},
                "interests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of user interests (e.g., 'tech', 'sports', 'fashion')."
                },
                "browsing_history": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of URLs or product IDs the user has viewed."
                },
                "content_type": {"type": "string", "description": "The type of content to personalize (e.g., 'homepage_banner', 'article_recommendation')."},
                "product_category": {"type": "string", "description": "The category for product recommendations (e.g., 'electronics', 'clothing')."},
                "layout_area": {"type": "string", "description": "The area of the layout to optimize (e.g., 'homepage', 'product_page')."}
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs: Any) -> Dict:
        try:
            action = action.lower()
            user_id = kwargs.get("user_id")

            if action != 'create_profile' and not user_id:
                raise ValueError(f"'user_id' is required for the '{action}' action.")

            actions = {
                "create_profile": self._create_user_profile,
                "update_profile": self._update_user_profile,
                "personalize_content": self._personalize_content,
                "recommend_products": self._recommend_products,
                "optimize_layout": self._optimize_layout,
                "get_profile": self._get_user_profile,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](**kwargs)

        except Exception as e:
            logger.error(f"An error occurred in WebsitePersonalizationTool: {e}")
            return {"error": str(e)}

    def _create_user_profile(self, user_id: str, interests: List[str] = None, **kwargs) -> Dict:
        if user_id in user_profiles:
            raise ValueError(f"User profile for '{user_id}' already exists.")
        
        new_profile = {
            "id": user_id,
            "interests": interests or [],
            "browsing_history": [],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        user_profiles[user_id] = new_profile
        logger.info(f"User profile for '{user_id}' created.")
        return {"message": "User profile created successfully.", "profile": new_profile}

    def _update_user_profile(self, user_id: str, interests: Optional[List[str]] = None, browsing_history: Optional[List[str]] = None, **kwargs) -> Dict:
        if user_id not in user_profiles:
            raise ValueError(f"User profile for '{user_id}' not found.")
            
        profile = user_profiles[user_id]
        if interests:
            profile["interests"].extend(interests)
            profile["interests"] = list(set(profile["interests"])) # Remove duplicates
        if browsing_history:
            profile["browsing_history"].extend(browsing_history)
            profile["browsing_history"] = list(set(profile["browsing_history"])) # Remove duplicates
        
        profile["last_updated"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"User profile for '{user_id}' updated.")
        return {"message": "User profile updated successfully.", "profile": profile}

    def _personalize_content(self, user_id: str, content_type: str, **kwargs) -> Dict:
        if user_id not in user_profiles:
            raise ValueError(f"User profile for '{user_id}' not found.")
            
        profile = user_profiles[user_id]
        
        # Simulate content personalization based on interests
        personalized_content = f"Here's some personalized {content_type} for you, {user_id}. "
        if profile["interests"]:
            personalized_content += f"Based on your interest in {random.choice(profile['interests'])}, we recommend..."  # nosec B311
        else:
            personalized_content += "We've selected some popular content for you."
            
        return {"message": "Content personalized.", "user_id": user_id, "content_type": content_type, "personalized_content": personalized_content}

    def _recommend_products(self, user_id: str, product_category: Optional[str] = None, **kwargs) -> Dict:
        if user_id not in user_profiles:
            raise ValueError(f"User profile for '{user_id}' not found.")
            
        profile = user_profiles[user_id]
        
        # Simulate product recommendations based on interests and browsing history
        recommendations = []
        if profile["interests"]:
            recommendations.append(f"Product related to {random.choice(profile['interests'])}")  # nosec B311
        if profile["browsing_history"]:
            recommendations.append(f"Product similar to {random.choice(profile['browsing_history'])}")  # nosec B311
        
        if not recommendations:
            recommendations.append("Popular product X")
            recommendations.append("Popular product Y")
            
        return {"message": "Products recommended.", "user_id": user_id, "recommendations": recommendations}

    def _optimize_layout(self, user_id: str, layout_area: str, **kwargs) -> Dict:
        if user_id not in user_profiles:
            raise ValueError(f"User profile for '{user_id}' not found.")
            
        # Simulate layout optimization
        optimized_layout = f"Layout for {layout_area} optimized for user {user_id}. "
        if user_profiles[user_id]["interests"]:
            optimized_layout += "Highlighting content based on your interests."
        else:
            optimized_layout += "Using a standard, high-engagement layout."
            
        return {"message": "Layout optimized.", "user_id": user_id, "layout_area": layout_area, "optimized_layout_description": optimized_layout}

    def _get_user_profile(self, user_id: str, **kwargs) -> Dict:
        if user_id not in user_profiles:
            raise ValueError(f"User profile for '{user_id}' not found.")
        return {"user_profile": user_profiles[user_id]}