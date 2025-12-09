import logging
from typing import Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class WordAndAlphabetCounterTool(BaseTool):
    """
    A tool for counting words and alphabets in a given text.
    """

    def __init__(self, tool_name: str = "word_and_alphabet_counter_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Counts the number of words and alphabets (letters) in a provided text content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text_content": {"type": "string", "description": "The text content to analyze."}
            },
            "required": ["text_content"]
        }

    def execute(self, text_content: str) -> Dict[str, Any]:
        """
        Counts the number of words and alphabets in a given text.
        """
        logger.info(f"Counting words and alphabets for text (first 50 chars): {text_content[:50]}...")

        word_count = len(text_content.split())
        alphabet_count = sum(c.isalpha() for c in text_content)

        return {
            "text_content_preview": text_content[:50] + "...",
            "word_count": word_count,
            "alphabet_count": alphabet_count,
            "message": f"Analysis complete. Words: {word_count}, Alphabets: {alphabet_count}."
        }

def execute(text_content: str) -> Dict[str, Any]:
    """Legacy execute function for backward compatibility."""
    tool = WordAndAlphabetCounterTool()
    return tool.execute(text_content)
