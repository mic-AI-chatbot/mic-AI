import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizationEngineSimulatorTool(BaseTool):
    """
    A tool that simulates a personalization engine, allowing for updating user
    profiles, generating recommendations, and personalizing content based on
    user preferences and context.
    """

    def __init__(self, tool_name: str = "PersonalizationEngineSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.profiles_file = os.path.join(self.data_dir, "user_profiles.json")
        # User profiles structure: {user_id: {preferences: {genres: [], topics: []}, history: []}}
        self.user_profiles: Dict[str, Dict[str, Any]] = self._load_data(self.profiles_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a personalization engine: updates profiles, generates recommendations, personalizes content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["update_user_profile", "get_recommendations", "personalize_content"]},
                "user_id": {"type": "string"},
                "preferences": {"type": "object", "description": "e.g., {'genres': ['sci-fi'], 'topics': ['AI']}"},
                "context": {"type": "object", "description": "e.g., {'last_viewed_category': 'electronics'}"},
                "content_id": {"type": "string", "description": "ID of the content to personalize."}
            },
            "required": ["operation", "user_id"]
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
        with open(self.profiles_file, 'w') as f: json.dump(self.user_profiles, f, indent=2)

    def update_user_profile(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Updates a user's profile with new preferences."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {"preferences": {}, "history": []}
        
        self.user_profiles[user_id]["preferences"].update(preferences)
        self.user_profiles[user_id]["last_updated"] = datetime.now().isoformat()
        self._save_data()
        return {"status": "success", "message": f"User '{user_id}' profile updated."}

    def get_recommendations(self, user_id: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generates rule-based recommendations for a user."""
        profile = self.user_profiles.get(user_id)
        if not profile: return {"status": "info", "message": f"User '{user_id}' profile not found. Cannot generate recommendations."}
        
        recommendations = []
        
        # Rule 1: Based on preferred genres
        for genre in profile["preferences"].get("genres", []):
            recommendations.append({"type": "movie", "title": f"Recommended {genre.title()} Film", "reason": f"Based on your preferred genre: {genre}."})
        
        # Rule 2: Based on preferred topics
        for topic in profile["preferences"].get("topics", []):
            recommendations.append({"type": "article", "title": f"Top Article on {topic.title()}", "reason": f"Based on your preferred topic: {topic}."})

        # Rule 3: Based on context (e.g., last viewed category)
        if context and context.get("last_viewed_category"):
            category = context["last_viewed_category"]
            recommendations.append({"type": "product", "title": f"New {category.title()} Gadget", "reason": f"Based on your recent interest in {category}."})
        
        if not recommendations:
            recommendations.append({"type": "general", "title": "Explore New Arrivals", "reason": "No specific preferences or context found."})

        return recommendations

    def personalize_content(self, user_id: str, content_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates a personalized version of content for a user."""
        profile = self.user_profiles.get(user_id)
        if not profile: return {"status": "info", "message": f"User '{user_id}' profile not found. Cannot personalize content."}
        
        personalized_text = f"Hello {user_id},\n\nHere is your personalized content for '{content_id}'.\n\n"
        
        # Example personalization: insert preferred topics into a generic article
        preferred_topics = profile["preferences"].get("topics", [])
        if preferred_topics:
            personalized_text += f"We know you're interested in {', '.join(preferred_topics)}. This article highlights recent developments in these areas.\n"
        
        if context and context.get("location"):
            personalized_text += f"Since you are in {context['location']}, we've included local insights relevant to you.\n"
        
        personalized_text += "This is the rest of the content, tailored to your interests."

        return {"status": "success", "user_id": user_id, "content_id": content_id, "personalized_content": personalized_text}

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "update_user_profile":
            return self.update_user_profile(kwargs['user_id'], kwargs['preferences'])
        elif operation == "get_recommendations":
            return self.get_recommendations(kwargs['user_id'], kwargs.get('context'))
        elif operation == "personalize_content":
            return self.personalize_content(kwargs['user_id'], kwargs['content_id'], kwargs.get('context'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizationEngineSimulatorTool functionality...")
    temp_dir = "temp_personalization_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    personalization_tool = PersonalizationEngineSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Update user profile
        print("\n--- Updating user profile for 'user_alice' ---")
        personalization_tool.execute(operation="update_user_profile", user_id="user_alice", preferences={"genres": ["sci-fi", "fantasy"], "topics": ["AI", "space_exploration"]})
        print("Profile updated.")

        # 2. Get recommendations for user_alice
        print("\n--- Getting recommendations for 'user_alice' ---")
        recs1 = personalization_tool.execute(operation="get_recommendations", user_id="user_alice")
        print(json.dumps(recs1, indent=2))

        # 3. Get recommendations with context
        print("\n--- Getting recommendations for 'user_alice' with context ---")
        context = {"last_viewed_category": "electronics"}
        recs2 = personalization_tool.execute(operation="get_recommendations", user_id="user_alice", context=context)
        print(json.dumps(recs2, indent=2))

        # 4. Personalize content
        print("\n--- Personalizing content 'news_article_1' for 'user_alice' ---")
        personalized_content = personalization_tool.execute(operation="personalize_content", user_id="user_alice", content_id="news_article_1", context={"location": "New York"})
        print(json.dumps(personalized_content, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")