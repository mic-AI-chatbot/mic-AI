import logging
import json
import random
from typing import Dict, Any

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# A simple "database" of crop information
CROP_DATABASE = {
    "corn": {"optimal_temp_c": 25, "optimal_rainfall_mm": 600, "optimal_ph": 6.5, "base_yield": 4.0},
    "wheat": {"optimal_temp_c": 20, "optimal_rainfall_mm": 500, "optimal_ph": 6.0, "base_yield": 3.5},
    "soybeans": {"optimal_temp_c": 28, "optimal_rainfall_mm": 700, "optimal_ph": 6.8, "base_yield": 3.0},
}

class YieldPredictor:
    """A class to simulate agricultural yield prediction."""
    def predict(self, crop_type: str, weather: Dict[str, Any], soil: Dict[str, Any]) -> float:
        if crop_type not in CROP_DATABASE:
            return 0.0

        crop_info = CROP_DATABASE[crop_type]
        predicted_yield = crop_info["base_yield"]

        # Temperature impact (quadratic penalty for deviation from optimal)
        temp_diff = abs(weather.get("avg_temp_c", crop_info["optimal_temp_c"]) - crop_info["optimal_temp_c"])
        predicted_yield *= max(0, 1 - (temp_diff / 15)**2) # Penalty up to 15 degrees diff

        # Rainfall impact
        rainfall_ratio = weather.get("total_rainfall_mm", crop_info["optimal_rainfall_mm"]) / crop_info["optimal_rainfall_mm"]
        predicted_yield *= min(rainfall_ratio, 1.0) # Capped at 1.0, no benefit from excess rain

        # Soil pH impact
        ph_diff = abs(soil.get("ph", crop_info["optimal_ph"]) - crop_info["optimal_ph"])
        predicted_yield *= max(0, 1 - ph_diff) # Linear penalty for pH deviation

        # Nitrogen level impact
        nitrogen_level = soil.get("nitrogen_level", "medium")
        if nitrogen_level == "low":
            predicted_yield *= 0.85
        elif nitrogen_level == "high":
            predicted_yield *= 1.05

        return predicted_yield * random.uniform(0.95, 1.05) # Add slight randomness  # nosec B311

class PredictAgriculturalYieldTool(BaseTool):
    """Tool to predict crop yield using a simulated agronomic model."""
    def __init__(self, tool_name="predict_agricultural_yield"):
        super().__init__(tool_name=tool_name)
        self.predictor = YieldPredictor()

    @property
    def description(self) -> str:
        return "Predicts crop yield based on crop type, weather, and soil conditions using a simulated agronomic model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crop_type": {"type": "string", "description": "The type of crop (e.g., 'corn', 'wheat', 'soybeans')."},
                "weather_forecast": {
                    "type": "object",
                    "description": "Weather forecast data (e.g., {\"avg_temp_c\": 25, \"total_rainfall_mm\": 300})."
                },
                "soil_conditions": {
                    "type": "object",
                    "description": "Current soil conditions (e.g., {\"ph\": 6.5, \"nitrogen_level\": \"medium\"})."
                }
            },
            "required": ["crop_type", "weather_forecast", "soil_conditions"]
        }

    def execute(self, crop_type: str, weather_forecast: Dict[str, Any], soil_conditions: Dict[str, Any], **kwargs: Any) -> str:
        predicted_yield = self.predictor.predict(crop_type, weather_forecast, soil_conditions)
        
        if predicted_yield == 0.0:
            return json.dumps({"error": f"Crop type '{crop_type}' not found in database."}, indent=2)

        report = {
            "crop_type": crop_type,
            "predicted_yield_tons_per_acre": round(predicted_yield, 2),
            "confidence_score": round(random.uniform(0.75, 0.95), 2)  # nosec B311
        }
        return json.dumps(report, indent=2)

class OptimizeFarmingStrategyTool(BaseTool):
    """Tool to suggest an optimized farming strategy based on conditions."""
    def __init__(self, tool_name="optimize_farming_strategy"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests an optimized farming strategy (fertilizer, irrigation, soil treatment) based on crop type and conditions."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "crop_type": {"type": "string", "description": "The type of crop."},
                "weather_forecast": {"type": "object"},
                "soil_conditions": {"type": "object"}
            },
            "required": ["crop_type", "weather_forecast", "soil_conditions"]
        }

    def execute(self, crop_type: str, weather_forecast: Dict[str, Any], soil_conditions: Dict[str, Any], **kwargs: Any) -> str:
        if crop_type not in CROP_DATABASE:
            return json.dumps({"error": f"Crop type '{crop_type}' not found in database."}, indent=2)

        crop_info = CROP_DATABASE[crop_type]
        suggestions = []

        # Irrigation suggestion
        rainfall_needed = crop_info["optimal_rainfall_mm"] - weather_forecast.get("total_rainfall_mm", 0)
        if rainfall_needed > 100:
            suggestions.append(f"Consider an irrigation schedule to supplement the low rainfall forecast. Aim for an additional {rainfall_needed}mm over the season.")

        # Fertilizer suggestion
        if soil_conditions.get("nitrogen_level") == "low":
            suggestions.append("Nitrogen levels are low. Apply a nitrogen-rich fertilizer early in the growing season.")

        # Soil treatment suggestion
        ph_diff = soil_conditions.get("ph", crop_info["optimal_ph"]) - crop_info["optimal_ph"]
        if ph_diff > 0.5:
            suggestions.append(f"Soil pH is too high (alkaline). Consider applying sulfur or acidic fertilizers to lower the pH towards the optimal {crop_info['optimal_ph']}.")
        elif ph_diff < -0.5:
            suggestions.append(f"Soil pH is too low (acidic). Consider applying lime to raise the pH towards the optimal {crop_info['optimal_ph']}.")

        if not suggestions:
            suggestions.append("Current conditions seem optimal. Follow standard best practices for this crop.")

        report = {
            "crop_type": crop_type,
            "suggested_strategies": suggestions
        }
        return json.dumps(report, indent=2)