import logging
from typing import Union, List, Dict, Any
from tools.base_tool import BaseTool
from transformers import pipeline

logger = logging.getLogger(__name__)

# In-memory cache for summarization results
summarization_cache: Dict[str, str] = {}

class AbstractiveSummarizationTool(BaseTool):
    """
    A tool for generating abstractive summaries of text using a pre-trained model.
    This tool includes an in-memory cache to speed up repeated summarizations of the same text.
    """

    def __init__(self, tool_name: str = "abstractive_summarization_tool"):
        super().__init__(tool_name=tool_name)
        try:
            # The 'facebook/bart-large-cnn' model is a popular and effective model for abstractive summarization.
            self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
            self.summarizer = None

    @property
    def description(self) -> str:
        return "Generates an abstractive summary of the provided text, aiming to capture the main points concisely."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The input text to summarize. Should be at least a few sentences long."
                },
                "max_length": {
                    "type": "integer",
                    "description": "The maximum length of the summary in tokens.",
                    "default": 150
                },
                "min_length": {
                    "type": "integer",
                    "description": "The minimum length of the summary in tokens.",
                    "default": 30
                },
                "use_cache": {
                    "type": "boolean",
                    "description": "Whether to use the cache for this request.",
                    "default": True
                }
            },
            "required": ["text"]
        }

    def execute(self, text: str, max_length: int = 150, min_length: int = 30, use_cache: bool = True) -> str:
        """
        Generates an abstractive summary of the provided text.
        """
        if not self.summarizer:
            return "Error: Summarization model is not available."

        if not text or not text.strip():
            return "Error: Input text cannot be empty."
        
        # A simple check for minimum text length to ensure meaningful summarization
        if len(text.split()) < min_length:
            return f"Error: Input text is too short. It should be longer than the minimum summary length of {min_length} words."

        # Create a unique key for the cache based on the input parameters
        cache_key = f"{text}:{max_length}:{min_length}"

        if use_cache and cache_key in summarization_cache:
            logger.info("Returning cached summary.")
            return summarization_cache[cache_key]

        try:
            logger.info(f"Generating summary for text with length {len(text)}...")
            # The summarizer returns a list of summaries. We take the first one.
            summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            summary_text = summary[0]['summary_text']

            if use_cache:
                summarization_cache[cache_key] = summary_text
            
            return summary_text
        except Exception as e:
            error_msg = f"An error occurred during summarization: {e}"
            logger.error(error_msg, exc_info=True)
            return "An error occurred during summarization. Please try again later."