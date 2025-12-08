import logging
import json
import random
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class MockAPILogGenerator:
    """Generates a stream of mock API log entries for analytics simulation."""
    def __init__(self, api_name: str):
        self.api_name = api_name
        self.endpoints = [f"/{api_name}/users", f"/{api_name}/products/{{id}}", f"/{api_name}/orders"]
        self.users = [f"user_{i}" for i in range(1, 21)]

    def generate_logs(self, num_logs: int) -> List[Dict[str, Any]]:
        logs = []
        now = datetime.utcnow()
        for _ in range(num_logs):
            # 95% success, 5% error
            status_code = 200 if random.random() < 0.95 else random.choice([400, 401, 404, 500])  # nosec B311
            # Simulate higher latency for errors
            latency = random.gauss(120, 40) if status_code == 200 else random.gauss(300, 100)
            
            logs.append({
                "timestamp": (now - timedelta(seconds=random.randint(0, 3600))).isoformat() + "Z",  # nosec B311
                "endpoint": random.choice(self.endpoints),  # nosec B311
                "user_id": random.choice(self.users),  # nosec B311
                "status_code": status_code,
                "latency_ms": max(20, round(latency))
            })
        return logs

class GetAPIGatewayAnalyticsTool(BaseTool):
    """
    Tool to generate and analyze a stream of mock API logs to produce a comprehensive analytics report.
    """
    def __init__(self, tool_name="get_api_gateway_analytics"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates and analyzes mock API logs to produce a report with traffic metrics (requests, errors, latency) and usage patterns (top users, top endpoints)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "api_name": {"type": "string", "description": "The name of the API to analyze (e.g., 'user_service')."},
                "num_logs_to_simulate": {"type": "integer", "description": "The number of log entries to simulate for the analysis.", "default": 5000}
            },
            "required": ["api_name"]
        }

    def execute(self, api_name: str, num_logs_to_simulate: int = 5000, **kwargs: Any) -> str:
        log_generator = MockAPILogGenerator(api_name)
        logs = log_generator.generate_logs(num_logs_to_simulate)
        
        if not logs:
            return json.dumps({"error": "No logs were generated for analysis."})

        # --- Calculate Traffic Metrics ---
        total_requests = len(logs)
        error_count = sum(1 for log in logs if log["status_code"] >= 400)
        error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
        
        latencies = [log["latency_ms"] for log in logs]
        avg_latency = np.mean(latencies) if latencies else 0
        p95_latency = np.percentile(latencies, 95) if latencies else 0
        p99_latency = np.percentile(latencies, 99) if latencies else 0

        # --- Calculate Usage Patterns ---
        top_users = Counter(log["user_id"] for log in logs).most_common(5)
        top_endpoints = Counter(log["endpoint"] for log in logs).most_common(3)

        report = {
            "api_name": api_name,
            "simulation_details": {
                "logs_analyzed": total_requests,
                "time_simulated": "last_hour"
            },
            "traffic_metrics": {
                "total_requests": total_requests,
                "error_count": error_count,
                "error_rate_percent": round(error_rate, 2),
                "average_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "p99_latency_ms": round(p99_latency, 2)
            },
            "usage_patterns": {
                "top_5_users": [{"user_id": user, "requests": count} for user, count in top_users],
                "top_3_endpoints": [{"endpoint": endpoint, "requests": count} for endpoint, count in top_endpoints]
            }
        }
        
        return json.dumps(report, indent=2)