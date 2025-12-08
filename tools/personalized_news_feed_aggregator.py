import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class NewsFeedCustomizerTool(BaseTool):
    """
    A tool that simulates a personalized news feed customizer, allowing users
    to define rules for blocking keywords, prioritizing sources, and blocking
    sources to tailor their news feed.
    """

    def __init__(self, tool_name: str = "NewsFeedCustomizer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.rules_file = os.path.join(self.data_dir, "user_customization_rules.json")
        self.articles_file = os.path.join(self.data_dir, "simulated_news_articles.json")
        
        # User customization rules: {user_id: {blocked_keywords: [], prioritized_sources: [], blocked_sources: []}}
        self.user_customization_rules: Dict[str, Dict[str, Any]] = self._load_data(self.rules_file, default={})
        # News articles: {article_id: {title: ..., content: ..., topic: ..., source: ...}}
        self.news_articles: Dict[str, Dict[str, Any]] = self._load_data(self.articles_file, default={})

    @property
    def description(self) -> str:
        return "Customizes news feeds: block keywords/sources, prioritize sources, and generate tailored feeds."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["set_customization_rules", "generate_customized_feed", "add_news_article"]},
                "user_id": {"type": "string"},
                "blocked_keywords": {"type": "array", "items": {"type": "string"}},
                "prioritized_sources": {"type": "array", "items": {"type": "string"}},
                "blocked_sources": {"type": "array", "items": {"type": "string"}},
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

    def _save_rules(self):
        with open(self.rules_file, 'w') as f: json.dump(self.user_customization_rules, f, indent=2)

    def _save_articles(self):
        with open(self.articles_file, 'w') as f: json.dump(self.news_articles, f, indent=2)

    def set_customization_rules(self, user_id: str, blocked_keywords: Optional[List[str]] = None, prioritized_sources: Optional[List[str]] = None, blocked_sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Sets customization rules for a user's news feed."""
        self.user_customization_rules[user_id] = {
            "blocked_keywords": [k.lower() for k in blocked_keywords] if blocked_keywords else [],
            "prioritized_sources": [s.lower() for s in prioritized_sources] if prioritized_sources else [],
            "blocked_sources": [s.lower() for s in blocked_sources] if blocked_sources else [],
            "last_updated": datetime.now().isoformat()
        }
        self._save_rules()
        return {"status": "success", "message": f"Customization rules set for user '{user_id}'."}

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

    def generate_customized_feed(self, user_id: str) -> List[Dict[str, Any]]:
        """Generates a customized news feed based on user rules."""
        rules = self.user_customization_rules.get(user_id)
        if not rules: return {"status": "info", "message": f"User '{user_id}' has no customization rules. Returning general feed."}
        
        feed = []
        prioritized_feed = []
        
        for article_id, article in self.news_articles.items():
            # Check for blocked sources
            if article["source"] in rules["blocked_sources"]:
                continue
            
            # Check for blocked keywords
            blocked_by_keyword = False
            for keyword in rules["blocked_keywords"]:
                if keyword in article["title"].lower() or keyword in article["content"].lower():
                    blocked_by_keyword = True
                    break
            if blocked_by_keyword:
                continue
            
            # Prioritize sources
            if article["source"] in rules["prioritized_sources"]:
                prioritized_feed.append(article)
            else:
                feed.append(article)
        
        # Combine and sort (prioritized first, then by published date)
        final_feed = prioritized_feed + feed
        final_feed.sort(key=lambda x: x["published_at"], reverse=True)
        
        return final_feed

    def execute(self, operation: str, user_id: str, **kwargs: Any) -> Any:
        if operation == "set_customization_rules":
            return self.set_customization_rules(user_id, kwargs.get('blocked_keywords'), kwargs.get('prioritized_sources'), kwargs.get('blocked_sources'))
        elif operation == "generate_customized_feed":
            return self.generate_customized_feed(user_id)
        elif operation == "add_news_article":
            article_id = kwargs.get('article_id')
            title = kwargs.get('title')
            content = kwargs.get('content')
            topic = kwargs.get('topic')
            source = kwargs.get('source')
            if not all([article_id, title, content, topic, source]):
                raise ValueError("Missing 'article_id', 'title', 'content', 'topic', or 'source' for 'add_news_article' operation.")
            return self.add_news_article(article_id, title, content, topic, source)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating NewsFeedCustomizerTool functionality...")
    temp_dir = "temp_news_customizer_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    news_customizer = NewsFeedCustomizerTool(data_dir=temp_dir)
    
    try:
        # 1. Add some simulated news articles
        print("\n--- Adding simulated news articles ---")
        news_customizer.execute(operation="add_news_article", article_id="art_001", title="Politics in the Tech World", content="...", topic="tech", source="tech_daily")
        news_customizer.execute(operation="add_news_article", article_id="art_002", title="Sports Highlights Today", content="...", topic="sports", source="sports_news")
        news_customizer.execute(operation="add_news_article", article_id="art_003", title="New Tech Gadgets Review", content="...", topic="tech", source="gadget_reviews")
        news_customizer.execute(operation="add_news_article", article_id="art_004", title="Political Debate Analysis", content="...", topic="politics", source="politics_today")
        print("Articles added.")

        # 2. Set customization rules for user_alice (block politics, prioritize tech_daily)
        print("\n--- Setting customization rules for 'user_alice' ---")
        news_customizer.execute(operation="set_customization_rules", user_id="user_alice", blocked_keywords=["politics"], prioritized_sources=["tech_daily"])
        print("Rules set for user_alice.")

        # 3. Generate customized news feed for user_alice
        print("\n--- Generating customized news feed for 'user_alice' ---")
        feed_alice = news_customizer.execute(operation="generate_customized_feed", user_id="user_alice")
        print(json.dumps(feed_alice, indent=2))

        # 4. Set customization rules for user_bob (block tech_daily, prioritize sports_news)
        print("\n--- Setting customization rules for 'user_bob' ---")
        news_customizer.execute(operation="set_customization_rules", user_id="user_bob", blocked_sources=["tech_daily"], prioritized_sources=["sports_news"])
        print("Rules set for user_bob.")

        # 5. Generate customized news feed for user_bob
        print("\n--- Generating customized news feed for 'user_bob' ---")
        feed_bob = news_customizer.execute(operation="generate_customized_feed", user_id="user_bob")
        print(json.dumps(feed_bob, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")