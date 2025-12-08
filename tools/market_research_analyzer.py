

import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np
import shutil

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MarketResearchAnalyzerTool(BaseTool):
    """
    A tool to store and analyze market research data, performing real trend
    analysis using linear regression on time-series data.
    """

    def __init__(self, tool_name: str = "MarketResearchAnalyzer", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "market_research_data.json")
        self.data: Dict[str, List[Dict[str, Any]]] = self._load_data(self.data_file, default={})

    @property
    def description(self) -> str:
        return "Analyzes market research data to identify trends using linear regression."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["add_data_points", "analyze_trends", "list_data_by_topic"]},
                "topic": {"type": "string"},
                "data_points": {"type": "array", "description": "List of dicts, e.g., [{'date': 'YYYY-MM-DD', 'score': 0.7}]"},
                "metric_to_analyze": {"type": "string", "description": "The key in the data points to analyze (e.g., 'score')."}
            },
            "required": ["operation", "topic"]
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
        with open(self.data_file, 'w') as f: json.dump(self.data, f, indent=4)

    def add_data_points(self, topic: str, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Adds new time-series data points for a given market topic."""
        if not topic or not data_points:
            raise ValueError("Topic and data points are required.")
        
        if topic not in self.data:
            self.data[topic] = []
        
        self.data[topic].extend(data_points)
        self._save_data()
        return {"status": "success", "added_count": len(data_points), "topic": topic}

    def analyze_trends(self, topic: str, metric_to_analyze: str) -> Dict[str, Any]:
        """Analyzes trends in the data for a topic using linear regression."""
        if topic not in self.data:
            raise ValueError(f"No data found for topic '{topic}'.")
        
        topic_data = self.data[topic]
        
        dates = [datetime.fromisoformat(p['date']) for p in topic_data if 'date' in p and metric_to_analyze in p]
        values = [p[metric_to_analyze] for p in topic_data if 'date' in p and metric_to_analyze in p]

        if len(values) < 2:
            return {"status": "not_enough_data", "message": "At least 2 data points are needed for trend analysis."}

        # Convert dates to numerical values (days since first date) for regression
        x = np.array([(d - dates[0]).days for d in dates])
        y = np.array(values)

        # Perform linear regression
        A = np.vstack([x, np.ones(len(x))]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]

        if slope > 0.05: trend = "upward"
        elif slope < -0.05: trend = "downward"
        else: trend = "stable"

        report = {
            "topic": topic,
            "metric": metric_to_analyze,
            "trend": trend,
            "analysis": {
                "data_points_analyzed": len(x),
                "regression_slope": round(slope, 4),
                "min_value": np.min(y),
                "max_value": np.max(y),
                "avg_value": np.mean(y)
            }
        }
        return report

    def list_data_by_topic(self, topic: str) -> List[Dict[str, Any]]:
        """Lists all data points for a specific topic."""
        return self.data.get(topic, [])

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "add_data_points": self.add_data_points,
            "analyze_trends": self.analyze_trends,
            "list_data_by_topic": self.list_data_by_topic
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating MarketResearchAnalyzerTool functionality...")
    temp_dir = "temp_market_research_data"
    if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = MarketResearchAnalyzerTool(data_dir=temp_dir)
    
    try:
        # 1. Add some structured data
        print("\n--- Adding market data for 'AI Adoption' ---")
        market_data = [
            {'date': '2023-01-01', 'adoption_rate': 15.0},
            {'date': '2023-04-01', 'adoption_rate': 18.5},
            {'date': '2023-07-01', 'adoption_rate': 22.0},
            {'date': '2023-10-01', 'adoption_rate': 25.5},
        ]
        analyzer_tool.execute(operation="add_data_points", topic="AI Adoption", data_points=market_data)
        print("Data added.")

        # 2. Analyze the trend in the data
        print("\n--- Analyzing trend for 'adoption_rate' ---")
        trend_report = analyzer_tool.execute(operation="analyze_trends", topic="AI Adoption", metric_to_analyze="adoption_rate")
        print(json.dumps(trend_report, indent=2))

        # 3. Add conflicting data and re-analyze
        print("\n--- Adding new data showing a downturn ---")
        new_data = [{'date': '2024-01-01', 'adoption_rate': 24.0}]
        analyzer_tool.execute(operation="add_data_points", topic="AI Adoption", data_points=new_data)
        
        print("\n--- Re-analyzing trend with new data ---")
        new_trend_report = analyzer_tool.execute(operation="analyze_trends", topic="AI Adoption", metric_to_analyze="adoption_rate")
        print(json.dumps(new_trend_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
