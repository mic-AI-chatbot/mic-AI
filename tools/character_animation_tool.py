import logging
import json
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Character animation tools will not be fully functional.")

logger = logging.getLogger(__name__)

class AnimationModel:
    """Manages the text generation model for animation tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnimationModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for animation are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for animation...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

animation_model_instance = AnimationModel()

class GenerateCharacterAnimationTool(BaseTool):
    """Generates a text-based description of an animation for a character using an AI model."""
    def __init__(self, tool_name="generate_character_animation"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a text-based description of an animation (e.g., walk, run, jump, idle) for a specified character, simulating the animation output."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "character_name": {"type": "string", "description": "The name of the character to animate."},
                "animation_type": {"type": "string", "description": "The type of animation to generate.", "enum": ["walk", "run", "jump", "idle", "talk", "wave"]},
                "character_description": {"type": "string", "description": "A brief description of the character (e.g., 'a tall knight', 'a small goblin')."}
            },
            "required": ["character_name", "animation_type", "character_description"]
        }

    def execute(self, character_name: str, animation_type: str, character_description: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Generate a detailed, text-based description of a '{animation_type}' animation for a character named '{character_name}', who is '{character_description}'. Describe the character's movements, posture, and any subtle details. Animation Description:"
        
        generated_animation_description = animation_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 300)
        
        report = {
            "character_name": character_name,
            "animation_type": animation_type,
            "animation_description": generated_animation_description
        }
        return json.dumps(report, indent=2)

class GenerateFacialExpressionsTool(BaseTool):
    """Generates a text-based description of facial expressions for a character using an AI model."""
    def __init__(self, tool_name="generate_facial_expressions"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a text-based description of facial expressions (e.g., happy, sad, angry) for a specified character, simulating the visual output."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "character_name": {"type": "string", "description": "The name of the character to generate expressions for."},
                "expression_type": {"type": "string", "description": "The type of facial expression to generate.", "enum": ["happy", "sad", "angry", "surprised", "confused", "thoughtful"]},
                "character_description": {"type": "string", "description": "A brief description of the character (e.g., 'a stoic warrior', 'a cheerful child')."}
            },
            "required": ["character_name", "expression_type", "character_description"]
        }

    def execute(self, character_name: str, expression_type: str, character_description: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Generate a detailed, text-based description of a '{expression_type}' facial expression for a character named '{character_name}', who is '{character_description}'. Describe the character's eyes, mouth, eyebrows, and any subtle nuances. Facial Expression Description:"
        
        generated_expression_description = animation_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 200)
        
        report = {
            "character_name": character_name,
            "expression_type": expression_type,
            "expression_description": generated_expression_description
        }
        return json.dumps(report, indent=2)