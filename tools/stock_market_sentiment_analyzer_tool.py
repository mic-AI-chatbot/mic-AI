
import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool
from textblob import TextBlob # For sentiment analysis

logger = logging.getLogger(__name__)

class StockMarketSentimentAnalyzerTool(BaseTool):
    """
    A tool that analyzes news headlines or social media posts related to a stock,
    calculates sentiment, and provides an overall sentiment score and label.
    """

    def __init__(self, tool_name: str = "StockMarketSentimentAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.sentiment_file = os.path.join(self.data_dir, "stock_sentiment_records.json")
        
        # Stock sentiment records: {report_id: {stock_symbol: ..., text_data: [], average_score: ..., overall_sentiment: ...}}
        self.stock_sentiment_records: Dict[str, Dict[str, Any]] = self._load_data(self.sentiment_file, default={})

    @property
    def description(self) -> str:
        return "Analyzes news/social media for stock sentiment, provides score and label (bullish, bearish, neutral)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_stock_sentiment", "get_sentiment_report"]},
                "stock_symbol": {"type": "string"},
                "text_data": {"type": "array", "items": {"type": "string"}, "description": "List of news headlines or social media posts."},
                "report_id": {"type": "string", "description": "ID of the sentiment report to retrieve."}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_data(self):
        with open(self.sentiment_file, 'w') as f: json.dump(self.stock_sentiment_records, f, indent=2)

    def analyze_stock_sentiment(self, stock_symbol: str, text_data: List[str]) -> Dict[str, Any]:
        """Analyzes sentiment for a stock based on news headlines or social media posts."""
        if not text_data: return {"status": "info", "message": "No text data provided for sentiment analysis."}
        
        total_polarity = 0.0
        positive_keywords = []
        negative_keywords = []
        
        for text in text_data:
            blob = TextBlob(text)
            total_polarity += blob.sentiment.polarity
            
            # Simple keyword extraction for sentiment drivers
            if blob.sentiment.polarity > 0.1:
                positive_keywords.extend([word for word in text.lower().split() if word in ["good", "strong", "gain", "rise", "up"]])
            elif blob.sentiment.polarity < -0.1:
                negative_keywords.extend([word for word in text.lower().split() if word in ["bad", "weak", "loss", "fall", "down"]])
        
        average_polarity = round(total_polarity / len(text_data), 2)
        
        overall_sentiment_label = "neutral"
        if average_polarity > 0.2: overall_sentiment_label = "bullish"
        elif average_polarity < -0.2: overall_sentiment_label = "bearish"
        
        report_id = f"sentiment_report_{stock_symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "stock_symbol": stock_symbol, "text_data_count": len(text_data),
            "average_sentiment_score": average_polarity, "overall_sentiment_label": overall_sentiment_label,
            "key_positive_drivers": list(set(positive_keywords)),
            "key_negative_drivers": list(set(negative_keywords)),
            "analyzed_at": datetime.now().isoformat()
        }
        self.stock_sentiment_records[report_id] = report
        self._save_data()
        return report

    def get_sentiment_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated stock sentiment report."""
        report = self.stock_sentiment_records.get(report_id)
        if not report: raise ValueError(f"Sentiment report '{report_id}' not found.")
        return report

    def execute(self, operation: str, stock_symbol: str, **kwargs: Any) -> Any:
        if operation == "analyze_stock_sentiment":
            return self.analyze_stock_sentiment(stock_symbol, kwargs['text_data'])
        elif operation == "get_sentiment_report":
            return self.get_sentiment_report(kwargs['report_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating StockMarketSentimentAnalyzerTool functionality...")
    temp_dir = "temp_stock_sentiment_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sentiment_analyzer = StockMarketSentimentAnalyzerTool(data_dir=temp_dir)
    
    try:
        # 1. Analyze sentiment for Apple (AAPL) with positive news
        print("\n--- Analyzing sentiment for AAPL (positive news) ---")
        aapl_positive_news = [
            "Apple stock shows strong gains after record iPhone sales.",
            "Analysts are bullish on AAPL's new services revenue.",
            "Apple's innovation continues to drive market confidence."
        ]
        report1 = sentiment_analyzer.execute(operation="analyze_stock_sentiment", stock_symbol="AAPL", text_data=aapl_positive_news)
        print(json.dumps(report1, indent=2))

        # 2. Analyze sentiment for Tesla (TSLA) with mixed news
        print("\n--- Analyzing sentiment for TSLA (mixed news) ---")
        tsla_mixed_news = [
            "Tesla production numbers disappoint investors.",
            "Elon Musk's new tweet causes TSLA stock to fluctuate.",
            "Tesla's new battery technology shows promising results."
        ]
        report2 = sentiment_analyzer.execute(operation="analyze_stock_sentiment", stock_symbol="TSLA", text_data=tsla_mixed_news)
        print(json.dumps(report2, indent=2))

        # 3. Get sentiment report
        print(f"\n--- Getting sentiment report for '{report1['id']}' ---")
        retrieved_report = sentiment_analyzer.execute(operation="get_sentiment_report", stock_symbol="any", report_id=report1["id"]) # stock_symbol is not used for get_sentiment_report
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
