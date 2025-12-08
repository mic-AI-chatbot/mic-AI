import logging
import json
import random
from typing import Union, List, Dict, Any, Optional

# Deferring transformers import
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered feedback analysis will not be available. Please install 'transformers' and 'torch'.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class FeedbackAnalysisModel:
    """Manages AI models for customer feedback analysis, using a singleton pattern."""
    _sentiment_analyzer = None
    _theme_identifier = None # Using a text generation model for theme identification
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FeedbackAnalysisModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for feedback analysis are not installed.")
                return cls._instance # Return instance without models
            
            try:
                logger.info("Initializing sentiment analyzer (distilbert-base-uncased-finetuned-sst-2-english)...")
                cls._instance._sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
                logger.info("Initializing text generation model (gpt2) for theme identification...")
                cls._instance._theme_identifier = pipeline("text-generation", model="gpt2")
            except Exception as e:
                logger.error(f"Failed to load AI models for feedback analysis: {e}")
        return cls._instance

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        if not self._sentiment_analyzer: return {"error": "Sentiment analyzer not available. Check logs for loading errors."}
        sentiment_result = self._sentiment_analyzer(text)[0]
        return {"sentiment": sentiment_result['label'].lower(), "score": round(sentiment_result['score'], 2)}

    def identify_themes(self, text: str) -> List[str]:
        if not self._theme_identifier: return ["Error: Theme identifier not available. Check logs for loading errors."]
        prompt = f"Identify the key themes and topics from the following customer feedback. List them concisely, one theme per line.\n\nFeedback: {text}\n\nThemes:"
        try:
            generated = self._theme_identifier(prompt, max_length=len(prompt.split()) + 100, num_return_sequences=1, pad_token_id=self._theme_identifier.tokenizer.eos_token_id)[0]['generated_text']
            themes_text = generated.replace(prompt, "").strip()
            return [theme.strip() for theme in themes_text.split('\n') if theme.strip()]
        except Exception as e:
            logger.error(f"Theme identification failed: {e}")
            return ["Error: Theme identification failed."]

feedback_analysis_model_instance = FeedbackAnalysisModel()

class AnalyzeFeedbackSentimentTool(BaseTool):
    """Analyzes customer feedback text for sentiment using an AI model."""
    def __init__(self, tool_name="analyze_feedback_sentiment"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes customer feedback text for sentiment (positive, negative, neutral) and returns a sentiment score using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"feedback_text": {"type": "string", "description": "The customer feedback text to analyze."}},
            "required": ["feedback_text"]
        }

    def execute(self, feedback_text: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for feedback analysis are not available. Please install 'transformers', 'torch'."})

        result = feedback_analysis_model_instance.analyze_sentiment(feedback_text)
        return json.dumps({
            "feedback_text": feedback_text,
            "sentiment_analysis": result,
            "message": "Sentiment analysis completed."
        }, indent=2)

class IdentifyFeedbackThemesTool(BaseTool):
    """Identifies key themes and topics from customer feedback using an AI model."""
    def __init__(self, tool_name="identify_feedback_themes"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies key themes and topics present in customer feedback text, categorizing common issues or praises using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"feedback_text": {"type": "string", "description": "The customer feedback text to analyze for themes."}},
            "required": ["feedback_text"]
        }

    def execute(self, feedback_text: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for feedback analysis are not available. Please install 'transformers', 'torch'."})

        themes = feedback_analysis_model_instance.identify_themes(feedback_text)
        return json.dumps({
            "feedback_text": feedback_text,
            "identified_themes": themes,
            "message": "Theme identification completed."
        }, indent=2)