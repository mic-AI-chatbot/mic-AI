
import logging
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Simple knowledge base of poetic/lyrical elements
GENERATION_ELEMENTS = {
    "nature": {
        "adjectives": ["green", "whispering", "ancient", "serene", "vibrant", "wild", "calm"],
        "nouns": ["trees", "rivers", "mountains", "flowers", "sky", "wind", "sun", "moon", "stars"],
        "verbs": ["sings", "flows", "stands", "blooms", "dances", "shines", "sleeps"],
        "phrases": ["under the sun", "beneath the moon", "a gentle breeze", "the earth awakes", "in silent grace"]
    },
    "love": {
        "adjectives": ["tender", "burning", "sweet", "eternal", "fragile", "deep", "true"],
        "nouns": ["heart", "soul", "embrace", "flame", "whisper", "dream", "light", "touch"],
        "verbs": ["beats", "burns", "holds", "cherishes", "unites", "shines", "yearns"],
        "phrases": ["my dearest one", "a timeless bond", "in your eyes", "forevermore", "side by side"]
    },
    "sadness": {
        "adjectives": ["grey", "fading", "lonely", "silent", "lost", "cold", "empty"],
        "nouns": ["shadows", "tears", "rain", "memories", "silence", "grief", "ache", "void"],
        "verbs": ["falls", "weeps", "fades", "lingers", "aches", "drifts", "breaks"],
        "phrases": ["a heavy sigh", "the fading light", "a distant echo", "all hope gone", "lost in thought"]
    },
    "hope": {
        "adjectives": ["bright", "new", "golden", "rising", "unseen", "strong", "gentle"],
        "nouns": ["dawn", "light", "future", "dream", "seed", "path", "strength"],
        "verbs": ["shines", "grows", "rises", "guides", "blooms", "whispers", "awaits"],
        "phrases": ["a new day", "the path ahead", "never give up", "a guiding star", "believe again"]
    }
}

class PoetrySongLyricGeneratorTool(BaseTool):
    """
    A tool that generates simulated poetry or song lyrics based on a topic,
    style, and mood, using rule-based text generation.
    """
    def __init__(self, tool_name: str = "PoetrySongLyricGenerator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Generates simulated poetry or song lyrics based on topic, style, and mood."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": ["nature", "love"], "description": "The topic for generation."},
                "style": {"type": "string", "enum": ["poetry", "lyrics"], "description": "The style of generation."},
                "mood": {"type": "string", "enum": ["sadness", "hope", "joyful", "melancholy"], "default": "hope", "description": "The emotional mood."}
            },
            "required": ["topic", "style"]
        }

    def execute(self, topic: str, style: str, mood: str = "hope", **kwargs: Any) -> Dict[str, Any]:
        """
        Generates poetry or song lyrics based on the specified topic, style, and mood.
        """
        if topic not in GENERATION_ELEMENTS:
            raise ValueError(f"Unsupported topic: {topic}. Choose from {list(GENERATION_ELEMENTS.keys())}.")
        if mood not in GENERATION_ELEMENTS:
            # Fallback to a general mood if specific mood elements not defined
            mood_elements = GENERATION_ELEMENTS["nature"]
        else:
            mood_elements = GENERATION_ELEMENTS[mood]

        topic_elements = GENERATION_ELEMENTS[topic]

        generated_text_lines = []

        if style == "poetry":
            generated_text_lines.append(f"A poem about {topic.title()} in a {mood} tone:")
            generated_text_lines.append("")
            for _ in range(random.randint(4, 8)): # Generate 4-8 lines  # nosec B311
                line = f"The {random.choice(mood_elements['adjectives'])} {random.choice(topic_elements['nouns'])} {random.choice(topic_elements['verbs'])} {random.choice(mood_elements['phrases'])}."  # nosec B311
                generated_text_lines.append(line.capitalize())
        elif style == "lyrics":
            generated_text_lines.append(f"Song Lyrics about {topic.title()} ({mood} mood):")
            generated_text_lines.append("")
            
            # Verse 1
            generated_text_lines.append("Verse 1:")
            generated_text_lines.append(f"  {random.choice(topic_elements['phrases'])}, a {random.choice(mood_elements['adjectives'])} {random.choice(topic_elements['nouns'])} {random.choice(topic_elements['verbs'])}.")  # nosec B311
            generated_text_lines.append(f"  My {random.choice(mood_elements['nouns'])} {random.choice(mood_elements['verbs'])} with {random.choice(topic_elements['adjectives'])} {random.choice(mood_elements['nouns'])}.")  # nosec B311
            generated_text_lines.append("")

            # Chorus
            generated_text_lines.append("Chorus:")
            generated_text_lines.append(f"  Oh, {random.choice(topic_elements['nouns'])}, my {random.choice(mood_elements['adjectives'])} {random.choice(mood_elements['nouns'])}!")  # nosec B311
            generated_text_lines.append(f"  {random.choice(topic_elements['phrases'])}, {random.choice(mood_elements['phrases'])}.")  # nosec B311
            generated_text_lines.append("")

            # Verse 2
            generated_text_lines.append("Verse 2:")
            generated_text_lines.append(f"  A {random.choice(topic_elements['adjectives'])} {random.choice(topic_elements['nouns'])} {random.choice(topic_elements['verbs'])} {random.choice(mood_elements['phrases'])}.")  # nosec B311
            generated_text_lines.append(f"  And {random.choice(mood_elements['adjectives'])} {random.choice(mood_elements['nouns'])} {random.choice(mood_elements['verbs'])} in the {random.choice(topic_elements['nouns'])}.")  # nosec B311
            generated_text_lines.append("")

            # Chorus
            generated_text_lines.append("Chorus:")
            generated_text_lines.append(f"  Oh, {random.choice(topic_elements['nouns'])}, my {random.choice(mood_elements['adjectives'])} {random.choice(mood_elements['nouns'])}!")  # nosec B311
            generated_text_lines.append(f"  {random.choice(topic_elements['phrases'])}, {random.choice(mood_elements['phrases'])}.")  # nosec B311
            generated_text_lines.append("")

            # Bridge
            generated_text_lines.append("Bridge:")
            generated_text_lines.append(f"  {random.choice(mood_elements['phrases'])}, {random.choice(topic_elements['phrases'])}.")  # nosec B311
            generated_text_lines.append(f"  The {random.choice(mood_elements['adjectives'])} {random.choice(mood_elements['nouns'])} {random.choice(mood_elements['verbs'])}.")  # nosec B311
            generated_text_lines.append("")

            # Outro
            generated_text_lines.append("Outro:")
            generated_text_lines.append(f"  {random.choice(topic_elements['phrases'])}...")  # nosec B311

        generated_text = "\n".join(generated_text_lines)

        return {
            "status": "success",
            "style": style,
            "topic": topic,
            "mood": mood,
            "generated_text": generated_text,
            "disclaimer": "This is simulated generated text. It is procedurally generated and may not be coherent or high-quality."
        }

if __name__ == '__main__':
    print("Demonstrating PoetrySongLyricGeneratorTool functionality...")
    
    generator_tool = PoetrySongLyricGeneratorTool()
    
    try:
        # 1. Generate a poem about nature in a hopeful mood
        print("\n--- Generating Poetry (Nature, Hope) ---")
        poem_result = generator_tool.execute(topic="nature", style="poetry", mood="hope")
        print(json.dumps(poem_result, indent=2))

        # 2. Generate song lyrics about love in a sad mood
        print("\n--- Generating Song Lyrics (Love, Sadness) ---")
        lyrics_result = generator_tool.execute(topic="love", style="lyrics", mood="sadness")
        print(json.dumps(lyrics_result, indent=2))
        
        # 3. Generate a poem about nature in a joyful mood
        print("\n--- Generating Poetry (Nature, Joyful) ---")
        poem_result_joy = generator_tool.execute(topic="nature", style="poetry", mood="joyful")
        print(json.dumps(poem_result_joy, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
