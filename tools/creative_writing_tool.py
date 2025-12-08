import logging
import json
import os
from typing import Dict, Any, List, Optional
from mic.hf_llm import HfLLM # Import the HfLLM
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class LLMCreativeWriter:
    """Manages the LLM instance for creative writing tasks, using a singleton pattern."""
    _llm = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMCreativeWriter, cls).__new__(cls)
            cls._instance._llm = HfLLM()
            if cls._instance._llm.llm is None:
                logger.error("LLM not initialized. Creative writing tools will not be fully functional.")
        return cls._instance

    def generate_response(self, prompt: str) -> str:
        if self._llm.llm is None:
            return json.dumps({"error": "LLM not available. Please ensure it is configured correctly."})
        try:
            return self._llm.generate_response(prompt)
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return json.dumps({"error": f"LLM generation failed: {e}"})

llm_creative_writer_instance = LLMCreativeWriter()

class GenerateCreativeContentTool(BaseTool):
    """Generates various types of creative content (e.g., poem, story, song, essay) based on a topic, genre, style, tone, and other parameters using an LLM."""
    def __init__(self, tool_name="generate_creative_content"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates various types of creative content (e.g., poem, story, song, essay) based on a topic, genre, style, tone, and other parameters using an LLM."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "content_type": {"type": "string", "description": "The type of content to generate.", "enum": ["poem", "story", "song", "essay", "article", "script"]},
                "topic": {"type": "string", "description": "The main topic or subject of the content."},
                "genre": {"type": "string", "description": "Optional: The genre for stories (e.g., 'fantasy', 'sci-fi', 'romance').", "default": None},
                "characters": {"type": "string", "description": "Optional: Characters to include in stories.", "default": None},
                "length": {"type": "string", "description": "Desired length ('short', 'medium', 'long').", "enum": ["short", "medium", "long"], "default": "medium"},
                "style": {"type": "string", "description": "Writing style (e.g., 'formal', 'casual', 'poetic').", "default": "neutral"},
                "tone": {"type": "string", "description": "Tone of the writing (e.g., 'optimistic', 'critical', 'humorous').", "default": "informative"},
                "keywords": {"type": "string", "description": "Optional: Comma-separated keywords to include in the content.", "default": None},
                "target_audience": {"type": "string", "description": "Optional: The intended audience for the content.", "default": None},
                "structure": {"type": "string", "description": "Optional: Specific structural requirements for the content (e.g., '3 verses, 1 chorus').", "default": None},
                "output_format": {"type": "string", "description": "Optional: The desired output format ('text', 'markdown').", "enum": ["text", "markdown"], "default": "text"},
                "context": {"type": "string", "description": "Optional: Additional context to guide the generation.", "default": None}
            },
            "required": ["content_type", "topic"]
        }

    def execute(self, content_type: str, topic: str, genre: Optional[str] = None, characters: Optional[str] = None, length: str = "medium", style: str = "neutral", tone: str = "informative", keywords: Optional[str] = None, target_audience: Optional[str] = None, structure: Optional[str] = None, output_format: str = "text", context: Optional[str] = None, **kwargs: Any) -> str:
        base_prompt = f"Generate a {length} {content_type} about {topic}."
        
        if genre and content_type == "story":
            base_prompt += f" in the {genre} genre."
        if characters and content_type == "story":
            base_prompt += f" with characters: {characters}."
        if style:
            base_prompt += f" Write in a {style} style."
        if tone:
            base_prompt += f" The tone should be {tone}."
        if keywords:
            base_prompt += f" Include the following keywords: {keywords}."
        if target_audience:
            base_prompt += f" The target audience is {target_audience}."
        if structure:
            base_prompt += f" Follow this structure: {structure}."
        if context:
            base_prompt += f" Use the following context: {context}."

        full_prompt = f"{base_prompt} Provide the output in {output_format} format. Also provide a brief summary of the generated content. Provide the output in JSON format with keys 'generated_content' and 'summary'.\n\nJSON Output:"
        
        llm_response = llm_creative_writer_instance.generate_response(full_prompt)
        
        try:
            return json.dumps(json.loads(llm_response), indent=2)
        except json.JSONDecodeError:
            return json.dumps({"error": "LLM response was not valid JSON.", "raw_llm_response": llm_response})