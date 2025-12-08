import logging
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Predefined content templates for personalization
CONTENT_TEMPLATES = {
    "marketing_copy": {
        "casual": "Hey there, {user_name}! Check out our awesome new {product_category} stuff. It's totally {adjective} and perfect for {user_interest}. Don't miss out!",
        "formal": "Dear {user_name}, we are pleased to present our latest {product_category} offerings. These {adjective} solutions are designed to meet your needs in {user_interest}. Learn more today."
    },
    "news_article": {
        "tech": "In the world of technology, {user_name} will be thrilled to hear about the latest breakthroughs in {user_interest}. Our new report highlights {key_finding}.",
        "sports": "For sports enthusiasts like {user_name}, the recent {user_interest} season has been {adjective}. We recap the top moments and look ahead to the next games."
    }
}

class PersonalizedContentGeneratorTool(BaseTool):
    """
    A tool that generates personalized text content (e.g., marketing copy,
    news articles) based on individual user preferences.
    """
    def __init__(self, tool_name: str = "PersonalizedContentGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates personalized text content (marketing copy, news) based on user preferences."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The ID of the user for whom to generate content."},
                "user_preferences": {
                    "type": "object",
                    "description": "The user's preferences (e.g., {'name': 'Alice', 'topics': ['tech'], 'tone': 'casual', 'product_category': 'gadgets', 'user_interest': 'innovation'})."
                },
                "content_type": {"type": "string", "enum": ["marketing_copy", "news_article"], "description": "The type of content to generate."}
            },
            "required": ["user_id", "user_preferences", "content_type"]
        }

    def execute(self, user_id: str, user_preferences: Dict[str, Any], content_type: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Generates personalized text content based on user preferences and content type.
        """
        if content_type not in CONTENT_TEMPLATES:
            raise ValueError(f"Unsupported content type: {content_type}. Choose from {list(CONTENT_TEMPLATES.keys())}.")

        # Extract preferences with defaults
        user_name = user_preferences.get("name", user_id)
        tone = user_preferences.get("tone", "casual")
        topics = user_preferences.get("topics", ["general"])
        product_category = user_preferences.get("product_category", "products")
        user_interest = user_preferences.get("user_interest", "new things")
        
        # Adjectives for variety
        adjectives = ["innovative", "exciting", "cutting-edge", "useful", "amazing"]

        # Prepare data for template filling
        template_data = {
            "user_name": user_name,
            "product_category": product_category,
            "adjective": random.choice(adjectives),  # nosec B311
            "user_interest": random.choice(topics) if topics else user_interest,  # nosec B311
            "key_finding": "significant advancements in AI" # Example for news
        }

        generated_content = "Could not generate content."
        if content_type == "marketing_copy":
            template = CONTENT_TEMPLATES["marketing_copy"].get(tone, CONTENT_TEMPLATES["marketing_copy"]["casual"])
            generated_content = template.format(**template_data)
        elif content_type == "news_article":
            # Pick a topic-specific template if available, else default to first topic
            topic_template_key = topics[0] if topics else "tech"
            template = CONTENT_TEMPLATES["news_article"].get(topic_template_key, CONTENT_TEMPLATES["news_article"]["tech"])
            generated_content = template.format(**template_data)

        return {
            "status": "success",
            "user_id": user_id,
            "content_type": content_type,
            "generated_content": generated_content
        }

if __name__ == '__main__':
    print("Demonstrating PersonalizedContentGeneratorTool functionality...")
    
    generator_tool = PersonalizedContentGeneratorTool()
    
    try:
        # 1. Generate marketing copy for Alice (casual, tech interest)
        print("\n--- Generating Marketing Copy for Alice (casual, tech) ---")
        alice_prefs = {"name": "Alice", "topics": ["AI", "gadgets"], "tone": "casual", "product_category": "tech"}
        result1 = generator_tool.execute(user_id="alice_123", user_preferences=alice_prefs, content_type="marketing_copy")
        print(json.dumps(result1, indent=2))

        # 2. Generate news article for Bob (formal, sports interest)
        print("\n--- Generating News Article for Bob (formal, sports) ---")
        bob_prefs = {"name": "Bob", "topics": ["football", "basketball"], "tone": "formal", "user_interest": "sports"}
        result2 = generator_tool.execute(user_id="bob_456", user_preferences=bob_prefs, content_type="news_article")
        print(json.dumps(result2, indent=2))
        
        # 3. Generate marketing copy for Charlie (default preferences)
        print("\n--- Generating Marketing Copy for Charlie (default) ---")
        charlie_prefs = {"name": "Charlie"}
        result3 = generator_tool.execute(user_id="charlie_789", user_preferences=charlie_prefs, content_type="marketing_copy")
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")