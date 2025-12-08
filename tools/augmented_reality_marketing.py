import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ARCampaign:
    """Represents an Augmented Reality advertising campaign."""
    def __init__(self, campaign_name: str, product_name: str, target_audience: str, budget: float):
        self.campaign_name = campaign_name
        self.product_name = product_name
        self.target_audience = target_audience
        self.budget = budget
        self.status = "active"
        self.metrics = {"impressions": 0, "engagements": 0, "conversions": 0, "spend": 0.0}

    def simulate_interaction(self, num_users: int):
        """Simulates user interactions and updates metrics based on a number of users."""
        self.metrics["impressions"] += num_users
        
        # Simulate engagement (e.g., 5-20% of impressions)
        engaged_users = int(num_users * random.uniform(0.05, 0.2))  # nosec B311
        self.metrics["engagements"] += engaged_users
        
        # Simulate conversions (e.g., 1-5% of engaged users)
        converted_users = int(engaged_users * random.uniform(0.01, 0.05))  # nosec B311
        self.metrics["conversions"] += converted_users
        
        # Simulate spend (e.g., $0.01 - $0.05 per impression)
        self.metrics["spend"] += num_users * random.uniform(0.01, 0.05)  # nosec B311

    def to_dict(self) -> Dict[str, Any]:
        return {
            "campaign_name": self.campaign_name,
            "product_name": self.product_name,
            "target_audience": self.target_audience,
            "budget": self.budget,
            "status": self.status,
            "metrics": self.metrics
        }

class CampaignManager:
    """Manages all created AR campaigns, using a singleton pattern."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CampaignManager, cls).__new__(cls)
            cls._instance.campaigns: Dict[str, ARCampaign] = {}
        return cls._instance

    def create_campaign(self, campaign_name: str, product_name: str, target_audience: str, budget: float) -> bool:
        if campaign_name in self.campaigns:
            return False
        self.campaigns[campaign_name] = ARCampaign(campaign_name, product_name, target_audience, budget)
        return True

    def get_campaign(self, campaign_name: str) -> ARCampaign:
        return self.campaigns.get(campaign_name)

campaign_manager = CampaignManager()

class CreateARAdCampaignTool(BaseTool):
    """Tool to create a new AR advertising campaign."""
    def __init__(self, tool_name="create_ar_ad_campaign"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Creates a new Augmented Reality (AR) advertising campaign for a product with a specified budget and target audience."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string", "description": "A unique name for the AR ad campaign."},
                "product_name": {"type": "string", "description": "The name of the product being advertised."},
                "target_audience": {"type": "string", "description": "The target audience for the campaign (e.g., 'gamers', 'shoppers', 'tech enthusiasts')."},
                "budget": {"type": "number", "description": "The total budget allocated for the campaign."}
            },
            "required": ["campaign_name", "product_name", "target_audience", "budget"]
        }

    def execute(self, campaign_name: str, product_name: str, target_audience: str, budget: float, **kwargs: Any) -> str:
        if campaign_manager.create_campaign(campaign_name, product_name, target_audience, budget):
            report = {"message": f"AR ad campaign '{campaign_name}' for product '{product_name}' created successfully."}
        else:
            report = {"error": f"An AR ad campaign with the name '{campaign_name}' already exists."}
        return json.dumps(report, indent=2)

class AnalyzeARCampaignPerformanceTool(BaseTool):
    """Analyzes the performance of an AR marketing campaign."""
    def __init__(self, tool_name="analyze_ar_campaign_performance"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates user interactions with an AR campaign and returns key performance metrics like impressions, engagements, and conversions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string", "description": "The name of the AR ad campaign to analyze."},
                "num_simulated_users": {"type": "integer", "description": "The number of simulated users interacting with the campaign.", "default": 1000}
            },
            "required": ["campaign_name"]
        }

    def execute(self, campaign_name: str, num_simulated_users: int = 1000, **kwargs: Any) -> str:
        campaign = campaign_manager.get_campaign(campaign_name)
        if not campaign:
            return json.dumps({"error": f"AR campaign '{campaign_name}' not found."})
        
        campaign.simulate_interaction(num_simulated_users)
        
        metrics = campaign.metrics
        engagement_rate = (metrics["engagements"] / metrics["impressions"]) * 100 if metrics["impressions"] > 0 else 0
        conversion_rate = (metrics["conversions"] / metrics["engagements"]) * 100 if metrics["engagements"] > 0 else 0
        # Simplified ROI calculation: assuming a fixed value per conversion
        roi = ((metrics["conversions"] * 10) - metrics["spend"]) / metrics["spend"] * 100 if metrics["spend"] > 0 else 0

        report = {
            "campaign_name": campaign_name,
            "performance_metrics": {
                "impressions": metrics["impressions"],
                "engagements": metrics["engagements"],
                "conversions": metrics["conversions"],
                "spend": round(metrics["spend"], 2),
                "engagement_rate_percent": round(engagement_rate, 2),
                "conversion_rate_percent": round(conversion_rate, 2),
                "roi_percent": round(roi, 2)
            }
        }
        return json.dumps(report, indent=2)

class OptimizeARCampaignTool(BaseTool):
    """Suggests optimization strategies for an AR marketing campaign."""
    def __init__(self, tool_name="optimize_ar_campaign"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes AR campaign performance metrics and suggests optimization strategies to improve engagement or conversions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"campaign_name": {"type": "string", "description": "The name of the AR campaign to optimize."}},
            "required": ["campaign_name"]
        }

    def execute(self, campaign_name: str, **kwargs: Any) -> str:
        campaign = campaign_manager.get_campaign(campaign_name)
        if not campaign:
            return json.dumps({"error": f"AR campaign '{campaign_name}' not found."})
        
        metrics = campaign.metrics
        suggestions = []

        if metrics["impressions"] == 0:
            suggestions.append("Campaign has no impressions. Ensure the AR experience is discoverable and promoted effectively.")
        elif metrics["engagement_rate_percent"] < 5:
            suggestions.append("Engagement rate is low. Consider refining the AR content to be more interactive, visually appealing, or relevant to the target audience. Experiment with different call-to-actions.")
        
        if metrics["engagements"] > 0 and metrics["conversion_rate_percent"] < 1:
            suggestions.append("Conversion rate is low despite engagement. Review the user journey after engagement. Is the path to purchase clear? Are there any friction points? Is the value proposition strong enough?")
        
        if campaign.budget > 0 and metrics["spend"] > campaign.budget * 0.8 and metrics["conversions"] < 10:
            suggestions.append("High spend with low conversions. Re-evaluate target audience and AR experience relevance. Consider pausing the campaign if performance doesn't improve significantly.")
        
        if not suggestions:
            suggestions.append("Campaign performance appears satisfactory. Continue monitoring and consider A/B testing minor variations in content or targeting.")

        return json.dumps({"campaign_name": campaign_name, "optimization_suggestions": suggestions}, indent=2)