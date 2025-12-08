import logging
import json
import random
import pandas as pd
import numpy as np
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. AI-powered recommendations will not be available.")

logger = logging.getLogger(__name__)

class CloudCostDataGenerator:
    """Generates mock cloud resource usage and cost data for simulation."""
    def generate_cost_data(self, provider: str, time_range: str, num_entries: int = 100) -> pd.DataFrame:
        services = ["EC2", "S3", "RDS", "Lambda", "EBS", "VPC"]
        regions = ["us-east-1", "eu-west-1", "ap-southeast-2"]
        
        data = {
            "service": np.random.choice(services, num_entries),
            "region": np.random.choice(regions, num_entries),
            "usage_hours": np.random.randint(1, 720, num_entries), # Up to a month of hours
            "cost": np.random.normal(loc=10, scale=50, size=num_entries).clip(min=0.1).round(2)
        }
        df = pd.DataFrame(data)
        
        # Introduce some idle resources for optimization opportunities
        idle_instances_count = int(num_entries * 0.1)
        if idle_instances_count > 0:
            idle_indices = np.random.choice(df.index, idle_instances_count, replace=False)
            df.loc[idle_indices, "usage_hours"] = np.random.randint(1, 5, len(idle_indices)) # Very low usage
            df.loc[idle_indices, "cost"] = df.loc[idle_indices, "cost"] * 0.1 # Lower cost
        
        return df

class CloudCostAnalyzer:
    """Analyzes mock cloud cost data to identify cost-saving opportunities."""
    def analyze_costs(self, df: pd.DataFrame) -> Dict[str, Any]:
        total_spend = df["cost"].sum()
        
        # Identify idle resources (e.g., very low usage)
        idle_resources = df[df["usage_hours"] < 10]
        potential_savings_idle = idle_resources["cost"].sum() * random.uniform(0.5, 0.9) # Can save 50-90% of idle cost  # nosec B311
        
        # Identify over-provisioned resources (e.g., high cost, but not necessarily low usage)
        # For simulation, let's say resources with high cost but medium usage are over-provisioned
        over_provisioned_resources = df[(df["cost"] > 100) & (df["usage_hours"] > 100) & (df["usage_hours"] < 500)]
        potential_savings_rightsizing = over_provisioned_resources["cost"].sum() * random.uniform(0.1, 0.3) # Can save 10-30%  # nosec B311
        
        potential_savings = potential_savings_idle + potential_savings_rightsizing
        
        return {
            "total_spend": round(total_spend, 2),
            "potential_savings": round(potential_savings, 2),
            "idle_resources_count": len(idle_resources),
            "over_provisioned_resources_count": len(over_provisioned_resources)
        }

class CloudOptimizerModel:
    """Manages the text generation model for cloud optimization recommendations, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CloudOptimizerModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for cloud optimization are not installed. Please install 'transformers' and 'torch'.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for cloud optimization...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_response(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            generated = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)[0]['generated_text']
            # Clean up the output from the model, removing the prompt
            return generated.replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

cloud_optimizer_model_instance = CloudOptimizerModel()
cloud_cost_data_generator = CloudCostDataGenerator()
cloud_cost_analyzer = CloudCostAnalyzer()

class AnalyzeCloudCostsTool(BaseTool):
    """Analyzes simulated cloud spending and identifies cost-saving opportunities."""
    def __init__(self, tool_name="analyze_cloud_costs"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes simulated cloud spending for a specified provider and time range, identifying total spend and potential savings."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "description": "The cloud provider.", "enum": ["aws", "azure", "gcp"], "default": "aws"},
                "time_range": {"type": "string", "description": "The time range for cost analysis.", "enum": ["monthly", "quarterly", "yearly"], "default": "monthly"},
                "num_cost_entries": {"type": "integer", "description": "Number of mock cost entries to generate for analysis.", "default": 100}
            },
            "required": []
        }

    def execute(self, provider: str = "aws", time_range: str = "monthly", num_cost_entries: int = 100, **kwargs: Any) -> str:
        df = cloud_cost_data_generator.generate_cost_data(provider, time_range, num_cost_entries)
        analysis_results = cloud_cost_analyzer.analyze_costs(df)
        
        report = {
            "provider": provider,
            "time_range": time_range,
            "total_spend": analysis_results["total_spend"],
            "potential_savings": analysis_results["potential_savings"],
            "details": f"Identified {analysis_results['idle_resources_count']} idle resources and {analysis_results['over_provisioned_resources_count']} over-provisioned resources."
        }
        return json.dumps(report, indent=2)

class RecommendCloudOptimizationsTool(BaseTool):
    """Recommends cloud optimization strategies based on cost analysis results using an AI model."""
    def __init__(self, tool_name="recommend_cloud_optimizations"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Recommends specific cloud optimization strategies (e.g., rightsizing, reserved instances, spot instances) based on cost analysis results using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "cost_analysis_report_json": {
                    "type": "string",
                    "description": "The JSON cost analysis report from the AnalyzeCloudCostsTool."
                },
                "optimization_focus": {"type": "string", "description": "The primary focus for optimization.", "enum": ["compute", "storage", "network", "database"], "default": "compute"}
            },
            "required": ["cost_analysis_report_json"]
        }

    def execute(self, cost_analysis_report_json: str, optimization_focus: str = "compute", **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "This tool requires 'transformers' library to be installed."})

        try:
            cost_analysis_report = json.loads(cost_analysis_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for cost_analysis_report_json."})

        prompt = f"Based on the following cloud cost analysis report: {json.dumps(cost_analysis_report)}, and focusing on '{optimization_focus}' optimization, provide specific and actionable recommendations for cost savings. Recommendations:"
        
        generated_recommendations = cloud_optimizer_model_instance.generate_response(prompt, max_length=len(prompt.split()) + 400)
        
        report = {
            "cost_analysis_report": cost_analysis_report,
            "optimization_focus": optimization_focus,
            "recommendations": generated_recommendations
        }
        return json.dumps(report, indent=2)