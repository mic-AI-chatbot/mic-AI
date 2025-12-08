import logging
import json
import random
import re
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Choreography generation tools will not be fully functional.")

logger = logging.getLogger(__name__)

class ChoreographyModel:
    """Manages the text generation model for choreography tasks, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChoreographyModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for choreography generation are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for choreography generation...")
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

choreography_model_instance = ChoreographyModel()

class GenerateDanceMovesTool(BaseTool):
    """Generates a list of detailed dance moves suitable for a given music style and intensity using an AI model."""
    def __init__(self, tool_name="generate_dance_moves"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a list of detailed dance moves suitable for a given music style and intensity using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "music_style": {"type": "string", "description": "The style of music (e.g., 'hip_hop', 'ballet', 'salsa', 'contemporary', 'jazz').", "enum": ["hip_hop", "ballet", "salsa", "contemporary", "jazz"]},
                "intensity": {"type": "string", "description": "The desired intensity of the dance moves.", "enum": ["low", "medium", "high"], "default": "medium"}
            },
            "required": ["music_style"]
        }

    def execute(self, music_style: str, intensity: str = "medium", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        prompt = f"Generate a list of 5-7 detailed and creative dance moves for a '{music_style}' style with '{intensity}' intensity. Describe each move clearly. Dance Moves:"
        
        generated_moves_text = choreography_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 400)
        
        # Attempt to parse the generated text into a list of moves
        # Assuming each move is on a new line or numbered
        moves_list = [line.strip() for line in generated_moves_text.split('\n') if line.strip() and not line.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.'))]
        if not moves_list: # If numbered list, try to extract
            moves_list = [re.sub(r'^\d+\.\s*', '', line).strip() for line in generated_moves_text.split('\n') if re.match(r'^\d+\.\s*', line)]

        report = {
            "music_style": music_style,
            "intensity": intensity,
            "generated_dance_moves": moves_list
        }
        return json.dumps(report, indent=2)

class CreateChoreographySequenceTool(BaseTool):
    """Creates a coherent choreography sequence from a list of dance moves using an AI model."""
    def __init__(self, tool_name="create_choreography_sequence"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a coherent choreography sequence by arranging a list of dance moves into a routine, including timing and transitions, using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "dance_moves": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of dance moves to arrange into a sequence (e.g., from GenerateDanceMovesTool)."
                },
                "music_style": {"type": "string", "description": "The music style for the choreography.", "enum": ["hip_hop", "ballet", "salsa", "contemporary", "jazz"]},
                "duration_seconds": {"type": "integer", "description": "The desired duration of the choreography in seconds.", "default": 60}
            },
            "required": ["dance_moves", "music_style"]
        }

    def execute(self, dance_moves: List[str], music_style: str, duration_seconds: int = 60, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        moves_str = "\n".join([f"- {move}" for move in dance_moves])
        prompt = f"Create a coherent choreography sequence for '{music_style}' music, lasting approximately {duration_seconds} seconds, using the following dance moves. Describe the timing, transitions, and overall flow. Dance Moves:\n{moves_str}\n\nChoreography Sequence:"
        
        generated_choreography = choreography_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 800)
        
        report = {
            "music_style": music_style,
            "duration_seconds": duration_seconds,
            "dance_moves_used": dance_moves,
            "choreography_sequence": generated_choreography
        }
        return json.dumps(report, indent=2)