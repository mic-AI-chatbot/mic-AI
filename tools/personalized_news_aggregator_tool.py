
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PersonalizedNewsAggregatorTool(BaseTool):
    """
    A tool that simulates a personalized news aggregator, allowing users to set
    preferences and generate a news feed tailored to their interests.
    """

    def __init__(self, tool_name: str = "PersonalizedNewsAggregator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.preferences_file = os.path.join(self.data_dir, "user_news_preferences.json")
        self.articles_file = os.path.join(self.data_dir, "simulated_news_articles.json")
        
        # User preferences: {user_id: {preferred_topics: [], preferred_sources: []}}
        self.user_preferences: Dict[str, Dict[str, Any]] = self._load_data(self.preferences_file, default={})
        # News articles: {article_id: {title: ..., content: ..., topic: ..., source: ...}}
        self.news_articles: Dict[str, Dict[str, Any]] = self._load_data(self.articles_file, default={})

    @property
    def description(self) -> str:
        return "Simulates a personalized news aggregator: set preferences and generate tailored news feeds."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["set_preferences", "generate_news_feed", "add_news_article"]},
                "user_id": {"type": "string"},
                "preferred_topics": {"type": "array", "items": {"type": "string"}},
                "preferred_sources": {"type": "array", "items": {"type": "string"}},
                "article_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "topic": {"type": "string"},
                "source": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_preferences(self):
        with open(self.preferences_file, 'w') as f: json.dump(self.user_preferences, f, indent=2)

    def _save_articles(self):
        with open(self.articles_file, 'w') as f: json.dump(self.news_articles, f, indent=2)

    def set_preferences(self, user_id: str, preferred_topics: List[str], preferred_sources: List[str]) -> Dict[str, Any]:
        """Sets user preferences for news aggregation."""
        self.user_preferences[user_id] = {
            "preferred_topics": [t.lower() for t in preferred_topics],
            "preferred_sources": [s.lower() for s in preferred_sources],
            "last_updated": datetime.now().isoformat()
        }
        self._save_preferences()
        return {"status": "success", "message": f"Preferences set for user '{user_id}'."}

    def add_news_article(self, article_id: str, title: str, content: str, topic: str, source: str) -> Dict[str, Any]:
        """Adds a simulated news article to the database."""
        if article_id in self.news_articles: raise ValueError(f"Article '{article_id}' already exists.")
        
        new_article = {
            "id": article_id, "title": title, "content": content,
            "topic": topic.lower(), "source": source.lower(),
            "published_at": datetime.now().isoformat()
        }
        self.news_articles[article_id] = new_article
        self._save_articles()
        return {"status": "success", "message": f"Article '{article_id}' added."}

    def generate_news_feed(self, user_id: str) -> List[Dict[str, Any]]:
        """Generates a personalized news feed based on user preferences."""
        preferences = self.user_preferences.get(user_id)
        if not preferences: return {"status": "info", "message": f"User '{user_id}' has no preferences set. Returning general feed."}
        
        feed = []
        for article_id, article in self.news_articles.items():
            topic_match = article["topic"] in preferences["preferred_topics"]
            source_match = article["source"] in preferences["preferred_sources"]
            
            if topic_match or source_match:
                feed.append(article)
        
        # Sort by published date (simulated)
        feed.sort(key=lambda x: x["published_at"], reverse=True)
        
        return feed

    def execute(self, operation: str, user_id: str, **kwargs: Any) -> Any:
        if operation == "set_preferences":
            return self.set_preferences(user_id, kwargs['preferred_topics'], kwargs['preferred_sources'])
        elif operation == "generate_news_feed":
            return self.generate_news_feed(user_id)
        elif operation == "add_news_article":
            return self.add_news_article(kwargs['article_id'], kwargs['title'], kwargs['content'], kwargs['topic'], kwargs['source'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PersonalizedNewsAggregatorTool functionality...")
    temp_dir = "temp_news_aggregator_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    news_aggregator = PersonalizedNewsAggregatorTool(data_dir=temp_dir)
    
    try:
        # 1. Add some simulated news articles
        print("\n--- Adding simulated news articles ---")
        news_aggregator.execute(operation="add_news_article", article_id="art_001", title="AI Breakthrough in Robotics", content="...", topic="tech", source="tech_daily")
        news_aggregator.execute(operation="add_news_article", article_id="art_002", title="Local Team Wins Championship", content="...", topic="sports", source="local_news")
        news_aggregator.execute(operation="add_news_article", article_id="art_003", title="Market Trends for Q4", content="...", topic="finance", source="business_journal")
        news_aggregator.execute(operation="add_news_article", article_id="art_004", title="New Gadget Review", content="...", topic="tech", source="gadget_reviews")
        print("Articles added.")

        # 2. Set preferences for user_alice
        print("\n--- Setting preferences for 'user_alice' ---")
        news_aggregator.execute(operation="set_preferences", user_id="user_alice", preferred_topics=["tech", "finance"], preferred_sources=["tech_daily"])
        print("Preferences set for user_alice.")

        # 3. Generate news feed for user_alice
        print("\n--- Generating news feed for 'user_alice' ---")
        feed_alice = news_aggregator.execute(operation="generate_news_feed", user_id="user_alice")
        print(json.dumps(feed_alice, indent=2))

        # 4. Set preferences for user_bob
        print("\n--- Setting preferences for 'user_bob' ---")
        news_aggregator.execute(operation="set_preferences", user_id="user_bob", preferred_topics=["sports"], preferred_sources=["local_news"])
        print("Preferences set for user_bob.")

        # 5. Generate news feed for user_bob
        print("\n--- Generating news feed for 'user_bob' ---")
        feed_bob = news_aggregator.execute(operation="generate_news_feed", user_id="user_bob")
        print(json.dumps(feed_bob, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
