import logging
import json
import os
from typing import List, Dict, Any, Optional

# Suppress INFO messages from transformers and PIL
logging.getLogger('transformers').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

# Deferring imports to handle cases where they might not be installed
try:
    from transformers import pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers or torch library not found. AI annotation tools will be limited.")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("Pillow library not found. Image annotation tools will be limited.")

from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class DataAnnotator:
    """
    An advanced tool for AI-powered data annotation of text and images.
    This class manages the loading of sophisticated models from Hugging Face
    and provides methods to perform real annotation tasks.
    """
    _ner_pipeline = None
    _object_detection_pipeline = None
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataAnnotator, cls).__new__(cls)
            if not TRANSFORMERS_AVAILABLE:
                logger.error("The 'transformers' and 'torch' libraries are required for AI annotation.")
            if not PIL_AVAILABLE:
                logger.error("The 'Pillow' library is required for image processing.")

            if TRANSFORMERS_AVAILABLE and cls._instance._ner_pipeline is None:
                try:
                    logger.info("Initializing NER model (dbmdz/bert-large-cased-finetuned-conll03-english)...")
                    cls._instance._ner_pipeline = pipeline(
                        "ner",
                        model="dbmdz/bert-large-cased-finetuned-conll03-english",
                        aggregation_strategy="simple"
                    )
                    logger.info("NER model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load NER model: {e}")
            
            if TRANSFORMERS_AVAILABLE and PIL_AVAILABLE and cls._instance._object_detection_pipeline is None:
                try:
                    logger.info("Initializing object detection model (facebook/detr-resnet-50)...")
                    cls._instance._object_detection_pipeline = pipeline(
                        "object-detection",
                        model="facebook/detr-resnet-50"
                    )
                    logger.info("Object detection model loaded successfully.")
                except Exception as e:
                    logger.error(f"Failed to load object detection model: {e}")
        return cls._instance

    def annotate_text_ner(self, text: str) -> Dict[str, Any]:
        """
        Performs Named Entity Recognition (NER) on a given text.
        """
        if not TRANSFORMERS_AVAILABLE or self._ner_pipeline is None:
            raise RuntimeError("NER model not available. Check logs for loading errors.")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string.")
            
        try:
            entities = self._ner_pipeline(text)
            formatted_entities = [
                {
                    "entity": entity['entity_group'],
                    "value": entity['word'],
                    "score": round(entity['score'], 4),
                    "start": entity['start'],
                    "end": entity['end']
                } for entity in entities
            ]

            return {
                "original_text": text,
                "annotations": formatted_entities
            }
        except Exception as e:
            logger.error(f"An error occurred during NER annotation: {e}")
            raise RuntimeError(f"Failed to annotate text due to an internal error: {e}")

    def annotate_image_object_detection(self, image_path: str) -> Dict[str, Any]:
        """
        Performs object detection on a given image.
        """
        if not TRANSFORMERS_AVAILABLE or not PIL_AVAILABLE or self._object_detection_pipeline is None:
            raise RuntimeError("Object detection model or Pillow not available. Check logs for loading errors.")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"The image file was not found at '{image_path}'.")

        try:
            with Image.open(image_path) as img:
                # Ensure image is in RGB format, as some models require it
                image_to_process = img.convert("RGB")
            
            objects = self._object_detection_pipeline(image_to_process)

            # Clean up the output for consistency
            formatted_objects = [
                {
                    "label": obj['label'],
                    "score": round(obj['score'], 4),
                    "box": obj['box']  # {'xmin': int, 'ymin': int, 'xmax': int, 'ymax': int}
                } for obj in objects
            ]

            return {
                "image_path": image_path,
                "annotations": formatted_objects
            }
        except Exception as e:
            logger.error(f"An error occurred during object detection: {e}")
            raise RuntimeError(f"Failed to annotate image due to an internal error: {e}")

data_annotator_instance = DataAnnotator()

class AnnotateTextNERTool(BaseTool):
    """Performs Named Entity Recognition (NER) on a given text using an AI model."""
    def __init__(self, tool_name="annotate_text_ner"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Performs Named Entity Recognition (NER) on a given text, identifying and categorizing entities like persons, organizations, and locations."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"text": {"type": "string", "description": "The text to annotate."}},
            "required": ["text"]
        }

    def execute(self, text: str, **kwargs: Any) -> str:
        try:
            results = data_annotator_instance.annotate_text_ner(text)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to annotate text: {e}"})

class AnnotateImageObjectDetectionTool(BaseTool):
    """Performs object detection on a given image using an AI model."""
    def __init__(self, tool_name="annotate_image_object_detection"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Performs object detection on a given image, returning a list of detected objects with their labels, confidence scores, and bounding box coordinates."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"image_path": {"type": "string", "description": "The local file path to the image to annotate."}},
            "required": ["image_path"]
        }

    def execute(self, image_path: str, **kwargs: Any) -> str:
        try:
            results = data_annotator_instance.annotate_image_object_detection(image_path)
            return json.dumps(results, indent=2)
        except Exception as e:
            return json.dumps({"error": f"Failed to annotate image: {e}"})
