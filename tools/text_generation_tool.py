import logging
from typing import Dict, Any
from tools.base_tool import BaseTool
from mic.llm_loader import get_llm
import json # Import json for printing results in main block

logger = logging.getLogger(__name__)

class TextGenerationTool(BaseTool):
    def __init__(self, tool_name: str = "text_generation_tool"):
        super().__init__(tool_name)
        self.llm = get_llm() # Instantiate the LLM directly

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The initial prompt for text generation."},
                "max_length": {"type": "integer", "minimum": 10, "default": 50, "description": "The maximum length of the generated text."}
            },
            "required": ["prompt"]
        }

    def execute(self, prompt: str, max_length: int = 50, **kwargs: Any) -> str:
        """
        Generates text based on a given prompt using a HuggingFace LLM.

        Args:
            prompt: The initial prompt for text generation.
            max_length: The maximum length of the generated text.

        Returns:
            The generated text.
        """
        if not prompt:
            raise ValueError("Missing 'prompt' for text generation.")

        logger.info(f"Generating text for prompt: {prompt[:50]}...")
        # In a real scenario, max_length would ideally be passed to the LLM's generate_response method.
        generated_text = self.llm.generate_response(prompt)
        return generated_text[:max_length]

if __name__ == '__main__':
    print("Demonstrating TextGenerationTool functionality...")
    
    text_gen_tool = TextGenerationTool()
    
    try:
        # 1. Generate a short story
        print("\n--- Generating a short story ---")
        story_prompt = "Once upon a time, in a land far away, there was a brave knight."
        generated_story = text_gen_tool.execute(prompt=story_prompt, max_length=100)
        print(generated_story)

        # 2. Generate a poem
        print("\n--- Generating a poem ---")
        poem_prompt = "Write a short poem about nature."
        generated_poem = text_gen_tool.execute(prompt=poem_prompt, max_length=80)
        print(generated_poem)

    except Exception as e:
        print(f"\nAn error occurred: {e}")