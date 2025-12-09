import logging
import json
import random
from typing import Dict, Any, List

from tools.base_tool import BaseTool
from textblob import TextBlob # For sentiment analysis

logger = logging.getLogger(__name__)

class SentimentAnalysisAPISimulatorTool(BaseTool):
    """
    A tool that simulates a sentiment analysis API, analyzing text for
    sentiment (positive, negative, neutral) and providing polarity and subjectivity scores.
    """

    def __init__(self, tool_name: str = "SentimentAnalysisAPISimulator", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)

    @property
    def description(self) -> str:
        return "Simulates a sentiment analysis API: analyzes text for sentiment (positive, negative, neutral)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to analyze for sentiment."}
            },
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Analyzes text for sentiment (polarity, subjectivity, and a sentiment label).
        """
        if not text:
            raise ValueError("Input text cannot be empty.")

        blob = TextBlob(text)
        polarity = round(blob.sentiment.polarity, 2)
        subjectivity = round(blob.sentiment.subjectivity, 2)
        
        sentiment_label = "neutral"
        if polarity > 0.1:
            sentiment_label = "positive"
        elif polarity < -0.1:
            sentiment_label = "negative"
        
        return {
            "status": "success",
            "text": text,
            "polarity": polarity,
            "subjectivity": subjectivity,
            "sentiment_label": sentiment_label
        }

if __name__ == '__main__':
    print("Demonstrating SentimentAnalysisAPISimulatorTool functionality...")
    
    sentiment_tool = SentimentAnalysisAPISimulatorTool()
    
    try:
        # 1. Analyze positive text
        print("\n--- Analyzing positive text ---")
        text1 = "This product is absolutely fantastic! I love it."
        result1 = sentiment_tool.execute(text=text1)
        print(json.dumps(result1, indent=2))

        # 2. Analyze negative text
        print("\n--- Analyzing negative text ---")
        text2 = "I am very disappointed with the service. It was terrible."
        result2 = sentiment_tool.execute(text=text2)
        print(json.dumps(result2, indent=2))

        # 3. Analyze neutral text
        print("\n--- Analyzing neutral text ---")
        text3 = "The sky is blue and the grass is green."
        result3 = sentiment_tool.execute(text=text3)
        print(json.dumps(result3, indent=2))

        # 4. Analyze mixed sentiment text
        print("\n--- Analyzing mixed sentiment text ---")
        text4 = "The movie had a great plot, but the acting was terrible."
        result4 = sentiment_tool.execute(text=text4)
        print(json.dumps(result4, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")