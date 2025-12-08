import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class RealtimeDataIngestionSimulatorTool(BaseTool):
    """
    A tool that simulates real-time data ingestion, allowing for defining
    data streams, ingesting data, and monitoring stream status.
    """

    def __init__(self, tool_name: str = "RealtimeDataIngestionSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.streams_file = os.path.join(self.data_dir, "data_streams.json")
        self.logs_file = os.path.join(self.data_dir, "ingestion_logs.json")
        
        # Data streams: {stream_id: {name: ..., source_type: ..., expected_volume_per_minute: ...}}
        self.data_streams: Dict[str, Dict[str, Any]] = self._load_data(self.streams_file, default={})
        # Ingestion logs: {stream_id: [{timestamp: ..., volume: ..., latency_ms: ..., data_quality_score: ...}]}
        self.ingestion_logs: Dict[str, List[Dict[str, Any]]] = self._load_data(self.logs_file, default={})

    @property
    def description(self) -> str:
        return "Simulates real-time data ingestion: define streams, ingest data, and get stream status."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["define_data_stream", "ingest_data", "get_stream_status"]},
                "stream_id": {"type": "string"},
                "name": {"type": "string"},
                "source_type": {"type": "string", "enum": ["sensor", "api_feed", "log_file"]},
                "expected_volume_per_minute": {"type": "integer", "minimum": 1},
                "data_volume": {"type": "integer", "minimum": 1}
            },
            "required": ["operation", "stream_id"]
        }

    def _load_data(self, file_path: str, default: Any) -> Any:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try: return json.load(f)
                except json.JSONDecodeError:
                    self.logger.warning(f"Corrupted data file '{file_path}'. Using default.")
                    return default
        return default

    def _save_streams(self):
        with open(self.streams_file, 'w') as f: json.dump(self.data_streams, f, indent=2)

    def _save_logs(self):
        with open(self.logs_file, 'w') as f: json.dump(self.ingestion_logs, f, indent=2)

    def define_data_stream(self, stream_id: str, name: str, source_type: str, expected_volume_per_minute: int) -> Dict[str, Any]:
        """Defines a new real-time data stream."""
        if stream_id in self.data_streams: raise ValueError(f"Data stream '{stream_id}' already exists.")
        
        new_stream = {
            "id": stream_id, "name": name, "source_type": source_type,
            "expected_volume_per_minute": expected_volume_per_minute,
            "defined_at": datetime.now().isoformat()
        }
        self.data_streams[stream_id] = new_stream
        self._save_streams()
        return new_stream

    def ingest_data(self, stream_id: str, data_volume: int) -> Dict[str, Any]:
        """Simulates ingesting data into a specified stream."""
        stream = self.data_streams.get(stream_id)
        if not stream: raise ValueError(f"Data stream '{stream_id}' not found. Define it first.")
        
        simulated_latency_ms = random.randint(10, 200)  # nosec B311
        data_quality_score = round(random.uniform(0.8, 0.99), 2)  # nosec B311
        
        # Simulate degradation if volume is much higher than expected
        if data_volume > stream["expected_volume_per_minute"] * 1.5:
            simulated_latency_ms = random.randint(200, 1000)  # nosec B311
            data_quality_score = round(random.uniform(0.5, 0.7), 2)  # nosec B311
        
        log_entry = {
            "timestamp": datetime.now().isoformat(), "volume": data_volume,
            "latency_ms": simulated_latency_ms, "data_quality_score": data_quality_score
        }
        self.ingestion_logs.setdefault(stream_id, []).append(log_entry)
        self._save_logs()
        return {"status": "success", "message": f"Ingested {data_volume} units into stream '{stream_id}'."}

    def get_stream_status(self, stream_id: str) -> Dict[str, Any]:
        """Retrieves the current status of a data stream."""
        stream = self.data_streams.get(stream_id)
        if not stream: raise ValueError(f"Data stream '{stream_id}' not found.")
        
        logs = self.ingestion_logs.get(stream_id, [])
        
        total_volume_last_hour = 0
        avg_latency_last_hour = 0
        recent_logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) > datetime.now() - timedelta(hours=1)]
        
        if recent_logs:
            total_volume_last_hour = sum(log["volume"] for log in recent_logs)
            avg_latency_last_hour = sum(log["latency_ms"] for log in recent_logs) / len(recent_logs)
        
        return {
            "stream_id": stream_id, "name": stream["name"], "source_type": stream["source_type"],
            "expected_volume_per_minute": stream["expected_volume_per_minute"],
            "current_status": "active", # Simplified
            "metrics_last_hour": {
                "total_volume": total_volume_last_hour,
                "avg_latency_ms": round(avg_latency_last_hour, 2),
                "num_ingestion_events": len(recent_logs)
            }
        }

    def execute(self, operation: str, stream_id: str, **kwargs: Any) -> Any:
        if operation == "define_data_stream":
            name = kwargs.get('name')
            source_type = kwargs.get('source_type')
            expected_volume_per_minute = kwargs.get('expected_volume_per_minute')
            if not all([name, source_type, expected_volume_per_minute]):
                raise ValueError("Missing 'name', 'source_type', or 'expected_volume_per_minute' for 'define_data_stream' operation.")
            return self.define_data_stream(stream_id, name, source_type, expected_volume_per_minute)
        elif operation == "ingest_data":
            data_volume = kwargs.get('data_volume')
            if data_volume is None: # Check for None specifically as 0 is a valid int
                raise ValueError("Missing 'data_volume' for 'ingest_data' operation.")
            return self.ingest_data(stream_id, data_volume)
        elif operation == "get_stream_status":
            # No additional kwargs required for get_stream_status
            return self.get_stream_status(stream_id)
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating RealtimeDataIngestionSimulatorTool functionality...")
    temp_dir = "temp_data_ingestion_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    ingestion_tool = RealtimeDataIngestionSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Define a data stream
        print("\n--- Defining data stream 'sensor_data_stream' ---")
        ingestion_tool.execute(operation="define_data_stream", stream_id="sensor_data_stream", name="IoT Sensor Data", source_type="sensor", expected_volume_per_minute=100)
        print("Stream defined.")

        # 2. Ingest some data
        print("\n--- Ingesting data into 'sensor_data_stream' (normal volume) ---")
        ingestion_tool.execute(operation="ingest_data", stream_id="sensor_data_stream", data_volume=90)
        print("Data ingested.")

        # 3. Ingest more data (simulating high volume)
        print("\n--- Ingesting data into 'sensor_data_stream' (high volume) ---")
        ingestion_tool.execute(operation="ingest_data", stream_id="sensor_data_stream", data_volume=200)
        print("Data ingested.")

        # 4. Get stream status
        print("\n--- Getting status for 'sensor_data_stream' ---")
        status = ingestion_tool.execute(operation="get_stream_status", stream_id="sensor_data_stream")
        print(json.dumps(status, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")