import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class PredictiveAnalyticsSimulatorTool(BaseTool):
    """
    A tool that simulates a predictive analytics engine, allowing for ingesting
    historical data, forecasting future trends, and identifying potential risks.
    """

    def __init__(self, tool_name: str = "PredictiveAnalyticsSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "predictive_data.json")
        self.reports_file = os.path.join(self.data_dir, "predictive_reports.json")
        
        # Historical data: {data_id: {target_metric: ..., data_points: [{date: ..., value: ...}]}}
        self.historical_data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={})
        # Analysis reports: {report_id: {data_id: ..., type: ..., results: {}}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates predictive analytics: forecasts trends and identifies risks from historical data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["ingest_historical_data", "forecast_trend", "identify_risk"]},
                "data_id": {"type": "string"},
                "target_metric": {"type": "string"},
                "data_points": {"type": "array", "items": {"type": "object", "properties": {"date": {"type": "string"}, "value": {"type": "number"}}}},
                "forecast_period_days": {"type": "integer", "minimum": 1},
                "risk_threshold": {"type": "number"}
            },
            "required": ["operation", "data_id"]
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
        with open(self.data_file, 'w') as f: json.dump(self.historical_data, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def ingest_historical_data(self, data_id: str, target_metric: str, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests simulated historical data for predictive analysis."""
        if data_id in self.historical_data: raise ValueError(f"Data '{data_id}' already exists.")
        
        # Ensure data points are sorted by date
        data_points.sort(key=lambda x: datetime.fromisoformat(x['date']))

        new_data = {
            "id": data_id, "target_metric": target_metric, "data_points": data_points,
            "ingested_at": datetime.now().isoformat()
        }
        self.historical_data[data_id] = new_data
        self._save_data()
        return new_data

    def forecast_trend(self, data_id: str, forecast_period_days: int) -> Dict[str, Any]:
        """Forecasts future trends using a simple linear regression model."""
        data = self.historical_data.get(data_id)
        if not data: raise ValueError(f"Historical data '{data_id}' not found.")
        
        if len(data["data_points"]) < 2:
            return {"status": "error", "message": "Not enough historical data for forecasting (min 2 points)."}

        # Convert dates to numerical values (days since first date)
        dates = [datetime.fromisoformat(dp['date']) for dp in data["data_points"]]
        values = [dp['value'] for dp in data["data_points"]]

        x = np.array([(d - dates[0]).days for d in dates])
        y = np.array(values)

        # Linear regression: y = mx + c
        m, c = np.polyfit(x, y, 1)

        forecast_start_day = x[-1] + 1
        forecast_end_day = forecast_start_day + forecast_period_days
        
        forecast_days = np.arange(forecast_start_day, forecast_end_day)
        forecast_values = m * forecast_days + c
        
        forecast_results = []
        for i, val in enumerate(forecast_values):
            forecast_date = dates[0] + timedelta(days=int(forecast_days[i]))
            forecast_results.append({"date": forecast_date.strftime("%Y-%m-%d"), "predicted_value": round(val, 2)})

        report_id = f"forecast_{data_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "data_id": data_id, "type": "trend_forecast",
            "forecast_period_days": forecast_period_days, "results": forecast_results,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def identify_risk(self, data_id: str, risk_threshold: float) -> Dict[str, Any]:
        """Identifies potential risks if the target metric exceeds a threshold."""
        data = self.historical_data.get(data_id)
        if not data: raise ValueError(f"Historical data '{data_id}' not found.")
        
        current_value = data["data_points"][-1]["value"]
        risk_identified = current_value > risk_threshold
        
        report_id = f"risk_{data_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "data_id": data_id, "type": "risk_identification",
            "risk_threshold": risk_threshold, "current_value": current_value,
            "risk_identified": risk_identified,
            "message": f"Risk identified: Current value ({current_value}) exceeds threshold ({risk_threshold})." if risk_identified else "No immediate risk identified.",
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def execute(self, operation: str, data_id: str, **kwargs: Any) -> Any:
        if operation == "ingest_historical_data":
            target_metric = kwargs.get('target_metric')
            data_points = kwargs.get('data_points')
            if not all([target_metric, data_points]):
                raise ValueError("Missing 'target_metric' or 'data_points' for 'ingest_historical_data' operation.")
            return self.ingest_historical_data(data_id, target_metric, data_points)
        elif operation == "forecast_trend":
            forecast_period_days = kwargs.get('forecast_period_days')
            if forecast_period_days is None: # Check for None specifically as 0 is a valid int
                raise ValueError("Missing 'forecast_period_days' for 'forecast_trend' operation.")
            return self.forecast_trend(data_id, forecast_period_days)
        elif operation == "identify_risk":
            risk_threshold = kwargs.get('risk_threshold')
            if risk_threshold is None: # Check for None specifically as 0 is a valid float
                raise ValueError("Missing 'risk_threshold' for 'identify_risk' operation.")
            return self.identify_risk(data_id, risk_threshold)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating PredictiveAnalyticsSimulatorTool functionality...")
    temp_dir = "temp_predictive_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    predictive_tool = PredictiveAnalyticsSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Ingest some simulated historical sales data
        print("\n--- Ingesting historical sales data ---")
        sales_data_points = [
            {"date": "2025-01-01", "value": 100},
            {"date": "2025-02-01", "value": 110},
            {"date": "2025-03-01", "value": 120},
            {"date": "2025-04-01", "value": 130},
            {"date": "2025-05-01", "value": 140}
        ]
        predictive_tool.execute(operation="ingest_historical_data", data_id="sales_data_q1q2", target_metric="sales", data_points=sales_data_points)
        print("Historical sales data ingested.")

        # 2. Forecast future sales
        print("\n--- Forecasting sales for the next 30 days ---")
        forecast_report = predictive_tool.execute(operation="forecast_trend", data_id="sales_data_q1q2", forecast_period_days=30)
        print(json.dumps(forecast_report, indent=2))

        # 3. Ingest data with a potential risk
        print("\n--- Ingesting historical data with a potential risk ---")
        risk_data_points = [
            {"date": "2025-01-01", "value": 50},
            {"date": "2025-02-01", "value": 55},
            {"date": "2025-03-01", "value": 60},
            {"date": "2025-04-01", "value": 85} # High value
        ]
        predictive_tool.execute(operation="ingest_historical_data", data_id="system_load_data", target_metric="system_load", data_points=risk_data_points)
        print("Historical system load data ingested.")

        # 4. Identify risk
        print("\n--- Identifying risk for 'system_load_data' with threshold 80 ---")
        risk_report = predictive_tool.execute(operation="identify_risk", data_id="system_load_data", risk_threshold=80)
        print(json.dumps(risk_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")