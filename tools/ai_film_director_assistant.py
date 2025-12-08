import logging
import json
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from transformers import pipeline

logger = logging.getLogger(__name__)

class FilmAssistantModel:
    """A helper class to manage the text generation model for the film assistant."""
    _generator = None

    @classmethod
    def get_generator(cls):
        if cls._generator is None:
            try:
                logger.info("Initializing text generation model (gpt2)...")
                cls._generator = pipeline("text-generation", model="distilgpt2")
                logger.info("Text generation model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load text generation model: {e}")
        return cls._generator

    def generate_text(self, prompt: str, max_length: int) -> str:
        generator = self.get_generator()
        if not generator:
            return "Text generation model is not available."
        
        try:
            # The generator returns a list of generated texts. We take the first one.
            generated = generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=generator.tokenizer.eos_token_id)
            return generated[0]['generated_text']
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

film_model = FilmAssistantModel()

class GenerateSceneConceptTool(BaseTool):
    """Tool to generate a creative concept for a film scene using a generative model."""
    def __init__(self, tool_name="generate_scene_concept"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a creative concept for a film scene, including plot points and mood, based on a theme and keywords."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "The central theme or genre of the scene (e.g., 'sci-fi mystery')."},
                "keywords": {"type": "array", "items": {"type": "string"}, "description": "Optional keywords to guide generation."}
            },
            "required": ["theme"]
        }

    def execute(self, theme: str, keywords: List[str] = None, **kwargs: Any) -> str:
        keyword_str = f"with elements of {', '.join(keywords)}" if keywords else ""
        prompt = f"Generate a detailed and creative concept for a {theme} film scene {keyword_str}. The concept should include a setting, a key character, a plot point, and the overall mood."
        
        concept = film_model.generate_text(prompt, max_length=150)
        
        return json.dumps({"scene_concept": concept}, indent=2)

class SuggestCameraAngleTool(BaseTool):
    """Tool to suggest a camera angle with justification."""
    def __init__(self, tool_name="suggest_camera_angle"):
        super().__init__(tool_name=tool_name)
        self.angle_justifications = {
            "Wide Shot": "to establish the setting and the character's relationship to it.",
            "Medium Shot": "to focus on the character's body language and interactions without being too intimate.",
            "Close-Up": "to capture subtle emotions and create a sense of intimacy or tension.",
            "Low Angle": "to make the subject appear powerful, dominant, or intimidating.",
            "High Angle": "to make the subject appear vulnerable, small, or insignificant.",
            "Dutch Angle": "to create a sense of unease, disorientation, or psychological distress."
        }

    @property
    def description(self) -> str:
        return "Suggests a camera angle for a scene and provides a justification for the choice based on cinematographic principles."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"scene_description": {"type": "string", "description": "A brief description of the scene's content and mood."}},
            "required": ["scene_description"]
        }

    def execute(self, scene_description: str, **kwargs: Any) -> str:
        scene_lower = scene_description.lower()
        suggested_angle = random.choice(list(self.angle_justifications.keys()))  # nosec B311

        if "confrontation" in scene_lower or "intense" in scene_lower or "powerful" in scene_lower:
            suggested_angle = random.choice(["Close-Up", "Low Angle"])  # nosec B311
        elif "vast" in scene_lower or "lonely" in scene_lower or "establishing" in scene_lower:
            suggested_angle = "Wide Shot"
        elif "vulnerable" in scene_lower or "defeated" in scene_lower or "small" in scene_lower:
            suggested_angle = "High Angle"
        elif "unease" in scene_lower or "confused" in scene_lower or "disoriented" in scene_lower:
            suggested_angle = "Dutch Angle"
        elif "dialogue" in scene_lower or "conversation" in scene_lower:
            suggested_angle = "Medium Shot"

        justification = self.angle_justifications[suggested_angle]
        
        report = {
            "scene_description": scene_description,
            "suggested_angle": suggested_angle,
            "justification": f"A {suggested_angle} would be effective here {justification}"
        }
        return json.dumps(report, indent=2)

class ProposeDialogueLineTool(BaseTool):
    """Tool to propose a dialogue line for a character using a generative model."""
    def __init__(self, tool_name="propose_dialogue_line"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Proposes a dialogue line for a character based on their personality and the scene's context."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "character_description": {"type": "string", "description": "A brief description of the character (e.g., 'a cynical detective', 'a cheerful optimist')."},
                "scene_context": {"type": "string", "description": "The context of the scene (e.g., 'interrogating a suspect', 'receiving good news')."}
            },
            "required": ["character_description", "scene_context"]
        }

    def execute(self, character_description: str, scene_context: str, **kwargs: Any) -> str:
        prompt = f"Write a single, impactful line of dialogue for a character who is {character_description}. The context of the scene is: {scene_context}. The dialogue should be:"
        
        # Generate a slightly longer text and extract the first line.
        dialogue_full = film_model.generate_text(prompt, max_length=len(prompt.split()) + 30)
        
        # Clean up the output from the model
        generated_part = dialogue_full.replace(prompt, "").strip()
        first_line = generated_part.split('\n')[0]

        return json.dumps({"proposed_dialogue": first_line}, indent=2)

class GenerateStoryboardTool(BaseTool):
    """Tool to generate a text-based storyboard for a scene."""
    def __init__(self, tool_name="generate_storyboard"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a simple, text-based storyboard for a scene, outlining a sequence of shots."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scene_concept": {"type": "string", "description": "The concept of the scene to storyboard, ideally from the GenerateSceneConceptTool."}
            },
            "required": ["scene_concept"]
        }

    def execute(self, scene_concept: str, **kwargs: Any) -> str:
        prompt = f"Create a simple, 3-shot storyboard in text format for the following film scene concept:\n\n{scene_concept}\n\nStoryboard:\n1. Shot Type: [e.g., Wide Shot]\n   Action: [Describe the action and what is seen]\n2. Shot Type: [e.g., Medium Shot]\n   Action: [Describe the action]\n3. Shot Type: [e.g., Close-Up]\n   Action: [Describe the action]"
        
        storyboard = film_model.generate_text(prompt, max_length=250)
        # The model might repeat the prompt, so we clean it up.
        cleaned_storyboard = storyboard.split("Storyboard:")[-1].strip()

        return json.dumps({"storyboard": cleaned_storyboard}, indent=2)