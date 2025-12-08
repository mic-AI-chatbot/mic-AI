import logging
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataStreamingPlatformTool(BaseTool):
    """
    A tool for simulating a data streaming platform, allowing for the creation
    of data streams, publishing data records, and consuming data records.
    """

    def __init__(self, tool_name: str = "data_streaming_platform"):
        super().__init__(tool_name)
        self.streams_file = "data_streams.json"
        self.streams: Dict[str, Dict[str, Any]] = self._load_streams()

    @property
    def description(self) -> str:
        return "Simulates a data streaming platform: creates streams, publishes records, and consumes data."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "The streaming operation to perform.",
                    "enum": ["create_stream", "publish_data", "consume_data", "list_streams", "get_stream_details"]
                },
                "stream_id": {"type": "string"},
                "stream_name": {"type": "string"},
                "description": {"type": "string"},
                "data_record": {"type": "object"},
                "num_records": {"type": "integer", "minimum": 1}
            },
            "required": ["operation"]
        }

    def _load_streams(self) -> Dict[str, Dict[str, Any]]:
        if os.path.exists(self.streams_file):
            with open(self.streams_file, 'r') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Corrupted streams file '{self.streams_file}'. Starting fresh.")
                    return {}
        return {}

    def _save_streams(self) -> None:
        with open(self.streams_file, 'w') as f:
            json.dump(self.streams, f, indent=4)

    def _create_stream(self, stream_id: str, stream_name: str, description: Optional[str] = None) -> Dict[str, Any]:
        if not all([stream_id, stream_name]):
            raise ValueError("Stream ID and name cannot be empty.")
        if stream_id in self.streams:
            raise ValueError(f"Data stream '{stream_id}' already exists.")

        new_stream = {
            "stream_id": stream_id, "stream_name": stream_name, "description": description,
            "created_at": datetime.now().isoformat(), "records": []
        }
        self.streams[stream_id] = new_stream
        self._save_streams()
        return new_stream

    def _publish_data(self, stream_id: str, data_record: Dict[str, Any]) -> Dict[str, Any]:
        stream = self.streams.get(stream_id)
        if not stream: raise ValueError(f"Data stream '{stream_id}' not found.")
        if not isinstance(data_record, dict): raise ValueError("Data record must be a dictionary.")

        record_with_timestamp = {
            "published_at": datetime.now().isoformat(), "data": data_record
        }
        stream["records"].append(record_with_timestamp)
        self._save_streams()
        return record_with_timestamp

    def _consume_data(self, stream_id: str, num_records: int = 1) -> List[Dict[str, Any]]:
        stream = self.streams.get(stream_id)
        if not stream: raise ValueError(f"Data stream '{stream_id}' not found.")
        if num_records <= 0: raise ValueError("Number of records to consume must be a positive integer.")

        consumed = []
        for _ in range(min(num_records, len(stream["records"]))):
            consumed.append(stream["records"].pop(0))
        
        self._save_streams()
        return consumed

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "create_stream":
            return self._create_stream(kwargs.get("stream_id"), kwargs.get("stream_name"), kwargs.get("description"))
        elif operation == "publish_data":
            return self._publish_data(kwargs.get("stream_id"), kwargs.get("data_record"))
        elif operation == "consume_data":
            return self._consume_data(kwargs.get("stream_id"), kwargs.get("num_records", 1))
        elif operation == "list_streams":
            return [{k: v for k, v in stream.items() if k != "records"} for stream in self.streams.values()]
        elif operation == "get_stream_details":
            return self.streams.get(kwargs.get("stream_id"))
        else:
            raise ValueError(f"Invalid operation: {operation}")

if __name__ == '__main__':
    print("Demonstrating DataStreamingPlatformTool functionality...")
    tool = DataStreamingPlatformTool()
    
    try:
        print("\n--- Creating Stream ---")
        tool.execute(operation="create_stream", stream_id="sensor_data", stream_name="IoT Sensor Data", description="Real-time sensor readings.")
        
        print("\n--- Publishing Data ---")
        tool.execute(operation="publish_data", stream_id="sensor_data", data_record={"device_id": "temp_001", "temperature": 25.5})

        print("\n--- Consuming Data ---")
        consumed_records = tool.execute(operation="consume_data", stream_id="sensor_data", num_records=1)
        print(json.dumps(consumed_records, indent=2))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if os.path.exists(tool.streams_file): os.remove(tool.streams_file)
        print("\nCleanup complete.")