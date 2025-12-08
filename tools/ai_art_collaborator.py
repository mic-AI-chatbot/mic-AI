import logging
import json
import random
from typing import Dict, Any
from tools.base_tool import BaseTool
import torch
from diffusers import StableDiffusionPipeline
import os

logger = logging.getLogger(__name__)

class DynamicPromptGenerator:
    """Generates dynamic and creative prompts for AI art."""
    def __init__(self, tool_name):
        self.subjects = ["a majestic lion", "a curious robot", "a forgotten queen", "a mythical creature", "a lone astronaut"]
        self.settings = ["in a neon-lit cyberpunk city", "in a whimsical forest of giant mushrooms", "on a desolate alien planet", "in a grand, underwater ballroom", "at the edge of a black hole"]
        self.actions = ["contemplating a glowing orb", "leading an army of clockwork soldiers", "discovering a hidden portal", "painting a masterpiece", "navigating a field of asteroids"]
        self.styles = ["digital painting", "concept art", "surrealism", "artstation", "highly detailed", "cinematic lighting"]

    def generate(self) -> str:
        subject = random.choice(self.subjects)  # nosec B311
        setting = random.choice(self.settings)  # nosec B311
        action = random.choice(self.actions)  # nosec B311
        style = random.choice(self.styles)  # nosec B311
        
        return f"{subject} {action} {setting}, {style}"

class GetCreativePromptTool(BaseTool):
    """Tool to generate a dynamic, creative prompt for AI art generation."""
    def __init__(self, tool_name="get_creative_prompt"):
        super().__init__(tool_name=tool_name)
        self.generator = DynamicPromptGenerator(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a dynamic and creative prompt to inspire AI art generation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        prompt = self.generator.generate()
        return json.dumps({"prompt": prompt}, indent=2)

class GenerateArtStyleSuggestionTool(BaseTool):
    """Tool to suggest an artistic style for a given creative prompt."""
    def __init__(self, tool_name="generate_art_style_suggestion"):
        super().__init__(tool_name=tool_name)
        self.style_map = {
            "cyberpunk": "A 'Cyberpunk' style would be great for this, with neon lights, futuristic technology, and a gritty, dystopian atmosphere.",
            "fantasy": "A 'Fantasy Art' style would fit well, with magical elements, mythical creatures, and epic, imaginative landscapes.",
            "surreal": "A 'Surrealist' approach could be very interesting, focusing on dream-like, illogical scenes and unexpected juxtapositions.",
            "steampunk": "Consider a 'Steampunk' style, featuring retrofuturistic technology powered by steam and clockwork, with Victorian aesthetics.",
            "default": "A 'Digital Painting' style with a focus on 'Concept Art' would be a good starting point, aiming for a detailed and realistic rendering of the scene."
        }

    @property
    def description(self) -> str:
        return "Suggests a detailed artistic style for a given creative prompt."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"prompt": {"type": "string", "description": "The creative prompt to analyze."}},
            "required": ["prompt"]
        }

    def execute(self, prompt: str, **kwargs: Any) -> str:
        prompt_lower = prompt.lower()
        suggestion = self.style_map["default"]

        if "cyberpunk" in prompt_lower or "robot" in prompt_lower or "neon" in prompt_lower:
            suggestion = self.style_map["cyberpunk"]
        elif "forest" in prompt_lower or "creature" in prompt_lower or "mythical" in prompt_lower or "queen" in prompt_lower:
            suggestion = self.style_map["fantasy"]
        elif "dream" in prompt_lower or "surreal" in prompt_lower or "underwater" in prompt_lower:
            suggestion = self.style_map["surreal"]
        elif "clockwork" in prompt_lower or "gears" in prompt_lower:
            suggestion = self.style_map["steampunk"]

        return json.dumps({"prompt": prompt, "style_suggestion": suggestion}, indent=2)

class GenerateAIArtTool(BaseTool):
    """Tool to generate AI art using a text-to-image model."""
    _pipe = None

    def __init__(self, tool_name="generate_ai_art"):
        super().__init__(tool_name=tool_name)
        if GenerateAIArtTool._pipe is None:
            self._initialize_pipeline()

    def _initialize_pipeline(self):
        logger.warning("AI Art Generation has been temporarily disabled to prevent memory-related crashes.")
        GenerateAIArtTool._pipe = None

    @property
    def description(self) -> str:
        return "Generates an image from a text prompt using a Stable Diffusion model and saves it to a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The text prompt to generate the image from."},
                "output_path": {"type": "string", "description": "The path to save the generated image file (e.g., 'generated_art.png')."}
            },
            "required": ["prompt", "output_path"]
        }

    def execute(self, prompt: str, output_path: str, **kwargs: Any) -> str:
        if GenerateAIArtTool._pipe is None:
            return json.dumps({"error": "Stable Diffusion pipeline is not initialized. Check logs for errors."})

        try:
            logger.info(f"Generating image for prompt: {prompt}")
            image = GenerateAIArtTool._pipe(prompt).images[0]
            
            # Ensure the output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            image.save(output_path)
            logger.info(f"Image successfully generated and saved to '{output_path}'")
            return json.dumps({"message": f"Image successfully generated and saved to '{os.path.abspath(output_path)}'"}, indent=2)
        except Exception as e:
            logger.error(f"AI art generation failed: {e}")
            return json.dumps({"error": f"An error occurred during image generation: {e}"}, indent=2)
