import logging
import json
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ClimateModel:
    """Manages the state of the simulated climate and updates it based on interventions."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClimateModel, cls).__new__(cls)
            cls._instance.temperature_change_c = 0.0 # Relative to pre-industrial levels
            cls._instance.sea_level_change_m = 0.0   # Relative to pre-industrial levels
            cls._instance.carbon_dioxide_concentration_ppm = 420.0 # Current baseline (e.g., 2024 levels)
        return cls._instance

    def apply_srm(self, reduction_percentage: float, duration_years: int):
        """Simulates Solar Radiation Management (SRM) effects over time."""
        for _ in range(duration_years):
            # Simulate impact per year, with some variability
            temp_effect_per_year = -2.0 * reduction_percentage * random.uniform(0.8, 1.2)  # nosec B311
            sea_level_effect_per_year = -0.5 * reduction_percentage * random.uniform(0.8, 1.2)  # nosec B311
            self.temperature_change_c += temp_effect_per_year
            self.sea_level_change_m += sea_level_effect_per_year

    def apply_ccm(self, carbon_removed_gigatons: float, duration_years: int):
        """Simulates Carbon Cycle Modification (CCM) effects over time."""
        for _ in range(duration_years):
            # 1 GtC is roughly 0.47 ppm CO2
            co2_reduction_ppm_per_year = carbon_removed_gigatons * 0.47 * random.uniform(0.9, 1.1)  # nosec B311
            self.carbon_dioxide_concentration_ppm -= co2_reduction_ppm_per_year
            # Simple feedback: lower CO2 also slightly reduces temperature
            self.temperature_change_c -= (co2_reduction_ppm_per_year / 100) * random.uniform(0.1, 0.3)  # nosec B311

    def to_dict(self) -> Dict[str, Any]:
        return {
            "temperature_change_c": round(self.temperature_change_c, 2),
            "sea_level_change_m": round(self.sea_level_change_m, 2),
            "carbon_dioxide_concentration_ppm": round(self.carbon_dioxide_concentration_ppm, 2)
        }

climate_model_instance = ClimateModel()

class SimulateSolarRadiationManagementTool(BaseTool):
    """Simulates the effect of reducing solar radiation on global climate."""
    def __init__(self, tool_name="simulate_solar_radiation_management"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the effect of reducing solar radiation on global temperature and sea levels over a specified duration."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "reduction_percentage": {"type": "number", "description": "The percentage of solar radiation to reduce (e.g., 0.01 for 1%, max 0.1 for 10%)."},
                "duration_years": {"type": "integer", "description": "The number of years to simulate the intervention.", "default": 10}
            },
            "required": ["reduction_percentage"]
        }

    def execute(self, reduction_percentage: float, duration_years: int = 10, **kwargs: Any) -> str:
        if not (0 <= reduction_percentage <= 0.1):
            return json.dumps({"error": "reduction_percentage must be between 0 and 0.1 (0-10%)."})
        if duration_years <= 0:
            return json.dumps({"error": "duration_years must be a positive integer."})
            
        initial_state = climate_model_instance.to_dict()
        climate_model_instance.apply_srm(reduction_percentage, duration_years)
        final_state = climate_model_instance.to_dict()
        
        report = {
            "intervention": "Solar Radiation Management",
            "reduction_percentage": reduction_percentage,
            "duration_years": duration_years,
            "initial_climate_state": initial_state,
            "final_climate_state": final_state,
            "summary": f"SRM applied for {duration_years} years. Temperature changed from {initial_state['temperature_change_c']}°C to {final_state['temperature_change_c']}°C. Sea level changed from {initial_state['sea_level_change_m']}m to {final_state['sea_level_change_m']}m."
        }
        return json.dumps(report, indent=2)

class SimulateCarbonCycleModificationTool(BaseTool):
    """Simulates the effect of modifying the carbon cycle on atmospheric CO2 and temperature."""
    def __init__(self, tool_name="simulate_carbon_cycle_modification"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the effect of modifying the carbon cycle (e.g., through carbon capture) on atmospheric CO2 concentration and global temperature over a specified duration."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "carbon_removed_gigatons": {"type": "number", "description": "The amount of carbon to remove from the atmosphere in gigatons (Gt) per year."},
                "duration_years": {"type": "integer", "description": "The number of years to simulate the intervention.", "default": 10}
            },
            "required": ["carbon_removed_gigatons"]
        }

    def execute(self, carbon_removed_gigatons: float, duration_years: int = 10, **kwargs: Any) -> str:
        if carbon_removed_gigatons < 0:
            return json.dumps({"error": "carbon_removed_gigatons must be a non-negative number."})
        if duration_years <= 0:
            return json.dumps({"error": "duration_years must be a positive integer."})

        initial_state = climate_model_instance.to_dict()
        climate_model_instance.apply_ccm(carbon_removed_gigatons, duration_years)
        final_state = climate_model_instance.to_dict()
        
        report = {
            "intervention": "Carbon Cycle Modification",
            "carbon_removed_gigatons_per_year": carbon_removed_gigatons,
            "duration_years": duration_years,
            "initial_climate_state": initial_state,
            "final_climate_state": final_state,
            "summary": f"CCM applied for {duration_years} years. CO2 changed from {initial_state['carbon_dioxide_concentration_ppm']}ppm to {final_state['carbon_dioxide_concentration_ppm']}ppm. Temperature changed from {initial_state['temperature_change_c']}°C to {final_state['temperature_change_c']}°C."
        }
        return json.dumps(report, indent=2)

class GetClimateStateTool(BaseTool):
    """Retrieves the current state of the simulated global climate."""
    def __init__(self, tool_name="get_climate_state"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Retrieves the current simulated state of the global climate, including temperature change, sea level change, and CO2 concentration."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> str:
        return json.dumps(climate_model_instance.to_dict(), indent=2)