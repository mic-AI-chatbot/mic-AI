import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

# Define sales stages and their associated probabilities
SALES_STAGES = {
    "prospecting": 0.10,
    "qualification": 0.25,
    "needs_analysis": 0.40,
    "solution_proposal": 0.60,
    "negotiation": 0.80,
    "closed_won": 1.00,
    "closed_lost": 0.00
}

class OpportunityTrackingTool(BaseTool):
    """
    A tool for tracking sales opportunities, allowing for creation, stage updates,
    and sales forecasting.
    """

    def __init__(self, tool_name: str = "OpportunityTracker", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.opportunities_file = os.path.join(self.data_dir, "sales_opportunities.json")
        # Opportunities structure: {opportunity_id: {name: ..., account: ..., stage: ..., value: ..., close_date: ..., probability: ...}}
        self.opportunities: Dict[str, Dict[str, Any]] = self._load_data(self.opportunities_file, default={})

    @property
    def description(self) -> str:
        return "Tracks sales opportunities: create, update stages, and generate forecasts."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_opportunity", "update_stage", "get_forecast", "list_opportunities"]},
                "opportunity_id": {"type": "string"},
                "name": {"type": "string"},
                "account": {"type": "string"},
                "value": {"type": "number", "minimum": 0},
                "close_date": {"type": "string", "description": "YYYY-MM-DD"},
                "stage": {"type": "string", "enum": list(SALES_STAGES.keys())},
                "filter_stage": {"type": "string", "enum": list(SALES_STAGES.keys()), "description": "Filter opportunities by stage."}
            },
            "required": ["operation", "opportunity_id"]
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
        with open(self.opportunities_file, 'w') as f: json.dump(self.opportunities, f, indent=2)

    def create_opportunity(self, opportunity_id: str, name: str, account: str, value: float, close_date: str, stage: str = "prospecting") -> Dict[str, Any]:
        """Creates a new sales opportunity."""
        if opportunity_id in self.opportunities: raise ValueError(f"Opportunity '{opportunity_id}' already exists.")
        if stage not in SALES_STAGES: raise ValueError(f"Invalid stage: {stage}.")

        new_opportunity = {
            "id": opportunity_id, "name": name, "account": account, "value": value,
            "close_date": close_date, "stage": stage, "probability": SALES_STAGES[stage],
            "created_at": datetime.now().isoformat()
        }
        self.opportunities[opportunity_id] = new_opportunity
        self._save_data()
        return new_opportunity

    def update_stage(self, opportunity_id: str, new_stage: str) -> Dict[str, Any]:
        """Updates the stage of an existing opportunity."""
        opportunity = self.opportunities.get(opportunity_id)
        if not opportunity: raise ValueError(f"Opportunity '{opportunity_id}' not found.")
        if new_stage not in SALES_STAGES: raise ValueError(f"Invalid stage: {new_stage}.")

        opportunity["stage"] = new_stage
        opportunity["probability"] = SALES_STAGES[new_stage]
        opportunity["last_updated_at"] = datetime.now().isoformat()
        self._save_data()
        return opportunity

    def get_forecast(self) -> Dict[str, Any]:
        """Calculates a simple sales forecast based on open opportunities."""
        total_forecast_value = 0.0
        open_opportunities = []
        
        for opp in self.opportunities.values():
            if opp["stage"] not in ["closed_won", "closed_lost"]:
                total_forecast_value += opp["value"] * opp["probability"]
                open_opportunities.append(opp)
        
        return {
            "total_forecast_value": round(total_forecast_value, 2),
            "num_open_opportunities": len(open_opportunities),
            "forecast_generated_at": datetime.now().isoformat()
        }

    def list_opportunities(self, filter_stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all sales opportunities, optionally filtered by stage."""
        filtered_list = list(self.opportunities.values())
        if filter_stage:
            filtered_list = [opp for opp in filtered_list if opp["stage"] == filter_stage]
        return filtered_list

    def execute(self, **kwargs: Any) -> Any:
        operation = kwargs.pop("operation")
        if not operation: raise ValueError("'operation' is required.")
        
        op_map = {
            "create_opportunity": self.create_opportunity,
            "update_stage": self.update_stage,
            "get_forecast": self.get_forecast,
            "list_opportunities": self.list_opportunities
        }
        if operation not in op_map: raise ValueError(f"Unsupported operation: {operation}")
        
        return op_map[operation](**kwargs)

if __name__ == '__main__':
    print("Demonstrating OpportunityTrackingTool functionality...")
    temp_dir = "temp_opportunity_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    tracker_tool = OpportunityTrackingTool(data_dir=temp_dir)
    
    try:
        # 1. Create a few opportunities
        print("\n--- Creating opportunities ---")
        tracker_tool.execute(operation="create_opportunity", opportunity_id="opp_001", name="Enterprise Software Deal", account="Acme Corp", value=100000.0, close_date="2025-12-31", stage="prospecting")
        tracker_tool.execute(operation="create_opportunity", opportunity_id="opp_002", name="Cloud Migration Project", account="Globex Inc.", value=250000.0, close_date="2026-03-15", stage="needs_analysis")
        tracker_tool.execute(operation="create_opportunity", opportunity_id="opp_003", name="Small Business License", account="SmallBiz LLC", value=15000.0, close_date="2025-11-30", stage="negotiation")
        print("Opportunities created.")

        # 2. Update the stage of an opportunity
        print("\n--- Updating stage of 'opp_001' to 'solution_proposal' ---")
        tracker_tool.execute(operation="update_stage", opportunity_id="opp_001", new_stage="solution_proposal")
        print("Stage updated.")

        # 3. Get a sales forecast
        print("\n--- Getting sales forecast ---")
        forecast = tracker_tool.execute(operation="get_forecast", opportunity_id="any") # opportunity_id is not used for get_forecast
        print(json.dumps(forecast, indent=2))

        # 4. List opportunities filtered by stage
        print("\n--- Listing opportunities in 'negotiation' stage ---")
        negotiation_opps = tracker_tool.execute(operation="list_opportunities", opportunity_id="any", filter_stage="negotiation")
        print(json.dumps(negotiation_opps, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")