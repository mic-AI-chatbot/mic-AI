import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool
from textblob import TextBlob
import spacy
from collections import Counter

logger = logging.getLogger(__name__)

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'.")
    nlp = None

class PostEventFeedbackAnalyzerTool(BaseTool):
    """
    A tool that analyzes post-event feedback to identify key insights,
    sentiment, and areas for improvement.
    """

    def __init__(self, tool_name: str = "PostEventFeedbackAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "feedback_analysis_reports.json")
        # Reports structure: {report_id: {event_name: ..., sentiment_summary: ..., keywords: ..., examples: []}}
        self.feedback_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Analyzes post-event feedback to identify key insights, sentiment, and areas for improvement."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_feedback"], "description": "The operation to perform."},
                "event_name": {"type": "string", "description": "The name of the event for which to analyze feedback."},
                "feedback_data": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of feedback comments or survey responses."
                }
            },
            "required": ["operation", "event_name", "feedback_data"]
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
        with open(self.reports_file, 'w') as f: json.dump(self.feedback_reports, f, indent=2)

    def execute(self, operation: str, event_name: str, feedback_data: List[str], **kwargs: Any) -> Dict[str, Any]:
        """
        Analyzes post-event feedback data to generate a summary report.
        """
        if operation != "analyze_feedback":
            raise ValueError(f"Invalid operation: {operation}. Only 'analyze_feedback' is supported.")
        if not feedback_data:
            return {"status": "info", "message": "No feedback data provided for analysis."}
        if nlp is None:
            raise RuntimeError("spaCy model 'en_core_web_sm' is not available. Cannot perform detailed NLP analysis.")

        report_id = f"feedback_report_{event_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        total_feedback = len(feedback_data)
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        all_keywords = []
        positive_examples = []
        negative_examples = []

        for comment in feedback_data:
            blob = TextBlob(comment)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                positive_count += 1
                positive_examples.append(comment)
            elif polarity < -0.1:
                negative_count += 1
                negative_examples.append(comment)
            else:
                neutral_count += 1
            
            doc = nlp(comment)
            keywords = [token.lemma_.lower() for token in doc if token.is_alpha and not token.is_stop and token.pos_ in ["NOUN", "ADJ", "VERB"]]
            all_keywords.extend(keywords)
        
        overall_sentiment = "mostly positive" if positive_count > negative_count else "mostly negative" if negative_count > positive_count else "mixed"
        
        top_keywords = Counter(all_keywords).most_common(10)
        
        report = {
            "report_id": report_id,
            "event_name": event_name,
            "total_feedback_comments": total_feedback,
            "sentiment_summary": {
                "overall_sentiment": overall_sentiment,
                "positive_comments": positive_count,
                "negative_comments": negative_count,
                "neutral_comments": neutral_count
            },
            "top_keywords": top_keywords,
            "example_positive_comments": random.sample(positive_examples, min(3, len(positive_examples))),  # nosec B311
            "example_negative_comments": random.sample(negative_examples, min(3, len(negative_examples))),  # nosec B311
            "generated_at": datetime.now().isoformat()
        }
        self.feedback_reports[report_id] = report
        self._save_data()
        return report

if __name__ == '__main__':
    print("Demonstrating PostEventFeedbackAnalyzerTool functionality...")
    temp_dir = "temp_feedback_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = PostEventFeedbackAnalyzerTool(data_dir=temp_dir)
    
    try:
        # 1. Analyze feedback for a conference
        print("\n--- Analyzing feedback for 'Annual Tech Conference 2023' ---")
        feedback_comments = [
            "The speakers were excellent and very informative!",
            "Networking opportunities were great, but the food was terrible.",
            "I learned a lot, especially from the AI ethics session.",
            "Too many technical issues with the virtual platform.",
            "Overall a positive experience, well organized.",
            "The keynote speaker was inspiring.",
            "Long queues for registration, very frustrating.",
            "Good content, but the schedule was too packed."
        ]
        report = analyzer_tool.execute(event_name="Annual Tech Conference 2023", feedback_data=feedback_comments)
        print(json.dumps(report, indent=2))

        # 2. Analyze feedback for a product launch
        print("\n--- Analyzing feedback for 'Product X Launch Event' ---")
        product_feedback = [
            "Product X is revolutionary! Love the new features.",
            "The demo was confusing and buggy.",
            "Great potential, but needs more polish.",
            "Very excited about this product, it solves a real problem.",
            "Poor user interface, hard to navigate."
        ]
        product_report = analyzer_tool.execute(event_name="Product X Launch Event", feedback_data=product_feedback)
        print(json.dumps(product_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")