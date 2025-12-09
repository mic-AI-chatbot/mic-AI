import logging
import random
from typing import Dict, Any, List
from tools.base_tool import BaseTool
from moviepy.editor import VideoFileClip
import os

logger = logging.getLogger(__name__)

class VideoAnalyticsPlatformTool(BaseTool):
    """
    A tool for simulating a video analytics platform.
    """
    def __init__(self, tool_name: str = "video_analytics_platform_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates a video analytics platform for object detection, motion detection, and summarization."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'get_metadata', 'detect_objects', 'detect_motion', 'summarize'."
                },
                "video_path": {"type": "string", "description": "The local file path to the video."},
                "object_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "A list of object types to detect (e.g., 'person', 'car').",
                    "default": ["person", "car", "bicycle"]
                }
            },
            "required": ["action", "video_path"]
        }

    def execute(self, action: str, video_path: str, **kwargs: Any) -> Dict:
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found at '{video_path}'.")

            action = action.lower()
            actions = {
                "get_metadata": self._get_metadata,
                "detect_objects": self._detect_objects,
                "detect_motion": self._detect_motion,
                "summarize": self._summarize_video,
            }
            if action not in actions:
                raise ValueError(f"Invalid action. Supported: {list(actions.keys())}")

            return actions[action](video_path=video_path, **kwargs)

        except Exception as e:
            logger.error(f"An error occurred in VideoAnalyticsPlatformTool: {e}")
            return {"error": str(e)}

    def _get_video_duration(self, video_path: str) -> float:
        with VideoFileClip(video_path) as clip:
            return clip.duration

    def _get_metadata(self, video_path: str, **kwargs) -> Dict:
        with VideoFileClip(video_path) as clip:
            metadata = {
                "filename": os.path.basename(video_path),
                "duration_seconds": clip.duration,
                "fps": clip.fps,
                "resolution": clip.size
            }
        return {"video_metadata": metadata}

    def _detect_objects(self, video_path: str, object_types: List[str], **kwargs) -> Dict:
        duration = self._get_video_duration(video_path)
        num_detections = random.randint(3, 10)  # nosec B311
        detections = []
        for _ in range(num_detections):
            obj_type = random.choice(object_types)  # nosec B311
            timestamp = round(random.uniform(0, duration), 2)  # nosec B311
            detections.append({
                "object_type": obj_type,
                "timestamp": timestamp,
                "confidence": round(random.uniform(0.7, 0.99), 2),  # nosec B311
                "bounding_box": [random.randint(10, 400), random.randint(10, 400), random.randint(450, 800), random.randint(450, 800)]  # nosec B311
            })
        
        detections.sort(key=lambda x: x["timestamp"])
        return {"object_detection_results": detections}

    def _detect_motion(self, video_path: str, **kwargs) -> Dict:
        duration = self._get_video_duration(video_path)
        num_events = random.randint(2, 5)  # nosec B311
        events = []
        for _ in range(num_events):
            start = round(random.uniform(0, duration - 5), 2)  # nosec B311
            end = round(start + random.uniform(1, 5), 2)  # nosec B311
            events.append({"start_time": start, "end_time": end})
            
        events.sort(key=lambda x: x["start_time"])
        return {"motion_detection_results": events}

    def _summarize_video(self, video_path: str, **kwargs) -> Dict:
        duration = self._get_video_duration(video_path)
        object_results = self._detect_objects(video_path, ["person", "car"], **kwargs)
        motion_results = self._detect_motion(video_path, **kwargs)

        key_events = [f"Motion detected at {event['start_time']}s." for event in motion_results["motion_detection_results"][:2]]
        key_events += [f"{det['object_type']} detected at {det['timestamp']}s." for det in object_results["object_detection_results"][:3]]
        
        summary = (
            f"Video of {duration:.2f} seconds analyzed. "
            f"Detected {len(object_results['object_detection_results'])} objects and {len(motion_results['motion_detection_results'])} motion events. "
            "Key moments include: " + ", ".join(key_events)
        )
        return {"video_summary": summary}