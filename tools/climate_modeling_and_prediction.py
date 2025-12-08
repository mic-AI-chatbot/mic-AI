import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

# Import ClimateModel from climate_engineering_simulator.py
try:
    from .climate_engineering_simulator import ClimateModel
    CLIMATE_MODEL_AVAILABLE = True
except ImportError:
    CLIMATE_MODEL_AVAILABLE = False
    logging.warning("ClimateModel from climate_engineering_simulator.py not found. Climate modeling will use a separate, simpler model.")

logger = logging.getLogger(__name__)

# If ClimateModel is not available, define a simple one for this file
if not CLIMATE_MODEL_AVAILABLE:
    class ClimateModel:
        """A simplified, local ClimateModel for when the main one is not available."""
        def __init__(self, tool_name):
            self.temperature_change_c = 0.0
            self.sea_level_change_m = 0.0
            self.carbon_dioxide_concentration_ppm = 420.0

        def simulate_emissions_impact(self, emissions_level: str, policy_changes: List[str], years: int):
            temp_effect_per_year = 0.0
            co2_effect_per_year = 0.0

            if emissions_level == "high":
                temp_effect_per_year = random.uniform(0.05, 0.1)  # nosec B311
                co2_effect_per_year = random.uniform(2.0, 4.0)  # nosec B311
            elif emissions_level == "medium":
                temp_effect_per_year = random.uniform(0.02, 0.05)  # nosec B311
                co2_effect_per_year = random.uniform(1.0, 2.0)  # nosec B311
            elif emissions_level == "low":
                temp_effect_per_year = random.uniform(0.005, 0.02)  # nosec B311
                co2_effect_per_year = random.uniform(0.5, 1.0)  # nosec B311
            
            # Apply policy impacts
            for policy in policy_changes:
                if "carbon_tax" in policy.lower():
                    temp_effect_per_year *= 0.95
                    co2_effect_per_year *= 0.9
                elif "renewable_energy_subsidies" in policy.lower():
                    temp_effect_per_year *= 0.9
                    co2_effect_per_year *= 0.85

            self.temperature_change_c += temp_effect_per_year * years
            self.carbon_dioxide_concentration_ppm += co2_effect_per_year * years
            # Simple relation for sea level
            self.sea_level_change_m += (self.temperature_change_c / 3) * random.uniform(0.01, 0.02) * years  # nosec B311

        def to_dict(self) -> Dict[str, Any]:
            return {
                "temperature_change_c": round(self.temperature_change_c, 2),
                "sea_level_change_m": round(self.sea_level_change_m, 2),
                "carbon_dioxide_concentration_ppm": round(self.carbon_dioxide_concentration_ppm, 2)
            }
    
    climate_model_instance = ClimateModel() # Create a new instance if not imported
else:
    # If ClimateModel is available, use its singleton instance
    from .climate_engineering_simulator import climate_model_instance


class SimulateClimateScenarioTool(BaseTool):
    """Simulates a climate scenario based on emissions and policies over time."""
    def __init__(self, tool_name="simulate_climate_scenario"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates a climate scenario based on specified emissions levels and policy changes over a given number of years, predicting outcomes like global temperature increase and sea level rise."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scenario_name": {"type": "string", "description": "A unique name for the climate scenario."},
                "emissions_level": {"type": "string", "description": "The level of greenhouse gas emissions.", "enum": ["high", "medium", "low"]},
                "policy_changes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of policy changes implemented (e.g., ['carbon_tax', 'renewable_energy_subsidies'])."
                },
                "duration_years": {"type": "integer", "description": "The number of years to simulate the intervention.", "default": 50}
            },
            "required": ["scenario_name", "emissions_level", "policy_changes"]
        }

    def execute(self, scenario_name: str, emissions_level: str, policy_changes: List[str], duration_years: int = 50, **kwargs: Any) -> str:
        initial_state = climate_model_instance.to_dict()
        climate_model_instance.simulate_emissions_impact(emissions_level, policy_changes, duration_years)
        final_state = climate_model_instance.to_dict()
        
        report = {
            "scenario_name": scenario_name,
            "emissions_level": emissions_level,
            "policy_changes": policy_changes,
            "duration_years": duration_years,
            "initial_climate_state": initial_state,
            "final_climate_state": final_state,
            "predicted_outcomes": {
                "global_temperature_increase_celsius": round(final_state["temperature_change_c"] - initial_state["temperature_change_c"], 2),
                "sea_level_rise_meters": round(final_state["sea_level_change_m"] - initial_state["sea_level_change_m"], 2),
                "co2_concentration_change_ppm": round(final_state["carbon_dioxide_concentration_ppm"] - initial_state["carbon_dioxide_concentration_ppm"], 2)
            }
        }
        return json.dumps(report, indent=2)

class PredictTemperatureChangeTool(BaseTool):
    """Predicts future temperature changes based on time horizon and emissions pathway."""
    def __init__(self, tool_name="predict_temperature_change"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Predicts future temperature changes for a specific region or globally, based on a given time horizon and emissions pathway."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "region": {"type": "string", "description": "The region for which to predict temperature change (e.g., 'global', 'arctic', 'europe').", "default": "global"},
                "time_horizon_years": {"type": "integer", "description": "The number of years into the future for the prediction."},
                "emissions_pathway": {"type": "string", "description": "The emissions pathway (e.g., 'SSP1-2.6', 'SSP2-4.5', 'SSP5-8.5').", "enum": ["SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5"]}
            },
            "required": ["time_horizon_years", "emissions_pathway"]
        }

    def execute(self, time_horizon_years: int, emissions_pathway: str, region: str = "global", **kwargs: Any) -> str:
        # Simplified model based on IPCC AR6 projections (highly simplified for simulation)
        # These are illustrative values, not actual model outputs, and include some randomness.
        pathway_impact = {
            "SSP1-2.6": {"temp_per_century": 1.5, "sea_level_per_century": 0.3}, # Low emissions, sustainable development
            "SSP2-4.5": {"temp_per_century": 2.7, "sea_level_per_century": 0.5}, # Medium emissions, middle of the road
            "SSP3-7.0": {"temp_per_century": 3.6, "sea_level_per_century": 0.7}, # High emissions, regional rivalry
            "SSP5-8.5": {"temp_per_century": 4.4, "sea_level_per_century": 0.8}  # Very high emissions, fossil-fueled development
        }
        
        impact = pathway_impact.get(emissions_pathway, {"temp_per_century": 2.0, "sea_level_per_century": 0.4})
        
        predicted_temp_increase = (impact["temp_per_century"] / 100) * time_horizon_years * random.uniform(0.9, 1.1)  # nosec B311
        predicted_sea_level_rise = (impact["sea_level_per_century"] / 100) * time_horizon_years * random.uniform(0.9, 1.1)  # nosec B311

        report = {
            "region": region,
            "time_horizon_years": time_horizon_years,
            "emissions_pathway": emissions_pathway,
            "predicted_temperature_increase_celsius": round(predicted_temp_increase, 2),
            "predicted_sea_level_rise_meters": round(predicted_sea_level_rise, 2),
            "confidence": f"{random.randint(70, 95)}%" # Simulated confidence  # nosec B311
        }
        return json.dumps(report, indent=2)