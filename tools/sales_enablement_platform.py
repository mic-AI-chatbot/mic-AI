import logging
import os
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SalesEnablementSimulatorTool(BaseTool):
    """
    A tool that simulates a sales enablement platform, allowing for tracking
    sales activities, recommending content, and analyzing sales performance.
    """

    def __init__(self, tool_name: str = "SalesEnablementSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.activities_file = os.path.join(self.data_dir, "sales_activities.json")
        self.reports_file = os.path.join(self.data_dir, "sales_performance_reports.json")
        
        # Sales activities: {sales_rep_id: [{type: ..., details: ..., timestamp: ...}]}
        self.sales_activities: Dict[str, List[Dict[str, Any]]] = self._load_data(self.activities_file, default={})
        # Sales performance reports: {report_id: {sales_rep_id: ..., total_sales: ..., conversion_rate: ...}}
        self.sales_performance_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates sales enablement: track activities, recommend content, analyze performance, generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["track_sales_activity", "get_content_recommendations", "analyze_sales_performance", "generate_sales_report"]},
                "sales_rep_id": {"type": "string"},
                "activity_type": {"type": "string", "enum": ["call", "email", "meeting", "demo"]},
                "details": {"type": "object", "description": "Details of the activity (e.g., {'lead_id': 'L1', 'outcome': 'positive'})."},
                "content_type": {"type": "string", "enum": ["presentation", "case_study", "brochure"]},
                "context": {"type": "object", "description": "Context for recommendations (e.g., {'lead_stage': 'discovery'})."},
                "time_range": {"type": "string", "enum": ["daily", "weekly", "monthly"], "default": "monthly"}
            },
            "required": ["operation", "sales_rep_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_activities(self):
        with open(self.activities_file, 'w') as f: json.dump(self.sales_activities, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.sales_performance_reports, f, indent=2)

    def track_sales_activity(self, sales_rep_id: str, activity_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Tracks a sales activity for a sales representative."""
        self.sales_activities.setdefault(sales_rep_id, []).append({
            "type": activity_type, "details": details, "timestamp": datetime.now().isoformat()
        })
        self._save_activities()
        return {"status": "success", "message": f"Sales activity '{activity_type}' tracked for '{sales_rep_id}'."}

    def get_content_recommendations(self, sales_rep_id: str, content_type: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Simulates recommending sales content to a sales representative."""
        recommendations = []
        
        if content_type == "presentation":
            if context and context.get("lead_stage") == "discovery":
                recommendations.append("Introductory Product Overview Presentation")
            else:
                recommendations.append("General Company Profile Presentation")
        elif content_type == "case_study":
            if context and context.get("industry") == "healthcare":
                recommendations.append("Healthcare Industry Case Study")
            else:
                recommendations.append("General Customer Success Story")
        elif content_type == "brochure":
            recommendations.append("Product Feature Brochure")
        
        return recommendations

    def analyze_sales_performance(self, sales_rep_id: str, time_range: str = "monthly") -> Dict[str, Any]:
        """Simulates analyzing sales performance metrics for a sales representative."""
        activities = self.sales_activities.get(sales_rep_id, [])
        
        total_calls = sum(1 for act in activities if act["type"] == "call")
        total_emails = sum(1 for act in activities if act["type"] == "email")
        total_meetings = sum(1 for act in activities if act["type"] == "meeting")
        
        # Simulate sales and conversion
        total_sales = round(random.uniform(5000, 50000), 2)  # nosec B311
        conversion_rate = round(random.uniform(0.05, 0.2), 2)  # nosec B311
        
        report_id = f"perf_report_{sales_rep_id}_{time_range}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "sales_rep_id": sales_rep_id, "time_range": time_range,
            "total_calls": total_calls, "total_emails": total_emails, "total_meetings": total_meetings,
            "total_sales": total_sales, "conversion_rate": conversion_rate,
            "generated_at": datetime.now().isoformat()
        }
        self.sales_performance_reports[report_id] = report
        self._save_reports()
        return report

    def generate_sales_report(self, sales_rep_id: str, report_type: str = "summary", time_range: str = "monthly") -> Dict[str, Any]:
        """Generates a sales report summarizing performance."""
        performance_data = self.analyze_sales_performance(sales_rep_id, time_range)
        
        report_lines = [
            f"--- Sales Performance Report for: {sales_rep_id} ({time_range}) ---",
            f"Total Sales: ${performance_data['total_sales']:.2f}",
            f"Conversion Rate: {performance_data['conversion_rate']:.2%}",
            f"Calls: {performance_data['total_calls']}",
            f"Emails: {performance_data['total_emails']}",
            f"Meetings: {performance_data['total_meetings']}"
        ]
        
        return {"status": "success", "sales_rep_id": sales_rep_id, "report": "\n".join(report_lines)}

    def execute(self, operation: str, sales_rep_id: str, **kwargs: Any) -> Any:
        if operation == "track_sales_activity":
            activity_type = kwargs.get('activity_type')
            details = kwargs.get('details')
            if not all([activity_type, details]):
                raise ValueError("Missing 'activity_type' or 'details' for 'track_sales_activity' operation.")
            return self.track_sales_activity(sales_rep_id, activity_type, details)
        elif operation == "get_content_recommendations":
            content_type = kwargs.get('content_type')
            if not content_type:
                raise ValueError("Missing 'content_type' for 'get_content_recommendations' operation.")
            return self.get_content_recommendations(sales_rep_id, content_type, kwargs.get('context'))
        elif operation == "analyze_sales_performance":
            # time_range has a default value, so no strict check needed here
            return self.analyze_sales_performance(sales_rep_id, kwargs.get('time_range', 'monthly'))
        elif operation == "generate_sales_report":
            # report_type and time_range have default values, so no strict check needed here
            return self.generate_sales_report(sales_rep_id, kwargs.get('report_type', 'summary'), kwargs.get('time_range', 'monthly'))
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SalesEnablementSimulatorTool functionality...")
    temp_dir = "temp_sales_enablement_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    sales_tool = SalesEnablementSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Track sales activities
        print("\n--- Tracking sales activities for 'sales_rep_alice' ---")
        sales_tool.execute(operation="track_sales_activity", sales_rep_id="sales_rep_alice", activity_type="call", details={"lead_id": "L1", "outcome": "positive"})
        sales_tool.execute(operation="track_sales_activity", sales_rep_id="sales_rep_alice", activity_type="email", details={"lead_id": "L2", "subject": "Follow-up"})
        sales_tool.execute(operation="track_sales_activity", sales_rep_id="sales_rep_alice", activity_type="meeting", details={"lead_id": "L3", "outcome": "demo_scheduled"})
        print("Activities tracked.")

        # 2. Get content recommendations
        print("\n--- Getting content recommendations for 'sales_rep_alice' ---")
        recommendations = sales_tool.execute(operation="get_content_recommendations", sales_rep_id="sales_rep_alice", content_type="presentation", context={"lead_stage": "discovery"})
        print(json.dumps(recommendations, indent=2))

        # 3. Analyze sales performance
        print("\n--- Analyzing sales performance for 'sales_rep_alice' ---")
        performance = sales_tool.execute(operation="analyze_sales_performance", sales_rep_id="sales_rep_alice")
        print(json.dumps(performance, indent=2))

        # 4. Generate sales report
        print("\n--- Generating sales report for 'sales_rep_alice' ---")
        report = sales_tool.execute(operation="generate_sales_report", sales_rep_id="sales_rep_alice")
        print(report["report"])

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")