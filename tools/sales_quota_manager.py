import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SalesQuotaManagerSimulatorTool(BaseTool):
    """
    A tool that simulates sales quota management, allowing for setting quotas,
    tracking performance, and generating reports on sales achievement.
    """

    def __init__(self, tool_name: str = "SalesQuotaManagerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.quotas_file = os.path.join(self.data_dir, "sales_quotas.json")
        self.performance_file = os.path.join(self.data_dir, "sales_performance.json")
        
        # Sales quotas: {sales_rep_id: {period: {target_amount: ...}}}
        self.sales_quotas: Dict[str, Dict[str, Any]] = self._load_data(self.quotas_file, default={})
        # Sales performance: {sales_rep_id: {period: {actual_amount: ...}}}
        self.sales_performance: Dict[str, Dict[str, Any]] = self._load_data(self.performance_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sales quota management: set quotas, track performance, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["set_quota", "track_performance", "generate_report", "list_quotas"]},
                "sales_rep_id": {"type": "string"},
                "period": {"type": "string", "description": "The period for the quota (e.g., 'Q1 2024', 'Monthly Nov 2024')."},
                "target_amount": {"type": "number", "minimum": 0},
                "actual_sales_amount": {"type": "number", "minimum": 0}
            },
            "required": ["operation"] # Only operation is required at top level
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_quotas(self):
        with open(self.quotas_file, 'w') as f: json.dump(self.sales_quotas, f, indent=2)

    def _save_performance(self):
        with open(self.performance_file, 'w') as f: json.dump(self.sales_performance, f, indent=2)

    def set_quota(self, sales_rep_id: str, period: str, target_amount: float) -> Dict[str, Any]:
        """Sets a sales quota for a sales representative for a specific period."""
        if sales_rep_id not in self.sales_quotas: self.sales_quotas[sales_rep_id] = {}
        if period in self.sales_quotas[sales_rep_id]: raise ValueError(f"Quota for '{sales_rep_id}' for period '{period}' already exists.")
        
        self.sales_quotas[sales_rep_id][period] = {"target_amount": target_amount, "set_at": datetime.now().isoformat()}
        self._save_quotas()
        return {"status": "success", "message": f"Quota of ${target_amount:.2f} set for '{sales_rep_id}' for period '{period}'."}

    def track_performance(self, sales_rep_id: str, period: str, actual_sales_amount: float) -> Dict[str, Any]:
        """Tracks actual sales performance against a quota."""
        if sales_rep_id not in self.sales_quotas or period not in self.sales_quotas[sales_rep_id]:
            raise ValueError(f"Quota for '{sales_rep_id}' for period '{period}' not found. Set quota first.")
        
        if sales_rep_id not in self.sales_performance: self.sales_performance[sales_rep_id] = {}
        self.sales_performance[sales_rep_id][period] = {"actual_amount": actual_sales_amount, "tracked_at": datetime.now().isoformat()}
        self._save_performance()
        return {"status": "success", "message": f"Actual sales of ${actual_sales_amount:.2f} tracked for '{sales_rep_id}' for period '{period}'."}

    def generate_report(self, sales_rep_id: str, period: str) -> Dict[str, Any]:
        """Generates a performance report for a sales representative against their quota."""
        quota_info = self.sales_quotas.get(sales_rep_id, {}).get(period)
        performance_info = self.sales_performance.get(sales_rep_id, {}).get(period)
        
        if not quota_info: return {"status": "info", "message": f"No quota found for '{sales_rep_id}' for period '{period}'."}
        if not performance_info: return {"status": "info", "message": f"No performance data found for '{sales_rep_id}' for period '{period}'."}
        
        target = quota_info["target_amount"]
        actual = performance_info["actual_amount"]
        
        achievement_percent = round((actual / target) * 100, 2) if target > 0 else 0
        status = "below"
        if achievement_percent >= 100: status = "exceeded"
        elif achievement_percent >= 90: status = "met"
        
        report_id = f"quota_report_{sales_rep_id}_{period}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "sales_rep_id": sales_rep_id, "period": period,
            "target_amount": target, "actual_sales_amount": actual,
            "achievement_percent": achievement_percent, "status": status,
            "generated_at": datetime.now().isoformat()
        }
        return report

    def list_quotas(self, sales_rep_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lists all set quotas, optionally filtered by sales representative."""
        quotas_list = []
        for rep_id, periods in self.sales_quotas.items():
            if sales_rep_id is None or rep_id == sales_rep_id:
                for period, quota_data in periods.items():
                    quotas_list.append({"sales_rep_id": rep_id, "period": period, "target_amount": quota_data["target_amount"]})
        return quotas_list

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "set_quota":
            sales_rep_id = kwargs.get('sales_rep_id')
            period = kwargs.get('period')
            target_amount = kwargs.get('target_amount')
            if not all([sales_rep_id, period, target_amount is not None]): # target_amount can be 0, so check for not None
                raise ValueError("Missing 'sales_rep_id', 'period', or 'target_amount' for 'set_quota' operation.")
            return self.set_quota(sales_rep_id, period, target_amount)
        elif operation == "track_performance":
            sales_rep_id = kwargs.get('sales_rep_id')
            period = kwargs.get('period')
            actual_sales_amount = kwargs.get('actual_sales_amount')
            if not all([sales_rep_id, period, actual_sales_amount is not None]): # actual_sales_amount can be 0, so check for not None
                raise ValueError("Missing 'sales_rep_id', 'period', or 'actual_sales_amount' for 'track_performance' operation.")
            return self.track_performance(sales_rep_id, period, actual_sales_amount)
        elif operation == "generate_report":
            sales_rep_id = kwargs.get('sales_rep_id')
            period = kwargs.get('period')
            if not all([sales_rep_id, period]):
                raise ValueError("Missing 'sales_rep_id' or 'period' for 'generate_report' operation.")
            return self.generate_report(sales_rep_id, period)
        elif operation == "list_quotas":
            # sales_rep_id is optional, so no strict check needed here
            return self.list_quotas(kwargs.get('sales_rep_id'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SalesQuotaManagerSimulatorTool functionality...")
    temp_dir = "temp_sales_quota_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    quota_manager = SalesQuotaManagerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Set a quota for a sales rep
        print("\n--- Setting quota for 'rep_alice' for 'Q1 2025' ---")
        quota_manager.execute(operation="set_quota", sales_rep_id="rep_alice", period="Q1 2025", target_amount=100000.0)
        print("Quota set.")

        # 2. Track performance
        print("\n--- Tracking performance for 'rep_alice' for 'Q1 2025' ---")
        quota_manager.execute(operation="track_performance", sales_rep_id="rep_alice", period="Q1 2025", actual_sales_amount=95000.0)
        print("Performance tracked.")

        # 3. Generate report
        print("\n--- Generating report for 'rep_alice' for 'Q1 2025' ---")
        report = quota_manager.execute(operation="generate_report", sales_rep_id="rep_alice", period="Q1 2025")
        print(json.dumps(report, indent=2))

        # 4. Set another quota and track performance (exceeded)
        print("\n--- Setting quota for 'rep_bob' for 'Q1 2025' ---")
        quota_manager.execute(operation="set_quota", sales_rep_id="rep_bob", period="Q1 2025", target_amount=50000.0)
        quota_manager.execute(operation="track_performance", sales_rep_id="rep_bob", period="Q1 2025", actual_sales_amount=55000.0)
        print("\n--- Generating report for 'rep_bob' for 'Q1 2025' ---")
        report_bob = quota_manager.execute(operation="generate_report", sales_rep_id="rep_bob", period="Q1 2025")
        print(json.dumps(report_bob, indent=2))

        # 5. List all quotas
        print("\n--- Listing all quotas ---")
        all_quotas = quota_manager.execute(operation="list_quotas", sales_rep_id="any") # sales_rep_id is not used for list_quotas
        print(json.dumps(all_quotas, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")