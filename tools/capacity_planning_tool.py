import logging
import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DemandForecaster:
    """Generates mock historical demand data and forecasts future demand using a simple linear model."""
    def generate_historical_demand(self, resource_type: str, num_periods: int = 12) -> pd.Series:
        base_demand = random.randint(50, 200)  # nosec B311
        growth_rate = random.uniform(0.01, 0.05)  # nosec B311
        noise = np.random.normal(0, 5, num_periods)
        
        demand = [base_demand * (1 + growth_rate)**i + noise[i] for i in range(num_periods)]
        return pd.Series(demand).round(0)

    def forecast_demand(self, historical_demand: pd.Series, forecast_periods: int = 1) -> List[float]:
        # Simple linear regression for forecasting
        if len(historical_demand) < 2:
            return [historical_demand.iloc[-1]] * forecast_periods if not historical_demand.empty else [0] * forecast_periods
        
        x = np.arange(len(historical_demand))
        y = historical_demand.values
        
        # Fit a linear model (y = slope * x + intercept)
        slope, intercept = np.polyfit(x, y, 1)
        
        forecast = [slope * (len(historical_demand) + i) + intercept for i in range(forecast_periods)]
        return [max(0, round(d, 0)) for d in forecast]

class CapacityAssessor:
    """Manages a mock inventory of resources and assesses capacity and utilization."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CapacityAssessor, cls).__new__(cls)
            cls._instance.resources: Dict[str, Dict[str, Any]] = {
                "servers": {"total": 100, "used": 70, "unit": "servers"},
                "network_bandwidth": {"total": 1000, "used": 600, "unit": "Gbps"},
                "staff": {"total": 50, "used": 40, "unit": "FTEs"}
            }
        return cls._instance

    def get_capacity(self, resource_type: str) -> Dict[str, Any]:
        if resource_type not in self.resources:
            return {"error": f"Resource type '{resource_type}' not managed by this assessor."}
        
        resource = self.resources[resource_type]
        available = resource["total"] - resource["used"]
        utilization = (resource["used"] / resource["total"]) * 100 if resource["total"] > 0 else 0
        
        return {
            "resource_type": resource_type,
            "total_capacity": resource["total"],
            "used_capacity": resource["used"],
            "available_capacity": available,
            "unit": resource["unit"],
            "utilization_percent": round(utilization, 2)
        }

demand_forecaster = DemandForecaster()
capacity_assessor = CapacityAssessor()

class ForecastDemandTool(BaseTool):
    """Forecasts future resource demand using simulated historical data."""
    def __init__(self, tool_name="forecast_demand"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Forecasts future demand for a specified resource type over a given period using simulated historical data and a simple forecasting model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "The type of resource to forecast demand for.", "enum": ["servers", "network_bandwidth", "staff"]},
                "num_historical_periods": {"type": "integer", "description": "Number of historical periods to generate data for.", "default": 12},
                "num_forecast_periods": {"type": "integer", "description": "Number of future periods to forecast demand for.", "default": 1}
            },
            "required": ["resource_type"]
        }

    def execute(self, resource_type: str, num_historical_periods: int = 12, num_forecast_periods: int = 1, **kwargs: Any) -> str:
        historical_demand = demand_forecaster.generate_historical_demand(resource_type, num_historical_periods)
        forecasted_demand = demand_forecaster.forecast_demand(historical_demand, num_forecast_periods)
        
        report = {
            "resource_type": resource_type,
            "historical_periods_count": num_historical_periods,
            "forecast_periods_count": num_forecast_periods,
            "forecasted_demand": forecasted_demand,
            "unit": capacity_assessor.resources.get(resource_type, {}).get("unit", "units"),
            "confidence_level": f"{random.randint(70, 95)}%" # Simulated confidence  # nosec B311
        }
        return json.dumps(report, indent=2)

class AssessCapacityTool(BaseTool):
    """Assesses current resource capacity and utilization."""
    def __init__(self, tool_name="assess_capacity"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Assesses the current capacity and utilization of a specified resource type based on simulated inventory data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"resource_type": {"type": "string", "description": "The type of resource to assess capacity for.", "enum": ["servers", "network_bandwidth", "staff"]}},
            "required": ["resource_type"]
        }

    def execute(self, resource_type: str, **kwargs: Any) -> str:
        capacity_data = capacity_assessor.get_capacity(resource_type)
        if "error" in capacity_data:
            return json.dumps(capacity_data)
        
        status = "sufficient" if capacity_data["utilization_percent"] < 80 else "constrained"
        
        report = {
            "resource_type": resource_type,
            "capacity_data": capacity_data,
            "status": status
        }
        return json.dumps(report, indent=2)

class GenerateCapacityPlanTool(BaseTool):
    """Generates recommendations for capacity adjustments based on demand forecast and current capacity."""
    def __init__(self, tool_name="generate_capacity_plan"):
        super().__init__(tool_name=tool_name)
        self.forecast_tool = ForecastDemandTool()
        self.assess_tool = AssessCapacityTool()

    @property
    def description(self) -> str:
        return "Generates recommendations for capacity adjustments (e.g., 'add X servers', 'hire Y staff') based on forecasted demand and current capacity."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "resource_type": {"type": "string", "description": "The type of resource to generate a plan for.", "enum": ["servers", "network_bandwidth", "staff"]},
                "forecast_periods": {"type": "integer", "description": "Number of future periods to consider for the plan.", "default": 1}
            },
            "required": ["resource_type"]
        }

    def execute(self, resource_type: str, forecast_periods: int = 1, **kwargs: Any) -> str:
        # Get forecast data
        forecast_json = self.forecast_tool.execute(resource_type=resource_type, num_forecast_periods=forecast_periods)
        forecast_data = json.loads(forecast_json)
        
        # Get capacity data
        capacity_json = self.assess_tool.execute(resource_type=resource_type)
        capacity_data = json.loads(capacity_json)

        if "error" in forecast_data or "error" in capacity_data:
            return json.dumps({"error": "Failed to retrieve forecast or capacity data. Check previous tool outputs."})

        # Assuming the first forecast period is the most relevant for immediate planning
        forecasted_demand = forecast_data["forecasted_demand"][0] 
        available_capacity = capacity_data["capacity_data"]["available_capacity"]
        unit = capacity_data["capacity_data"]["unit"]

        recommendations = []
        if forecasted_demand > available_capacity:
            needed = forecasted_demand - available_capacity
            recommendations.append(f"Recommendation: Increase capacity by {needed} {unit} to meet forecasted demand of {forecasted_demand} {unit}.")
        elif capacity_data["capacity_data"]["utilization_percent"] > 85: # High utilization threshold
            recommendations.append(f"Recommendation: Current utilization is high ({capacity_data['capacity_data']['utilization_percent']}%). Consider increasing capacity proactively to avoid future bottlenecks.")
        else:
            recommendations.append("Recommendation: Current capacity is sufficient for forecasted demand. Continue monitoring resource utilization.")
        
        report = {
            "resource_type": resource_type,
            "forecasted_demand": f"{forecasted_demand} {unit}",
            "current_available_capacity": f"{available_capacity} {unit}",
            "recommendations": recommendations
        }
        return json.dumps(report, indent=2)