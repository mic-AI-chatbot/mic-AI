import logging
import json
import random
import numpy as np
from typing import List, Dict, Any
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class SurveillanceDataStream:
    """Generates a simulated stream of surveillance data (e.g., activity level)."""
    def __init__(self, base_level=10, noise=2):
        self.base_level = base_level
        self.noise = noise

    def generate_data(self, points: int, anomaly_prob: float = 0.05) -> List[float]:
        data = np.random.normal(self.base_level, self.noise, points).tolist()
        for i in range(points):
            if random.random() < anomaly_prob:  # nosec B311
                # Inject an anomaly
                data[i] *= random.uniform(3, 5) # Spike in activity  # nosec B311
        return [round(d, 2) for d in data]

class AnomalyDetector:
    """Detects anomalies in a time series using a moving average and standard deviation."""
    def __init__(self, window_size=10, threshold=3.0):
        self.window_size = window_size
        self.threshold = threshold

    def find_anomalies(self, data: List[float]) -> List[Dict[str, Any]]:
        anomalies = []
        if len(data) < self.window_size:
            return []

        for i in range(self.window_size, len(data)):
            window = data[i-self.window_size : i]
            mean = np.mean(window)
            std = np.std(window)
            
            if std > 0 and abs(data[i] - mean) > self.threshold * std:
                anomalies.append({
                    "timestamp_index": i,
                    "value": data[i],
                    "reason": f"Value {data[i]} is more than {self.threshold} standard deviations from the moving average ({mean:.2f})."
                })
        return anomalies

class DetectAnomaliesInStreamTool(BaseTool):
    """Tool to detect anomalies in a simulated surveillance data stream."""
    def __init__(self, tool_name="detect_anomalies_in_stream"):
        super().__init__(tool_name=tool_name)
        self.stream_generator = SurveillanceDataStream()
        self.detector = AnomalyDetector()

    @property
    def description(self) -> str:
        return "Detects anomalies in a simulated surveillance data stream using a statistical method (moving average and standard deviation)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_points": {"type": "integer", "description": "The number of data points to simulate in the stream.", "default": 100},
                "anomaly_probability": {"type": "number", "description": "The probability of an anomaly occurring at any point.", "default": 0.05}
            },
            "required": []
        }

    def execute(self, data_points: int = 100, anomaly_probability: float = 0.05, **kwargs: Any) -> str:
        data_stream = self.stream_generator.generate_data(data_points, anomaly_probability)
        anomalies = self.detector.find_anomalies(data_stream)
        
        report = {
            "data_stream_summary": {
                "points_analyzed": len(data_stream),
                "average_level": round(np.mean(data_stream), 2)
            },
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }
        return json.dumps(report, indent=2)

class AnalyzeActivityPatternTool(BaseTool):
    """Tool to analyze the overall pattern of activity in a data stream."""
    def __init__(self, tool_name="analyze_activity_pattern"):
        super().__init__(tool_name=tool_name)
        self.stream_generator = SurveillanceDataStream()

    @property
    def description(self) -> str:
        return "Analyzes a simulated surveillance data stream to identify overall activity patterns, such as peak activity times."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data_points": {"type": "integer", "description": "The number of data points to simulate (e.g., 240 for 24 hours).", "default": 240}
            },
            "required": []
        }

    def execute(self, data_points: int = 240, **kwargs: Any) -> str:
        # Simulate a daily pattern with a peak (e.g., midday)
        base_data = np.sin(np.linspace(0, 2 * np.pi, data_points) - (np.pi / 2)) * 10 + 20
        noise = np.random.normal(0, 2, data_points)
        data_stream = [round(d, 2) for d in (base_data + noise)]
        
        peak_activity_index = np.argmax(data_stream)
        peak_activity_value = data_stream[peak_activity_index]
        
        report = {
            "analysis_period_points": data_points,
            "average_activity_level": round(np.mean(data_stream), 2),
            "peak_activity": {
                "timestamp_index": peak_activity_index,
                "value": peak_activity_value
            },
            "summary": f"The activity pattern shows a predictable peak around timestamp index {peak_activity_index}. Deviations from this pattern could be considered anomalous."
        }
        return json.dumps(report, indent=2)