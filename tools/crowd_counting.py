import logging
import json
import random
import base64
import os
from io import BytesIO
from typing import Union, List, Dict, Any, Optional

# Deferring heavy imports
try:
    from transformers import pipeline
    from PIL import Image
    import requests
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers, PIL, or requests not found. Crowd counting tools will not be fully functional. Please install 'transformers', 'torch', 'Pillow', 'requests'.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class CrowdCountingModel:
    """Manages AI models for crowd counting tasks, using a singleton pattern."""
    _object_detector = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CrowdCountingModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for crowd counting are not installed.")
                return cls._instance # Return instance without models
            
            try:
                logger.info("Initializing object detection model (facebook/detr-resnet-50) for crowd counting...")
                cls._instance._object_detector = pipeline("object-detection", model="facebook/detr-resnet-50")
            except Exception as e:
                logger.error(f"Failed to load object detection model: {e}")
        return cls._instance

    def _load_image(self, image_path: str = None, image_url: str = None, image_base64: str = None) -> Image.Image:
        if image_path:
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found at {image_path}")
            return Image.open(image_path).convert("RGB")
        elif image_url:
            response = requests.get(image_url, stream=True, timeout=10)
            response.raise_for_status() # Raise an exception for HTTP errors
            return Image.open(BytesIO(response.content)).convert("RGB")
        elif image_base64:
            image_bytes = base64.b64decode(image_base64)
            return Image.open(BytesIO(image_bytes)).convert("RGB")
        else:
            raise ValueError("One of image_path, image_url, or image_base64 must be provided.")

    def count_people(self, image_path: str = None, image_url: str = None, image_base64: str = None) -> Dict[str, Any]:
        if not self._object_detector: return {"error": "Object detection model not available. Check logs for loading errors."}
        try:
            image = self._load_image(image_path, image_url, image_base64)
            detection_results = self._object_detector(image)
            
            people_count = 0
            people_detections = []
            for det in detection_results:
                if det['label'].lower() == 'person':
                    people_count += 1
                    people_detections.append({"box": det['box'], "score": round(det['score'], 2)})
            
            return {"people_count": people_count, "people_detections": people_detections}
        except Exception as e:
            logger.error(f"People counting failed: {e}")
            return {"error": f"People counting failed: {e}"}

crowd_counting_model_instance = CrowdCountingModel()

class CountPeopleTool(BaseTool):
    """Counts the number of people in an image or video frame using an AI model."""
    def __init__(self, tool_name="count_people"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Counts the number of people detected in an image or video frame (from path, URL, or base64) using an AI object detection model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Optional: The absolute path to the image file.", "default": None},
                "image_url": {"type": "string", "description": "Optional: The URL of the image.", "default": None},
                "image_base64": {"type": "string", "description": "Optional: Base64 encoded image data.", "default": None}
            },
            "required": [] # One of the image sources must be provided
        }

    def execute(self, image_path: str = None, image_url: str = None, image_base64: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for crowd counting are not available. Please install 'transformers', 'torch', 'Pillow', 'requests'."})

        result = crowd_counting_model_instance.count_people(image_path, image_url, image_base64)
        if "error" in result:
            return json.dumps(result)
        
        return json.dumps({
            "image_source": image_path or image_url or "base64_data",
            "crowd_count": result["people_count"],
            "message": f"Detected {result['people_count']} people in the image.",
            "people_detections_sample": result["people_detections"][:5] # Show a sample of detections
        }, indent=2)

class EstimateCrowdDensityTool(BaseTool):
    """Estimates crowd density in an image or video frame using an AI model."""
    def __init__(self, tool_name="estimate_crowd_density"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Estimates the density of a crowd in an image or video frame (from path, URL, or base64) using an AI object detection model, categorizing it (e.g., 'sparse', 'medium', 'dense')."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Optional: The absolute path to the image file.", "default": None},
                "image_url": {"type": "string", "description": "Optional: The URL of the image.", "default": None},
                "image_base64": {"type": "string", "description": "Optional: Base64 encoded image data.", "default": None}
            },
            "required": [] # One of the image sources must be provided
        }

    def execute(self, image_path: str = None, image_url: str = None, image_base64: str = None, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for crowd counting are not available. Please install 'transformers', 'torch', 'Pillow', 'requests'."})

        result = crowd_counting_model_instance.count_people(image_path, image_url, image_base64)
        if "error" in result:
            return json.dumps(result)
        
        people_count = result["people_count"]
        
        # Simulate density estimation based on count (and implicitly, image size)
        # These thresholds are arbitrary and would depend on actual image resolution/area
        density_category = "sparse"
        if people_count > 50:
            density_category = "medium"
        if people_count > 200:
            density_category = "dense"
        
        return json.dumps({
            "image_source": image_path or image_url or "base64_data",
            "people_count": people_count,
            "density_category": density_category,
            "message": f"Estimated crowd density as '{density_category}' with {people_count} people detected."
        }, indent=2)