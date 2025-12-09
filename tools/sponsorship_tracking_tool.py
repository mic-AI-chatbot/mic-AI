import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SponsorshipTrackingSimulatorTool(BaseTool):
    """
    A tool that simulates sponsorship tracking, allowing for creating deals,
    tracking performance metrics, and generating reports on sponsorship value.
    """

    def __init__(self, tool_name: str = "SponsorshipTrackingSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.deals_file = os.path.join(self.data_dir, "sponsorship_deals.json")
        self.tracking_file = os.path.join(self.data_dir, "sponsorship_tracking_records.json")
        
        # Sponsorship deals: {deal_id: {sponsor_name: ..., event_name: ..., value_usd: ..., start_date: ..., end_date: ...}}
        self.sponsorship_deals: Dict[str, Dict[str, Any]] = self._load_data(self.deals_file, default={})
        # Tracking records: {deal_id: [{timestamp: ..., metrics: {impressions: ..., engagement_rate: ...}}]}
        self.tracking_records: Dict[str, List[Dict[str, Any]]] = self._load_data(self.tracking_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sponsorship tracking: create deals, track performance, and generate reports on value/ROI."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["create_sponsorship_deal", "track_performance", "generate_report", "list_deals"]},
                "deal_id": {"type": "string"},
                "sponsor_name": {"type": "string"},
                "event_name": {"type": "string"},
                "value_usd": {"type": "number", "minimum": 0},
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "metrics": {"type": "object", "description": "e.g., {'impressions': 100000, 'engagement_rate': 0.05}"}
            },
            "required": ["operation"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_deals(self):
        with open(self.deals_file, 'w') as f: json.dump(self.sponsorship_deals, f, indent=2)

    def _save_tracking(self):
        with open(self.tracking_file, 'w') as f: json.dump(self.tracking_records, f, indent=2)

    def create_sponsorship_deal(self, deal_id: str, sponsor_name: str, event_name: str, value_usd: float, start_date: str, end_date: str) -> Dict[str, Any]:
        """Creates a new sponsorship deal record."""
        if deal_id in self.sponsorship_deals: raise ValueError(f"Sponsorship deal '{deal_id}' already exists.")
        
        new_deal = {
            "id": deal_id, "sponsor_name": sponsor_name, "event_name": event_name,
            "value_usd": value_usd, "start_date": start_date, "end_date": end_date,
            "created_at": datetime.now().isoformat()
        }
        self.sponsorship_deals[deal_id] = new_deal
        self._save_deals()
        return new_deal

    def track_performance(self, deal_id: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Tracks performance metrics for a sponsorship deal."""
        if deal_id not in self.sponsorship_deals: raise ValueError(f"Sponsorship deal '{deal_id}' not found. Create it first.")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "metrics": metrics
        }
        self.tracking_records.setdefault(deal_id, []).append(log_entry)
        self._save_tracking()
        return {"status": "success", "message": f"Performance metrics tracked for deal '{deal_id}'."}

    def generate_report(self, deal_id: str) -> Dict[str, Any]:
        """Generates a report summarizing the sponsorship's value and ROI."""
        deal = self.sponsorship_deals.get(deal_id)
        if not deal: raise ValueError(f"Sponsorship deal '{deal_id}' not found.")
        
        performance_history = self.tracking_records.get(deal_id, [])
        
        total_impressions = sum(m.get("impressions", 0) for rec in performance_history for m in [rec["metrics"]])
        avg_engagement_rate = sum(m.get("engagement_rate", 0) for rec in performance_history for m in [rec["metrics"]]) / len(performance_history) if performance_history else 0
        
        # Simulate ROI calculation
        simulated_roi_percent = round((total_impressions / 1000 * 0.01 * avg_engagement_rate * 100) / deal["value_usd"] * 100, 2) if deal["value_usd"] > 0 else 0
        
        report_id = f"spon_report_{deal_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "deal_id": deal_id, "sponsor_name": deal["sponsor_name"],
            "event_name": deal["event_name"], "value_usd": deal["value_usd"],
            "total_impressions": total_impressions, "average_engagement_rate": round(avg_engagement_rate, 4),
            "simulated_roi_percent": simulated_roi_percent,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def list_deals(self) -> List[Dict[str, Any]]:
        """Lists all sponsorship deals."""
        return list(self.sponsorship_deals.values())

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_sponsorship_deal":
            deal_id = kwargs.get('deal_id')
            sponsor_name = kwargs.get('sponsor_name')
            event_name = kwargs.get('event_name')
            value_usd = kwargs.get('value_usd')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            if not all([deal_id, sponsor_name, event_name, value_usd is not None, start_date, end_date]):
                raise ValueError("Missing 'deal_id', 'sponsor_name', 'event_name', 'value_usd', 'start_date', or 'end_date' for 'create_sponsorship_deal' operation.")
            return self.create_sponsorship_deal(deal_id, sponsor_name, event_name, value_usd, start_date, end_date)
        elif operation == "track_performance":
            deal_id = kwargs.get('deal_id')
            metrics = kwargs.get('metrics')
            if not all([deal_id, metrics]):
                raise ValueError("Missing 'deal_id' or 'metrics' for 'track_performance' operation.")
            return self.track_performance(deal_id, metrics)
        elif operation == "generate_report":
            deal_id = kwargs.get('deal_id')
            if not deal_id:
                raise ValueError("Missing 'deal_id' for 'generate_report' operation.")
            return self.generate_report(deal_id)
        elif operation == "list_deals":
            # No additional kwargs required for list_deals
            return self.list_deals()
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SponsorshipTrackingSimulatorTool functionality...")
    temp_dir = "temp_sponsorship_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sponsorship_tool = SponsorshipTrackingSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Create a sponsorship deal
        print("\n--- Creating sponsorship deal 'TechConf2025_Sponsor' ---")
        sponsorship_tool.execute(operation="create_sponsorship_deal", deal_id="TechConf2025_Sponsor", sponsor_name="GlobalTech Inc.", event_name="Annual Tech Conference", value_usd=50000.0, start_date="2025-10-01", end_date="2025-10-03")
        print("Deal created.")

        # 2. Track performance
        print("\n--- Tracking performance for 'TechConf2025_Sponsor' ---")
        sponsorship_tool.execute(operation="track_performance", deal_id="TechConf2025_Sponsor", metrics={"impressions": 150000, "engagement_rate": 0.03})
        sponsorship_tool.execute(operation="track_performance", deal_id="TechConf2025_Sponsor", metrics={"impressions": 200000, "engagement_rate": 0.04})
        print("Performance tracked.")

        # 3. Generate report
        print("\n--- Generating report for 'TechConf2025_Sponsor' ---")
        report = sponsorship_tool.execute(operation="generate_report", deal_id="TechConf2025_Sponsor")
        print(json.dumps(report, indent=2))

        # 4. List all deals
        print("\n--- Listing all deals ---")
        all_deals = sponsorship_tool.execute(operation="list_deals")
        print(json.dumps(all_deals, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")