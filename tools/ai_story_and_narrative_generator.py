import asyncio
import logging
from typing import Dict, Any

from mic.llm_loader import get_llm
from tools.base_tool import BaseTool

class AiStoryAndNarrativeGenerator(BaseTool):
    """
    A tool to generate stories and narratives using a local LLM.
    """

    def __init__(self, tool_name: str = "ai_story_and_narrative_generator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Creates coherent and context-aware stories or scripts based on a prompt."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The starting idea or core concept for the story."
                },
                "genre": {
                    "type": "string",
                    "description": "The genre of the story (e.g., 'fantasy', 'sci-fi', 'mystery', 'romance').",
                    "enum": ["fantasy", "sci-fi", "mystery", "romance", "horror", "thriller", "drama", "comedy", "historical", "western", "adventure", "dystopian", "cyberpunk", "steampunk", "post-apocalyptic", "superhero", "slice of life", "young adult", "children's", "biography", "autobiography", "non-fiction", "other"],
                    "default": "other"
                },
                "characters": {
                    "type": "string",
                    "description": "Key characters in the story (e.g., 'a brave knight, a wise wizard')."
                },
                "setting": {
                    "type": "string",
                    "description": "The setting of the story (e.g., 'a futuristic city', 'a medieval castle')."
                },
                "plot_points": {
                    "type": "string",
                    "description": "Key plot points or events to include in the narrative, separated by semicolons (e.g., 'a mysterious artifact is found; a journey begins; a betrayal occurs')."
                },
                "max_length": {
                    "type": "integer",
                    "description": "The approximate maximum length of the story in tokens.",
                    "default": 500
                }
            },
            "required": ["prompt"]
        }

    async def execute(self, prompt: str, genre: str = "other", characters: str = None, setting: str = None, plot_points: str = None, max_length: int = 500) -> Dict[str, Any]:
        """
        Generates a story based on a prompt and additional parameters using the configured local LLM.
        """
        if not prompt:
            return {"error": "Prompt cannot be empty."}

        self.logger.info(f"Generating story from prompt: '{prompt}' with genre='{genre}', characters='{characters}', setting='{setting}', plot_points='{plot_points}'")
        
        llm = get_llm()
        
        full_story_parts = []
        try:
            creative_prompt_parts = [f"Write a compelling and imaginative story based on the following idea: {prompt}"]
            if genre and genre != "other":
                creative_prompt_parts.append(f"Genre: {genre}.")
            if characters:
                creative_prompt_parts.append(f"Main characters: {characters}.")
            if setting:
                creative_prompt_parts.append(f"Setting: {setting}.")
            if plot_points:
                creative_prompt_parts.append(f"Key plot points: {plot_points}.")
            
            creative_prompt = " ".join(creative_prompt_parts)
            
            response_stream = llm.stream_response(prompt=creative_prompt)
            
            async for chunk in response_stream:
                if chunk.get("type") == "token" and chunk.get("content"):
                    full_story_parts.append(chunk["content"])
                elif chunk.get("type") == "error":
                    self.logger.error(f"Error from LLM stream: {chunk.get('content')}")
                    return {"error": f"Error generating story: {chunk.get('content')}"}

            if not full_story_parts:
                return {"error": "The model did not return a story. Please try a different prompt or parameters."}

            generated_story = "".join(full_story_parts)
            return {"story": generated_story, "genre": genre, "characters": characters, "setting": setting, "plot_points": plot_points}

        except Exception as e:
            self.logger.error(f"An exception occurred while generating the story: {e}", exc_info=True)
            return {"error": f"An unexpected error occurred: {e}"}

    def run_sync(self, prompt: str, genre: str = "other", characters: str = None, setting: str = None, plot_points: str = None, max_length: int = 500) -> Dict[str, Any]:
        """
        Synchronous wrapper for the async execute method for testing.
        """
        try:
            return asyncio.run(self.execute(prompt=prompt, genre=genre, characters=characters, setting=setting, plot_points=plot_points, max_length=max_length))
        except Exception as e:
            self.logger.error(f"Error running story generator synchronously: {e}")
            return {"error": f"Failed to run story generator: {e}"}