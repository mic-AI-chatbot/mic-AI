import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SocialListeningSimulatorTool(BaseTool):
    """
    A tool that simulates social listening, allowing for monitoring keywords,
    analyzing sentiment, identifying influencers, and generating reports.
    """

    def __init__(self, tool_name: str = "SocialListeningSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.keywords_file = os.path.join(self.data_dir, "monitored_keywords.json")
        self.reports_file = os.path.join(self.data_dir, "social_listening_reports.json")
        
        # Monitored keywords: {keyword: {platform: {mentions: ..., sentiment: ...}}}
        self.monitored_keywords: Dict[str, Dict[str, Any]] = self._load_data(self.keywords_file, default={})
        # Analysis reports: {report_id: {topic: ..., platform: ..., metrics: {}}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates social listening: monitor keywords, analyze sentiment, identify influencers, generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["monitor_keywords", "analyze_sentiment", "identify_influencers", "generate_report"]},
                "keywords": {"type": "array", "items": {"type": "string"}},
                "platform": {"type": "string", "enum": ["twitter", "facebook", "instagram", "reddit"], "default": "twitter"},
                "topic": {"type": "string"},
                "mentions": {"type": "array", "items": {"type": "string"}, "description": "List of simulated social media mentions."},
                "report_type": {"type": "string", "enum": ["summary", "detailed"], "default": "summary"}
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

    def _save_keywords(self):
        with open(self.keywords_file, 'w') as f: json.dump(self.monitored_keywords, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def monitor_keywords(self, keywords: List[str], platform: str = "twitter") -> Dict[str, Any]:
        """Simulates monitoring social media for specific keywords."""
        results = []
        for kw in keywords:
            mentions = random.randint(10, 100)  # nosec B311
            sentiment = random.choice(["positive", "negative", "neutral"])  # nosec B311
            
            if kw not in self.monitored_keywords: self.monitored_keywords[kw] = {}
            self.monitored_keywords[kw][platform] = {"mentions": mentions, "sentiment": sentiment, "monitored_at": datetime.now().isoformat()}
            results.append({"keyword": kw, "platform": platform, "mentions": mentions, "sentiment": sentiment})
        
        self._save_keywords()
        return {"status": "success", "message": "Keywords monitored.", "results": results}

    def analyze_sentiment(self, mentions: List[str]) -> Dict[str, Any]:
        """Simulates analyzing the sentiment of social media mentions."""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for _ in mentions:
            sentiment = random.choice(["positive", "negative", "neutral"])  # nosec B311
            if sentiment == "positive": positive_count += 1
            elif sentiment == "negative": negative_count += 1
            else: neutral_count += 1
        
        return {"status": "success", "total_mentions": len(mentions), "positive": positive_count, "negative": negative_count, "neutral": neutral_count}

    def identify_influencers(self, topic: str, platform: str = "twitter") -> List[Dict[str, Any]]:
        """Simulates identifying key influencers related to a topic."""
        influencers = []
        for i in range(random.randint(1, 3)):  # nosec B311
            influencers.append({
                "name": f"Influencer_{random.randint(100, 999)}",  # nosec B311
                "followers": random.randint(10000, 500000),  # nosec B311
                "platform": platform,
                "relevance_score": round(random.uniform(0.7, 0.95), 2)  # nosec B311
            })
        return influencers

    def generate_report(self, topic: str, platform: str = "twitter", report_type: str = "summary") -> Dict[str, Any]:
        """Generates a social listening report."""
        report_id = f"sl_report_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Simulate data for the report
        total_mentions = random.randint(500, 5000)  # nosec B311
        positive_mentions = random.randint(total_mentions // 4, total_mentions // 2)  # nosec B311
        negative_mentions = random.randint(total_mentions // 10, total_mentions // 4)  # nosec B311
        neutral_mentions = total_mentions - positive_mentions - negative_mentions
        
        top_keywords = [{"keyword": "product_x", "mentions": 150}, {"keyword": "customer_service", "mentions": 80}]
        top_influencers = self.identify_influencers(topic, platform)
        
        report = {
            "id": report_id, "topic": topic, "platform": platform, "report_type": report_type,
            "total_mentions": total_mentions,
            "sentiment_breakdown": {"positive": positive_mentions, "negative": negative_mentions, "neutral": neutral_mentions},
            "top_keywords": top_keywords,
            "top_influencers": top_influencers,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "monitor_keywords":
            keywords = kwargs.get('keywords')
            if not keywords:
                raise ValueError("Missing 'keywords' for 'monitor_keywords' operation.")
            return self.monitor_keywords(keywords, kwargs.get('platform', 'twitter'))
        elif operation == "analyze_sentiment":
            mentions = kwargs.get('mentions')
            if not mentions:
                raise ValueError("Missing 'mentions' for 'analyze_sentiment' operation.")
            return self.analyze_sentiment(mentions)
        elif operation == "identify_influencers":
            topic = kwargs.get('topic')
            if not topic:
                raise ValueError("Missing 'topic' for 'identify_influencers' operation.")
            return self.identify_influencers(topic, kwargs.get('platform', 'twitter'))
        elif operation == "generate_report":
            topic = kwargs.get('topic')
            if not topic:
                raise ValueError("Missing 'topic' for 'generate_report' operation.")
            return self.generate_report(topic, kwargs.get('platform', 'twitter'), kwargs.get('report_type', 'summary'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SocialListeningSimulatorTool functionality...")
    temp_dir = "temp_social_listening_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sl_tool = SocialListeningSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Monitor keywords
        print("\n--- Monitoring keywords ['product_launch', 'customer_service'] ---")
        monitor_result = sl_tool.execute(operation="monitor_keywords", keywords=["product_launch", "customer_service"], platform="twitter")
        print(json.dumps(monitor_result, indent=2))

        # 2. Analyze sentiment of simulated mentions
        print("\n--- Analyzing sentiment of simulated mentions ---")
        simulated_mentions = ["great product", "terrible support", "neutral comment", "love it", "hate it"]
        sentiment_analysis = sl_tool.execute(operation="analyze_sentiment", mentions=simulated_mentions)
        print(json.dumps(sentiment_analysis, indent=2))

        # 3. Identify influencers
        print("\n--- Identifying influencers for 'AI' on 'twitter' ---")
        influencers = sl_tool.execute(operation="identify_influencers", topic="AI", platform="twitter")
        print(json.dumps(influencers, indent=2))

        # 4. Generate a report
        print("\n--- Generating summary report for 'product_launch' on 'twitter' ---")
        report = sl_tool.execute(operation="generate_report", topic="product_launch", platform="twitter", report_type="summary")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")