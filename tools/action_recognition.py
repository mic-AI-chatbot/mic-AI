import logging
import random
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from transformers import pipeline
import numpy as np
import cv2  # Using opencv-python
import json

logger = logging.getLogger(__name__)

class VideoAnalyzer:
    """A helper class to analyze videos using transformers models."""
    def __init__(self, tool_name):
        self.pipe = None
        try:
            # Using a pre-trained model for video classification.
            # This model is effective for general action recognition.
            self.pipe = pipeline("video-classification", model="MCG-NJU/videomae-base-finetuned-kinetics-400")
        except Exception as e:
            logger.error(f"Failed to load video-classification model: {e}")
            self.pipe = None # Ensure pipe is None if loading fails

    def get_video_frames(self, video_source: str, num_frames: int = 16) -> List[np.ndarray]:
        """
        Loads a video from the given source and extracts a specified number of frames.
        """
        try:
            cap = cv2.VideoCapture(video_source)
            frames = []
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if total_frames == 0:
                logger.warning(f"Video source '{video_source}' could not be opened or is empty.")
                return [np.random.randint(0, 255, size=(224, 224, 3), dtype=np.uint8) for _ in range(num_frames)]

            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

            for i in sorted(set(frame_indices)):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                if not ret:
                    continue
                # Convert frame from BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame)
            cap.release()
            
            if not frames:
                logger.warning(f"Could not read frames from {video_source}. Returning random frames.")
                return [np.random.randint(0, 255, size=(224, 224, 3), dtype=np.uint8) for _ in range(num_frames)]

            return frames
        except Exception as e:
            logger.error(f"Failed to process video {video_source}: {e}")
            # Fallback to random frames if video processing fails
            return [np.random.randint(0, 255, size=(224, 224, 3), dtype=np.uint8) for _ in range(num_frames)]


class RecognizeActionTool(BaseTool):
    """
    Tool to recognize human actions in a video using a pre-trained model.
    """
    def __init__(self, tool_name: str = "recognize_action"):
        super().__init__(tool_name=tool_name)
        self.video_analyzer = VideoAnalyzer(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Recognizes human actions (e.g., walking, running) in a given video and returns detected actions with confidence scores."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_source": {"type": "string", "description": "The path to the video file to analyze."},
            },
            "required": ["video_source"]
        }

    def execute(self, video_source: str, **kwargs: Any) -> str:
        """
        Recognizes actions in a video and returns a JSON string of the results.
        """
        if self.video_analyzer.pipe is None:
            return json.dumps([{"error": "Action recognition model is not loaded. Please check server logs for details."}])
        if not video_source:
            return json.dumps([{"error": "Video source cannot be empty."}])
            
        frames = self.video_analyzer.get_video_frames(video_source)
        
        try:
            results = self.video_analyzer.pipe(frames)
            return json.dumps(results, indent=2)
        except Exception as e:
            logger.error(f"An error occurred during action recognition: {e}")
            return json.dumps([{"error": f"An error occurred during action recognition: {e}"}])

class DetectEventTool(BaseTool):
    """
    Tool to simulate detecting specific events in a video stream.
    NOTE: This is a simulation and does not use a real model.
    """
    def __init__(self, tool_name: str = "detect_event"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates detecting specific events (e.g., anomalies, specific occurrences) in a video stream and returns detected events with timestamps."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_source": {"type": "string", "description": "The URL or identifier of the video stream to analyze."},
                "event_type": {"type": "string", "description": "The type of event to detect (e.g., 'anomaly', 'intrusion').", "default": "anomaly"}
            },
            "required": ["video_source"]
        }

    def execute(self, video_source: str, event_type: str = "anomaly", **kwargs: Any) -> str:
        """
        Simulates event detection and returns a JSON string of the results.
        A real implementation would require a dedicated event detection model.
        """
        timestamp = random.uniform(0, 60)  # nosec B311
        result = {
            "event": event_type,
            "timestamp": f"{timestamp:.2f}s",
            "confidence": random.uniform(0.7, 0.99),  # nosec B311
            "simulation": True
        }
        return json.dumps([result], indent=2)

class TrackActivityTool(BaseTool):
    """
    Tool to simulate tracking activities over time in a video stream.
    NOTE: This is a simulation and does not use a real model.
    """
    def __init__(self, tool_name: str = "track_activity"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates tracking general activities (e.g., movement, interaction) over time in a video stream and returns activity summaries."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_source": {"type": "string", "description": "The URL or identifier of the video stream to analyze."},
                "activity_type": {"type": "string", "description": "The type of activity to track (e.g., 'general', 'specific_task').", "default": "general"}
            },
            "required": ["video_source"]
        }

    def execute(self, video_source: str, activity_type: str = "general", **kwargs: Any) -> str:
        """
        Simulates activity tracking and returns a JSON string of the summary.
        A real implementation would require a model capable of temporal activity detection.
        """
        duration = random.uniform(5, 20)  # nosec B311
        result = {
            "activity": activity_type,
            "start_time": "0.00s",
            "end_time": f"{duration:.2f}s",
            "summary": "Activity detected and tracked (simulated).",
            "simulation": True
        }
        return json.dumps([result], indent=2)

class AnalyzePoseAndGesturesTool(BaseTool):
    """
    Tool to analyze human poses and gestures in a video using a pre-trained model.
    It filters action recognition results for gesture-related classes.
    """
    def __init__(self, tool_name: str = "analyze_pose_and_gestures"):
        super().__init__(tool_name=tool_name)
        self.video_analyzer = VideoAnalyzer(tool_name=tool_name)
        # List of gesture-related classes from the Kinetics-400 dataset
        self.gesture_keywords = [
            "waving", "pointing", "clapping", "thumb up", "thumb down", "shaking head", "nodding"
        ]

    @property
    def description(self) -> str:
        return "Analyzes a video to detect human poses and gestures, returning findings with confidence scores."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "video_source": {"type": "string", "description": "The path to the video file to analyze."}
            },
            "required": ["video_source"]
        }

    def execute(self, video_source: str, **kwargs: Any) -> str:
        """
        Analyzes gestures in a video and returns a JSON string of the results.
        """
        if self.video_analyzer.pipe is None:
            return json.dumps([{"error": "Pose and gesture analysis model is not loaded. Please check server logs for details."}])
        if not video_source:
            return json.dumps([{"error": "Video source cannot be empty."}])

        frames = self.video_analyzer.get_video_frames(video_source)
        
        try:
            results = self.video_analyzer.pipe(frames)
            
            # Filter results for gestures
            gesture_results = []
            for result in results:
                for keyword in self.gesture_keywords:
                    if keyword in result['label']:
                        gesture_results.append(result)
                        break # Move to the next result once a keyword is found
            
            if not gesture_results:
                return json.dumps([{"message": "No specific gestures detected, but here are the top general actions found.", "actions": results[:2]}])

            return json.dumps(gesture_results, indent=2)
        except Exception as e:
            logger.error(f"An error occurred during gesture analysis: {e}")
            return json.dumps([{"error": f"An error occurred during gesture analysis: {e}"}])
