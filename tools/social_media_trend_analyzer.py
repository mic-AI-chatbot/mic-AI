import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SocialMediaTrendAnalyzerSimulatorTool(BaseTool):
    """
    A tool that simulates social media trend analysis, allowing for analyzing
    trends for a given topic or keyword across various platforms.
    """

    def __init__(self, tool_name: str = "SocialMediaTrendAnalyzerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.reports_file = os.path.join(self.data_dir, "social_media_trend_reports.json")
        
        # Trend analysis reports: {report_id: {topic: ..., platform: ..., metrics: {}}}
        self.trend_analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates analyzing social media trends for a given topic or keyword across platforms."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["analyze_trends", "get_trend_report"]},
                "topic": {"type": "string"},
                "platform": {"type": "string", "enum": ["Twitter", "Facebook", "Instagram", "TikTok"], "default": "Twitter"},
                "report_id": {"type": "string", "description": "ID of the trend report to retrieve."}
            },
            "required": ["operation"] # Only operation is required at top level
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
        with open(self.reports_file, 'w') as f: json.dump(self.trend_analysis_reports, f, indent=2)

    def analyze_trends(self, topic: str, platform: str = "Twitter") -> Dict[str, Any]:
        """Simulates analyzing social media trends for a given topic."""
        report_id = f"trend_report_{topic.replace(' ', '_')}_{platform}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        mentions_count = random.randint(1000, 100000)  # nosec B311
        sentiment_positive = random.uniform(0.4, 0.7)  # nosec B311
        sentiment_negative = random.uniform(0.1, 0.3)  # nosec B311
        sentiment_neutral = 1.0 - sentiment_positive - sentiment_negative
        
        trend_direction = random.choice(["rising", "falling", "stable"])  # nosec B311
        top_hashtags = random.sample([f"#{topic.replace(' ', '')}", "#Trending", "#News", "#Viral"], k=random.randint(2, 4))  # nosec B311
        
        report = {
            "id": report_id, "topic": topic, "platform": platform,
            "mentions_count": mentions_count,
            "sentiment_distribution": {
                "positive": round(sentiment_positive, 2),
                "negative": round(sentiment_negative, 2),
                "neutral": round(sentiment_neutral, 2)
            },
            "trend_direction": trend_direction,
            "top_hashtags": top_hashtags,
            "analyzed_at": datetime.now().isoformat()
        }
        self.trend_analysis_reports[report_id] = report
        self._save_data()
        return report

    def get_trend_report(self, report_id: str) -> Dict[str, Any]:
        """Retrieves a previously generated trend analysis report."""
        report = self.trend_analysis_reports.get(report_id)
        if not report: raise ValueError(f"Trend report '{report_id}' not found.")
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "analyze_trends":
            topic = kwargs.get('topic')
            if not topic:
                raise ValueError("Missing 'topic' for 'analyze_trends' operation.")
            return self.analyze_trends(topic, kwargs.get('platform', 'Twitter'))
        elif operation == "get_trend_report":
            report_id = kwargs.get('report_id')
            if not report_id:
                raise ValueError("Missing 'report_id' for 'get_trend_report' operation.")
            return self.get_trend_report(report_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SocialMediaTrendAnalyzerSimulatorTool functionality...")
    temp_dir = "temp_social_trends_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    trend_analyzer = SocialMediaTrendAnalyzerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Analyze trends for "AI Ethics" on Twitter
        print("\n--- Analyzing trends for 'AI Ethics' on Twitter ---")
        report1 = trend_analyzer.execute(operation="analyze_trends", topic="AI Ethics", platform="Twitter")
        print(json.dumps(report1, indent=2))

        # 2. Analyze trends for "Sustainable Fashion" on Instagram
        print("\n--- Analyzing trends for 'Sustainable Fashion' on Instagram ---")
        report2 = trend_analyzer.execute(operation="analyze_trends", topic="Sustainable Fashion", platform="Instagram")
        print(json.dumps(report2, indent=2))

        # 3. Get trend report
        print(f"\n--- Getting trend report for '{report1['id']}' ---")
        retrieved_report = trend_analyzer.execute(operation="get_trend_report", topic="any", report_id=report1["id"]) # topic is not used for get_trend_report
        print(json.dumps(retrieved_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")