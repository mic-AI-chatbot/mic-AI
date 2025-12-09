
import logging
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import math

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SeismicDataAnalyzerSimulatorTool(BaseTool):
    """
    A tool that simulates seismic data analysis, allowing for ingesting
    seismic data, detecting events, estimating magnitudes, and generating reports.
    """

    def __init__(self, tool_name: str = "SeismicDataAnalyzerSimulator", data_dir: str = ".", **kwargs):
        super().__init__(tool_name=tool_name, **kwargs)
        self.data_dir = data_dir
        self.data_file = os.path.join(self.data_dir, "seismic_data.json")
        self.reports_file = os.path.join(self.data_dir, "seismic_analysis_reports.json")
        
        # Seismic data: {station_id: {data_points: [{timestamp: ..., amplitude: ...}]}}
        self.seismic_data: Dict[str, Dict[str, Any]] = self._load_data(self.data_file, default={})
        # Analysis reports: {report_id: {station_id: ..., detected_events: []}}
        self.analysis_reports: Dict[str, Dict[str, Any]] = self._load_data(self.reports_file, default={})

    @property
    def description(self) -> str:
        return "Simulates seismic data analysis: ingest data, detect events, estimate magnitudes, and generate reports."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {"type": "string", "enum": ["ingest_seismic_data", "detect_events", "estimate_magnitude", "generate_report"]},
                "station_id": {"type": "string"},
                "data_points": {"type": "array", "items": {"type": "object", "properties": {"timestamp": {"type": "string"}, "amplitude": {"type": "number"}}}},
                "threshold": {"type": "number", "minimum": 0.0},
                "event_id": {"type": "string"},
                "peak_amplitude": {"type": "number", "minimum": 0.0}
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

    def _save_seismic_data(self):
        with open(self.data_file, 'w') as f: json.dump(self.seismic_data, f, indent=2)

    def _save_reports(self):
        with open(self.reports_file, 'w') as f: json.dump(self.analysis_reports, f, indent=2)

    def ingest_seismic_data(self, station_id: str, data_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Ingests simulated seismic data for a station."""
        if station_id in self.seismic_data: raise ValueError(f"Seismic data for station '{station_id}' already exists.")
        
        # Ensure data points are sorted by timestamp
        data_points.sort(key=lambda x: datetime.fromisoformat(x['timestamp']))

        new_data = {
            "id": station_id, "data_points": data_points,
            "ingested_at": datetime.now().isoformat()
        }
        self.seismic_data[station_id] = new_data
        self._save_seismic_data()
        return new_data

    def detect_events(self, station_id: str, threshold: float) -> Dict[str, Any]:
        """Detects seismic events by identifying amplitude spikes above a threshold."""
        seismic_record = self.seismic_data.get(station_id)
        if not seismic_record: raise ValueError(f"Seismic data for station '{station_id}' not found. Ingest it first.")
        
        detected_events = []
        in_event = False
        event_start_time = None
        event_peak_amplitude = 0.0
        
        for i, dp in enumerate(seismic_record["data_points"]):
            if dp["amplitude"] >= threshold and not in_event:
                in_event = True
                event_start_time = dp["timestamp"]
                event_peak_amplitude = dp["amplitude"]
            elif dp["amplitude"] >= threshold and in_event:
                event_peak_amplitude = max(event_peak_amplitude, dp["amplitude"])
            elif dp["amplitude"] < threshold and in_event:
                in_event = False
                event_id = f"event_{station_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(100,999)}"  # nosec B311
                detected_events.append({
                    "id": event_id, "start_time": event_start_time, "end_time": dp["timestamp"],
                    "peak_amplitude": event_peak_amplitude, "status": "detected"
                })
                event_peak_amplitude = 0.0
        
        report_id = f"detection_report_{station_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report = {
            "id": report_id, "station_id": station_id, "threshold": threshold,
            "detected_events": detected_events,
            "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def estimate_magnitude(self, event_id: str, peak_amplitude: float) -> Dict[str, Any]:
        """Estimates the magnitude of a seismic event using a simple formula."""
        # Simplified magnitude estimation (e.g., Richter scale approximation)
        # M = log10(A) + C, where A is peak amplitude and C is a constant
        magnitude_constant = 2.5 # Arbitrary constant for simulation
        magnitude = round(math.log10(peak_amplitude) + magnitude_constant, 2) if peak_amplitude > 0 else 0.0
        
        return {"status": "success", "event_id": event_id, "peak_amplitude": peak_amplitude, "estimated_magnitude": magnitude}

    def generate_report(self, station_id: str) -> Dict[str, Any]:
        """Generates a report summarizing detected events and their magnitudes."""
        report_id = f"summary_report_{station_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        detected_events_reports = [r for r in self.analysis_reports.values() if r.get("station_id") == station_id and r.get("detected_events")]
        
        summary = {
            "station_id": station_id,
            "total_events_detected": sum(len(r["detected_events"]) for r in detected_events_reports),
            "events_details": []
        }
        
        for r in detected_events_reports:
            for event in r["detected_events"]:
                magnitude_info = self.estimate_magnitude(event["id"], event["peak_amplitude"])
                summary["events_details"].append({
                    "event_id": event["id"],
                    "start_time": event["start_time"],
                    "end_time": event["end_time"],
                    "peak_amplitude": event["peak_amplitude"],
                    "estimated_magnitude": magnitude_info["estimated_magnitude"]
                })
        
        report = {
            "id": report_id, "station_id": station_id, "type": "seismic_summary",
            "summary": summary, "generated_at": datetime.now().isoformat()
        }
        self.analysis_reports[report_id] = report
        self._save_reports()
        return report

    def execute(self, operation: str, **kwargs: Any) -> Any:
        if operation == "ingest_seismic_data":
            return self.ingest_seismic_data(kwargs['station_id'], kwargs['data_points'])
        elif operation == "detect_events":
            return self.detect_events(kwargs['station_id'], kwargs['threshold'])
        elif operation == "estimate_magnitude":
            return self.estimate_magnitude(kwargs['event_id'], kwargs['peak_amplitude'])
        elif operation == "generate_report":
            return self.generate_report(kwargs['station_id'])
        else:
            raise ValueError(f"Invalid operation: {operation}.")

if __name__ == '__main__':
    print("Demonstrating SeismicDataAnalyzerSimulatorTool functionality...")
    temp_dir = "temp_seismic_data"
    if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    analyzer_tool = SeismicDataAnalyzerSimulatorTool(data_dir=temp_dir)
    
    try:
        # 1. Ingest some simulated seismic data
        print("\n--- Ingesting seismic data for 'station_A' ---")
        seismic_data_points = []
        current_time = datetime.now()
        for i in range(100):
            amplitude = random.uniform(0.1, 0.5)  # nosec B311
            if 30 < i < 40: amplitude = random.uniform(1.0, 3.0) # Simulate an event  # nosec B311
            seismic_data_points.append({"timestamp": (current_time + timedelta(seconds=i)).isoformat(), "amplitude": amplitude})
        
        analyzer_tool.execute(operation="ingest_seismic_data", station_id="station_A", data_points=seismic_data_points)
        print("Seismic data ingested.")

        # 2. Detect events
        print("\n--- Detecting events for 'station_A' with threshold 0.8 ---")
        detection_report = analyzer_tool.execute(operation="detect_events", station_id="station_A", threshold=0.8)
        print(json.dumps(detection_report, indent=2))

        # 3. Estimate magnitude for a detected event
        if detection_report["detected_events"]:
            event_to_estimate = detection_report["detected_events"][0]
            print(f"\n--- Estimating magnitude for event '{event_to_estimate['id']}' ---")
            magnitude = analyzer_tool.execute(operation="estimate_magnitude", event_id=event_to_estimate["id"], peak_amplitude=event_to_estimate["peak_amplitude"])
            print(json.dumps(magnitude, indent=2))

        # 4. Generate a report
        print("\n--- Generating summary report for 'station_A' ---")
        summary_report = analyzer_tool.execute(operation="generate_report", station_id="station_A")
        print(json.dumps(summary_report, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        if os.path.exists(temp_dir): import shutil; shutil.rmtree(temp_dir)
        print(f"\nCleaned up temporary directory '{temp_dir}'.")
