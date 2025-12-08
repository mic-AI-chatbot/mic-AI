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
    logging.warning("transformers library not found. Natural language insights will not be available.")

logger = logging.getLogger(__name__)

class MockDatasetGenerator:
    """Generates a mock sales dataset with trends."""
    def generate_sales_data(self, num_months: int = 12) -> pd.DataFrame:
        dates = pd.date_range(start="2024-01-01", periods=num_months, freq="MS")
        base_sales = np.linspace(100, 200, num_months) + np.random.normal(0, 10, num_months)
        
        # Add a seasonal trend (e.g., higher sales in summer/winter)
        seasonal_factor = np.sin(np.linspace(0, 2 * np.pi, num_months)) * 20
        sales = base_sales + seasonal_factor
        
        # Add a general upward growth trend
        growth_factor = np.linspace(0, 50, num_months)
        sales += growth_factor
        
        df = pd.DataFrame({"date": dates, "sales": sales.round(2)})
        return df

class AugmentedAnalyticsModel:
    """Manages the text generation model for insights, using a singleton pattern."""
    _generator = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AugmentedAnalyticsModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for natural language insights are not installed.")
                return cls._instance # Return instance without generator
            
            if cls._generator is None:
                try:
                    logger.info("Initializing text generation model (gpt2) for insights...")
                    cls._generator = pipeline("text-generation", model="distilgpt2")
                    logger.info("Text generation model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load text generation model: {e}")
        return cls._instance

    def generate_insights(self, prompt: str, max_length: int) -> str:
        if not self._generator:
            return "Text generation model not available. Check logs for loading errors."
        
        try:
            # The generator returns a list of generated texts. We take the first one.
            # Add pad_token_id to avoid warning when max_length is reached
            response = self._generator(prompt, max_length=max_length, num_return_sequences=1, pad_token_id=self._generator.tokenizer.eos_token_id)
            # Clean up the output from the model, removing the prompt and taking the first line
            generated_text = response[0]['generated_text']
            cleaned_text = generated_text.replace(prompt, "").strip()
            return cleaned_text.split('\n')[0] if cleaned_text else ""
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"Error during text generation: {e}"

analytics_model_instance = AugmentedAnalyticsModel()

class IdentifyDataTrendsTool(BaseTool):
    """Identifies trends in a simulated dataset using statistical methods."""
    def __init__(self, tool_name="identify_data_trends"):
        super().__init__(tool_name=tool_name)
        self.data_generator = MockDatasetGenerator()

    @property
    def description(self) -> str:
        return "Generates a mock sales dataset and identifies key trends (e.g., growth, seasonality) using statistical analysis."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"num_months": {"type": "integer", "description": "The number of months to simulate data for.", "default": 12}},
            "required": []
        }

    def execute(self, num_months: int = 12, **kwargs: Any) -> str:
        df = self.data_generator.generate_sales_data(num_months)
        
        trends = []
        # Simple trend detection: overall growth/decline
        if df["sales"].iloc[-1] > df["sales"].iloc[0] * 1.1: # More than 10% growth
            trends.append("Overall sales show a significant upward trend over the period.")
        elif df["sales"].iloc[-1] < df["sales"].iloc[0] * 0.9: # More than 10% decline
            trends.append("Overall sales show a significant downward trend over the period.")
        else:
            trends.append("Overall sales are relatively stable with minor fluctuations.")

        # Simple seasonality detection: check for significant variance
        if df["sales"].max() - df["sales"].min() > df["sales"].mean() * 0.25: # Max-min range is > 25% of average
            trends.append("Significant seasonal variations are observed in sales, indicating cyclical patterns.")
        
        report = {
            "dataset_summary": {
                "start_date": str(df["date"].min().date()),
                "end_date": str(df["date"].max().date()),
                "total_sales": round(df["sales"].sum(), 2),
                "average_monthly_sales": round(df["sales"].mean(), 2)
            },
            "identified_trends": trends,
            "raw_data_sample": df.head().to_dict(orient="records") # Provide a sample of the raw data
        }
        return json.dumps(report, indent=2)

class GenerateNaturalLanguageInsightsTool(BaseTool):
    """Generates natural language insights from identified data trends using an AI model."""
    def __init__(self, tool_name="generate_natural_language_insights"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates natural language insights and explanations from identified data trends using a text generation AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"trend_report_json": {"type": "string", "description": "The JSON output from the IdentifyDataTrendsTool."}},
            "required": ["trend_report_json"]
        }

    def execute(self, trend_report_json: str, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "Natural language insights tool requires 'transformers' library to be installed."})

        try:
            trend_report = json.loads(trend_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for the trend report."})

        trends = trend_report.get("identified_trends", [])
        if not trends:
            return json.dumps({"message": "No specific trends identified in the report to generate insights from."})

        prompt = f"Based on the following data trends: {'; '.join(trends)}. Provide a concise natural language insight and a potential business implication. Insight:"
        
        insight = analytics_model_instance.generate_insights(prompt, max_length=100)
        
        report = {
            "identified_trends": trends,
            "generated_insight": insight
        }
        return json.dumps(report, indent=2)