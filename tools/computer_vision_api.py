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
    logging.warning("transformers, PIL, or requests not found. Computer Vision tools will not be fully functional. Please install 'transformers', 'torch', 'Pillow', 'requests'.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ComputerVisionModel:
    """Manages AI models for computer vision tasks, using a singleton pattern."""
    _object_detector = None
    _image_classifier = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ComputerVisionModel, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("Required libraries for computer vision are not installed.")
                return cls._instance # Return instance without models
            
            try:
                logger.info("Initializing object detection model (facebook/detr-resnet-50)...")
                cls._instance._object_detector = pipeline("object-detection", model="facebook/detr-resnet-50")
                logger.info("Initializing image classification model (google/vit-base-patch16-224)...")
                cls._instance._image_classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
            except Exception as e:
                logger.error(f"Failed to load AI models for computer vision: {e}")
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

    def detect_objects(self, image_path: str = None, image_url: str = None, image_base64: str = None) -> List[Dict[str, Any]]:
        if not self._object_detector: return [{"error": "Object detection model not available. Check logs for loading errors."}]
        try:
            image = self._load_image(image_path, image_url, image_base64)
            detection_results = self._object_detector(image)
            objects = [{"box": det['box'], "label": det['label'], "score": round(det['score'], 2)} for det in detection_results]
            return objects
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return [{"error": f"Object detection failed: {e}"}]

    def classify_image(self, image_path: str = None, image_url: str = None, image_base64: str = None, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self._image_classifier: return [{"error": "Image classification model not available. Check logs for loading errors."}]
        try:
            image = self._load_image(image_path, image_url, image_base64)
            predictions = self._image_classifier(image, top_k=top_k)
            categories = [{"label": p['label'], "score": round(p['score'], 2)} for p in predictions]
            return categories
        except Exception as e:
            logger.error(f"Image classification failed: {e}")
            return [{"error": f"Image classification failed: {e}"}]

computer_vision_model_instance = ComputerVisionModel()

class ObjectDetectionTool(BaseTool):
    """Detects objects within an image using an AI model."""
    def __init__(self, tool_name="object_detection"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Detects objects within an image (from path, URL, or base64) and returns a list of detected objects with their confidence and bounding box coordinates using an AI model."

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
            return json.dumps({"error": "AI models for computer vision are not available. Please install 'transformers', 'torch', 'Pillow', 'requests'."})

        detected_objects = computer_vision_model_instance.detect_objects(image_path, image_url, image_base64)
        return json.dumps({"detected_objects": detected_objects}, indent=2)

class ImageClassificationTool(BaseTool):
    """Classifies an image into predefined categories using an AI model."""
    def __init__(self, tool_name="image_classification"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Classifies an image (from path, URL, or base64) into predefined categories and returns the top predicted categories with confidence scores using an AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Optional: The absolute path to the image file.", "default": None},
                "image_url": {"type": "string", "description": "Optional: The URL of the image.", "default": None},
                "image_base64": {"type": "string", "description": "Optional: Base64 encoded image data.", "default": None},
                "top_k": {"type": "integer", "description": "The number of top categories to return.", "default": 3}
            },
            "required": [] # One of the image sources must be provided
        }

    def execute(self, image_path: str = None, image_url: str = None, image_base64: str = None, top_k: int = 3, **kwargs: Any) -> str:
        if not TRANSFORMERS_AVAILABLE:
            return json.dumps({"error": "AI models for computer vision are not available. Please install 'transformers', 'torch', 'Pillow', 'requests'."})

        predicted_categories = computer_vision_model_instance.classify_image(image_path, image_url, image_base64, top_k)
        return json.dumps({"predicted_categories": predicted_categories}, indent=2)