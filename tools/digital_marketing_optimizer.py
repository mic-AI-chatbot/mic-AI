import logging
import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DigitalMarketingOptimizerTool(BaseTool):
    """
    A tool for simulating digital marketing optimization actions.
    """

    def __init__(self, tool_name: str = "digital_marketing_optimizer"):
        super().__init__(tool_name)
        self.campaigns_file = "marketing_campaigns.json"
        self.campaigns: Dict[str, Dict[str, Any]] = self._load_campaigns()

    @property
    def description(self) -> str:
        return "Simulates digital marketing optimization: creates campaigns, optimizes, generates reports, analyzes audiences, and recommends content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The marketing optimization operation to perform.",
                    "enum": ["create_campaign", "optimize_campaign", "get_performance_report", "analyze_audience", "recommend_content", "list_campaigns", "get_campaign_details"]
                },
                "campaign_id": {"type": "string"},
                "campaign_name": {"type": "string"},
                "goal": {"type": "string"},
                "channels": {"type": "array", "items": {"type": "string"}},
                "budget": {"type": "number"},
                "description": {"type": "string"},
                "optimization_goal": {"type": "string"},
                "time_range": {"type": "string"},
                "audience_segment": {"type": "string"},
                "content_type": {"type": "string"}
            },
            "required": ["operation"]
        }

    def _load_campaigns(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.campaigns_file):
            with open(self.campaigns_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted campaigns file '{self.campaigns_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_campaigns(self) -> None:
        with open(self.campaigns_file, 'w') as f:
            json.dump(self.campaigns, f, indent=4)

    def _create_campaign(self, campaign_id: str, campaign_name: str, goal: str, channels: List[str], budget: float, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([campaign_id, campaign_name, goal, channels, budget]):
            raise ValueError("Campaign ID, name, goal, channels, and budget cannot be empty.")
        if campaign_id in self.campaigns: raise ValueError(f"Campaign '{campaign_id}' already exists.")

        new_campaign = {
            "campaign_id": campaign_id, "campaign_name": campaign_name, "description": description,
            "goal": goal, "channels": channels, "budget": budget, "status": "active",
            "created_at": datetime.now().isoformat(), "performance_metrics": []
        }
        self.campaigns[campaign_id] = new_campaign
        self._save_campaigns()
        return new_campaign

    def _optimize_campaign(self, campaign_id: str, optimization_goal: str) -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign: raise ValueError(f"Campaign '{campaign_id}' not found.")
        if campaign["status"] != "active": raise ValueError(f"Campaign '{campaign_id}' is not active, cannot optimize.")

        improvement_percent = round(random.uniform(0.05, 0.20), 2)  # nosec B311
        optimization_result = {
            "campaign_id": campaign_id, "optimization_goal": optimization_goal,
            "simulated_improvement_percent": improvement_percent * 100,
            "message": f"Simulated optimization for '{campaign_id}' resulted in a {improvement_percent*100:.2f}% improvement in {optimization_goal}.",
            "optimized_at": datetime.now().isoformat()
        }
        return optimization_result

    def _get_performance_report(self, campaign_id: str, time_range: str = "last_30_days") -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign: raise ValueError(f"Campaign '{campaign_id}' not found.")
        
        impressions = random.randint(10000, 100000)  # nosec B311
        clicks = random.randint(100, 1000)  # nosec B311
        conversions = random.randint(10, 100)  # nosec B311
        
        report = {
            "campaign_id": campaign_id, "campaign_name": campaign["campaign_name"], "time_range": time_range,
            "impressions": impressions, "clicks": clicks, "conversions": conversions,
            "ctr": round((clicks / impressions) * 100, 2) if impressions > 0 else 0,
            "cvr": round((conversions / clicks) * 100, 2) if clicks > 0 else 0,
            "generated_at": datetime.now().isoformat()
        }
        campaign["performance_metrics"].append(report)
        self._save_campaigns()
        return report

    def _analyze_audience(self, campaign_id: str, audience_segment: str) -> Dict[str, Any]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign: raise ValueError(f"Campaign '{campaign_id}' not found.")
        
        demographics = {"age_range": random.choice(["18-24", "25-34", "35-44"]), "gender": random.choice(["male", "female", "other"])}  # nosec B311
        interests = random.sample(["tech", "travel", "fashion", "sports", "food"], random.randint(1,3))  # nosec B311

        analysis_result = {
            "campaign_id": campaign_id, "audience_segment": audience_segment,
            "simulated_demographics": demographics, "simulated_interests": interests,
            "insights": f"Simulated insights for '{audience_segment}': This segment shows high engagement with {', '.join(interests)}.",
            "analyzed_at": datetime.now().isoformat()
        }
        return analysis_result

    def _recommend_content(self, campaign_id: str, content_type: str) -> List[str]:
        campaign = self.campaigns.get(campaign_id)
        if not campaign: raise ValueError(f"Campaign '{campaign_id}' not found.")
        
        recommendations = [
            f"Simulated {content_type} idea 1 for '{campaign_id}': Focus on {campaign['goal']} with a strong CTA.",
            f"Simulated {content_type} idea 2 for '{campaign_id}': Highlight benefits relevant to {random.choice(['young_adults', 'tech_enthusiasts'])}."  # nosec B311
        ]
        return recommendations

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_campaign":
            return self._create_campaign(kwargs.get("campaign_id"), kwargs.get("campaign_name"), kwargs.get("goal"), kwargs.get("channels"), kwargs.get("budget"), kwargs.get("description"))
        elif operation == "optimize_campaign":
            return self._optimize_campaign(kwargs.get("campaign_id"), kwargs.get("optimization_goal"))
        elif operation == "get_performance_report":
            return self._get_performance_report(kwargs.get("campaign_id"), kwargs.get("time_range", "last_30_days"))
        elif operation == "analyze_audience":
            return self._analyze_audience(kwargs.get("campaign_id"), kwargs.get("audience_segment"))
        elif operation == "recommend_content":
            return self._recommend_content(kwargs.get("campaign_id"), kwargs.get("content_type"))
        elif operation == "list_campaigns":
            return [{k: v for k, v in campaign.items() if k != "performance_metrics"} for campaign in self.campaigns.values()]
        elif operation == "get_campaign_details":
            return self.campaigns.get(kwargs.get("campaign_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DigitalMarketingOptimizerTool functionality...")
    tool = DigitalMarketingOptimizerTool()
    
    try:
        print("\n--- Creating Campaign ---")
        tool.execute(operation="create_campaign", campaign_id="summer_sale", campaign_name="Summer Sale 2024", goal="conversions", channels=["email"], budget=5000.0)
        
        print("\n--- Optimizing Campaign ---")
        optimization_result = tool.execute(operation="optimize_campaign", campaign_id="summer_sale", optimization_goal="conversions")
        print(json.dumps(optimization_result, indent=2))

        print("\n--- Getting Performance Report ---")
        report = tool.execute(operation="get_performance_report", campaign_id="summer_sale", time_range="last_7_days")
        print(json.dumps(report, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.campaigns_file): os.remove(tool.campaigns_file)
        print("\nCleanup complete.")
