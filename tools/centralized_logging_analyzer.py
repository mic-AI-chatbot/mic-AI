import logging
import json
import random
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from mic.database import get_db
from mic.models import LogEntry
from sqlalchemy import and_

logger = logging.getLogger(__name__)

class LogGenerator:
    """Generates mock log entries for simulation."""
    def generate_log_entry(self, service: str) -> Dict[str, str]:
        levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR"] # More INFO, fewer WARNING/ERROR
        level = random.choice(levels)  # nosec B311
        
        messages = {
            "INFO": ["Request processed successfully.", "User logged in.", "Data updated.", "Service heartbeat."],
            "WARNING": ["High latency detected.", "Resource utilization above threshold.", "Deprecated API call.", "Cache miss."],
            "ERROR": ["NullPointerException in module X.", "Database connection failed.", "Unauthorized access attempt.", "External service timeout."]
        }
        message = random.choice(messages[level])  # nosec B311
        
        return {
            "timestamp": (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat() + "Z",  # nosec B311
            "level": level,
            "service": service,
            "message": message
        }

log_generator = LogGenerator()

class GenerateAndStoreLogsTool(BaseTool):
    """Generates mock log entries and stores them in a centralized database."""
    def __init__(self, tool_name="generate_and_store_logs"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a specified number of mock log entries for various services and stores them in a centralized database."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_entries": {"type": "integer", "description": "The number of mock log entries to generate.", "default": 100},
                "services": {"type": "array", "items": {"type": "string"}, "description": "A list of simulated service names.", "default": ["auth_service", "payment_service", "user_service"]}
            },
            "required": []
        }

    def execute(self, num_entries: int = 100, services: List[str] = None, **kwargs: Any) -> str:
        if services is None:
            services = ["auth_service", "payment_service", "user_service"]
        
        added_count = 0
        db = next(get_db())
        try:
            for _ in range(num_entries):
                service = random.choice(services)  # nosec B311
                log_entry_data = log_generator.generate_log_entry(service)
                new_log = LogEntry(**log_entry_data)
                db.add(new_log)
                added_count += 1
            db.commit()
            report = {"message": f"{added_count} mock log entries generated and stored."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error generating and storing logs: {e}")
            report = {"error": f"Failed to generate and store logs: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class AnalyzeLogsForErrorsTool(BaseTool):
    """Analyzes stored log data for errors and warnings."""
    def __init__(self, tool_name="analyze_logs_for_errors"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes stored log data for errors and warnings, summarizing their counts and types."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "service": {"type": "string", "description": "Optional: Filter logs by service."},
                "start_time": {"type": "string", "description": "Optional: Filter logs by start time (YYYY-MM-DDTHH:MM:SSZ)."},
                "end_time": {"type": "string", "description": "Optional: Filter logs by end time (YYYY-MM-DDTHH:MM:SSZ)."}
            },
            "required": []
        }

    def execute(self, service: str = None, start_time: str = None, end_time: str = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            error_query = db.query(LogEntry).filter(LogEntry.level == "ERROR")
            warning_query = db.query(LogEntry).filter(LogEntry.level == "WARNING")

            if service:
                error_query = error_query.filter(LogEntry.service == service)
                warning_query = warning_query.filter(LogEntry.service == service)
            if start_time:
                error_query = error_query.filter(LogEntry.timestamp >= start_time)
                warning_query = warning_query.filter(LogEntry.timestamp >= start_time)
            if end_time:
                error_query = error_query.filter(LogEntry.timestamp <= end_time)
                warning_query = warning_query.filter(LogEntry.timestamp <= end_time)
            
            errors = error_query.all()
            warnings = warning_query.all()
            
            error_messages = [log.message for log in errors]
            warning_messages = [log.message for log in warnings]

            report = {
                "total_errors": len(errors),
                "total_warnings": len(warnings),
                "error_messages_sample": error_messages[:5], # Show up to 5 samples
                "warning_messages_sample": warning_messages[:5]
            }
        except Exception as e:
            logger.error(f"Error analyzing logs for errors: {e}")
            report = {"error": f"Failed to analyze logs for errors: {e}"}
        finally:
            db.close()
        return json.dumps(report, indent=2)

class VisualizeLogTrendsTool(BaseTool):
    """Visualizes log trends (e.g., log levels over time)."""
    def __init__(self, tool_name="visualize_log_trends"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Visualizes log trends (e.g., log levels over time) and saves the chart to a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output_path": {"type": "string", "description": "The absolute path to save the generated chart image (e.g., 'log_trends.png')."},
                "service": {"type": "string", "description": "Optional: Filter logs by service."},
                "start_time": {"type": "string", "description": "Optional: Filter logs by start time (YYYY-MM-DDTHH:MM:SSZ)."},
                "end_time": {"type": "string", "description": "Optional: Filter logs by end time (YYYY-MM-DDTHH:MM:SSZ)."}
            },
            "required": ["output_path"]
        }

    def execute(self, output_path: str, service: str = None, start_time: str = None, end_time: str = None, **kwargs: Any) -> str:
        db = next(get_db())
        try:
            query = db.query(LogEntry)
            if service:
                query = query.filter(LogEntry.service == service)
            if start_time:
                query = query.filter(LogEntry.timestamp >= start_time)
            if end_time:
                query = query.filter(LogEntry.timestamp <= end_time)
            
            logs = query.order_by(LogEntry.timestamp).all()
            if not logs:
                return json.dumps({"error": "No log data found to visualize."})
            
            # Convert SQLAlchemy objects to dictionaries for DataFrame
            logs_data = [{
                "id": log.id,
                "timestamp": log.timestamp,
                "level": log.level,
                "service": log.service,
                "message": log.message
            } for log in logs]

            df = pd.DataFrame(logs_data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df.set_index("timestamp", inplace=True)
            
            # Resample by hour and count log levels
            log_counts = df.groupby([pd.Grouper(freq='H'), 'level']).size().unstack(fill_value=0)
            
            plt.figure(figsize=(12, 6))
            log_counts.plot(kind='line', marker='o', ax=plt.gca())
            plt.title("Log Levels Over Time")
            plt.xlabel("Time")
            plt.ylabel("Number of Logs")
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            plt.savefig(output_path)
            plt.close()
            
            report = {
                "message": f"Log trends chart generated and saved to '{os.path.abspath(output_path)}'.",
                "file_path": os.path.abspath(output_path)
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"Error generating log trends chart: {e}")
            return json.dumps({"error": f"Error generating log trends chart: {e}"})
        finally:
            db.close()