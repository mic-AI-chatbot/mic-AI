import logging
import random
import json
from typing import Dict, Any, List

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple knowledge base of content elements by topic and tone
CONTENT_ELEMENTS = {
    "tech": {
        "hashtags": ["#Tech", "#Innovation", "#AI", "#FutureTech"],
        "emojis": ["💻", "🚀", "💡", "🤖"],
        "phrases": {
            "informative": "Explore the latest advancements in technology.",
            "engaging": "Dive into the future with cutting-edge tech!",
            "humorous": "My computer just updated itself. I think it's planning something...",
            "professional": "Discover strategic insights into technological evolution."
        },
        "adjectives": ["groundbreaking", "disruptive", "transformative", "futuristic"],
        "nouns": ["algorithms", "data", "networks", "innovations"],
        "verbs": ["optimize", "revolutionize", "integrate", "accelerate"]
    },
    "sports": {
        "hashtags": ["#Sports", "#GameDay", "#Athletics", "#Fitness"],
        "emojis": ["🏆", "💪", "⚽", "🏀"],
        "phrases": {
            "informative": "Stay updated on the latest sports news and scores.",
            "engaging": "Feel the adrenaline! What's your favorite game-day moment?",
            "humorous": "My workout routine is mostly running late.",
            "professional": "Analyze athletic performance and team strategies."
        },
        "adjectives": ["intense", "thrilling", "strategic", "powerful"],
        "nouns": ["athletes", "teams", "matches", "victories"],
        "verbs": ["compete", "train", "dominate", "excel"]
    },
    "food": {
        "hashtags": ["#Foodie", "#Delicious", "#Cooking", "#Recipes"],
        "emojis": ["🍔", "🍕", "😋", "👨‍🍳"],
        "phrases": {
            "informative": "Learn about healthy eating habits and culinary techniques.",
            "engaging": "What's cooking tonight? Share your favorite dish!",
            "humorous": "I'm on a seafood diet. I see food and I eat it.",
            "professional": "Explore gastronomic trends and food industry innovations."
        },
        "adjectives": ["delectable", "gourmet", "savory", "aromatic"],
        "nouns": ["ingredients", "dishes", "flavors", "cuisines"],
        "verbs": ["savor", "prepare", "indulge", "create"]
    }
}

class SocialMediaContentCreatorTool(BaseTool):
    """
    A tool that generates social media content (posts, captions) based on
    platform, topic, tone, and desired length using rule-based templates.
    """

    def __init__(self, tool_name: str = "SocialMediaContentCreator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates social media content (posts, captions) based on platform, topic, tone, and length."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["Facebook", "Twitter", "Instagram", "LinkedIn"], "description": "The social media platform."},
                "topic": {"type": "string", "enum": ["tech", "sports", "food"], "description": "The topic of the content."},
                "tone": {"type": "string", "enum": ["informative", "engaging", "humorous", "professional"], "default": "engaging", "description": "The desired tone."},
                "length": {"type": "string", "enum": ["short", "medium", "long"], "default": "medium", "description": "The desired length of the content."}
            },
            "required": ["platform", "topic"]
        }

    def execute(self, platform: str, topic: str, tone: str = "engaging", length: str = "medium", **kwargs: Any) -> Dict[str, Any]:
        """
        Generates social media content based on the specified platform, topic, tone, and length.
        """
        if topic not in CONTENT_ELEMENTS:
            raise ValueError(f"Unsupported topic: {topic}. Choose from {list(CONTENT_ELEMENTS.keys())}.")
        
        elements = CONTENT_ELEMENTS[topic]
        
        post_content = []
        
        # Main phrase based on tone
        main_phrase = elements["phrases"].get(tone, elements["phrases"]["informative"])
        post_content.append(main_phrase)
        
        # Add more details based on length
        if length == "medium":
            post_content.append(f"Here's a {random.choice(elements['adjectives'])} insight: {random.choice(elements['nouns'])} {random.choice(elements['verbs'])}.")  # nosec B311
        elif length == "long":
            post_content.append(f"Here's a {random.choice(elements['adjectives'])} insight: {random.choice(elements['nouns'])} {random.choice(elements['verbs'])}.")  # nosec B311
            post_content.append(f"Discover how {random.choice(elements['nouns'])} can {random.choice(elements['verbs'])} {random.choice(elements['phrases'].values())[0]}.") # Use a random phrase from the values  # nosec B311
        
        # Add emojis and hashtags
        post_content.append(random.choice(elements["emojis"]))  # nosec B311
        post_content.extend(random.sample(elements["hashtags"], k=random.randint(2, 4)))  # nosec B311
        
        generated_post = " ".join(post_content)

        return {
            "status": "success",
            "platform": platform,
            "topic": topic,
            "tone": tone,
            "length": length,
            "generated_content": generated_post,
            "disclaimer": "This is simulated content. It is procedurally generated and may not be coherent or high-quality."
        }

if __name__ == '__main__':
    print("Demonstrating SocialMediaContentCreatorTool functionality...")
    
    creator_tool = SocialMediaContentCreatorTool()
    
    try:
        # 1. Generate an engaging Facebook post about tech
        print("\n--- Generating Engaging Facebook Post (Tech) ---")
        result1 = creator_tool.execute(platform="Facebook", topic="tech", tone="engaging", length="medium")
        print(json.dumps(result1, indent=2))

        # 2. Generate an informative Twitter post about sports
        print("\n--- Generating Informative Twitter Post (Sports) ---")
        result2 = creator_tool.execute(platform="Twitter", topic="sports", tone="informative", length="short")
        print(json.dumps(result2, indent=2))
        
        # 3. Generate a humorous Instagram post about food
        print("\n--- Generating Humorous Instagram Post (Food) ---")
        result3 = creator_tool.execute(platform="Instagram", topic="food", tone="humorous", length="long")
        print(json.dumps(result3, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")