import logging
import json
import random
import numpy as np
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from PIL import Image
import requests

# Deferring the import of transformers to avoid loading it if not needed
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Artifact identification will not be available.")

logger = logging.getLogger(__name__)

# --- Geophysical Data Simulation ---
def generate_geophysical_data(grid_size: int = 50, num_anomalies: int = 3) -> np.ndarray:
    """Generates a grid of simulated geophysical data with anomalies."""
    data = np.random.normal(loc=20, scale=5, size=(grid_size, grid_size))
    for _ in range(num_anomalies):
        x, y = random.randint(0, grid_size - 5), random.randint(0, grid_size - 5)  # nosec B311
        size = random.randint(2, 5)  # nosec B311
        data[x:x+size, y:y+size] += random.uniform(20, 40) # Add a strong signal anomaly  # nosec B311
    return np.round(data, 2)

# --- Artifact Identification ---
class ArtifactIdentifier:
    """Uses an image classification model to identify archaeological artifacts."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ArtifactIdentifier, cls).__new__(cls)
            cls._instance.classifier = None
            if TRANSFORMERS_AVAILABLE:
                try:
                    logger.info("Initializing image classification model for artifact identification...")
                    cls._instance.classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
                    logger.info("Image classification model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load image classification model: {e}")
            
            cls._instance.artifact_db = {
                "pottery": {"estimated_age_range_bp": (500, 8000), "description": "Fragments of ceramic vessels, often decorated."},
                "arrowhead": {"estimated_age_range_bp": (200, 15000), "description": "A projectile point, usually made of stone, used for hunting or warfare."},
                "coin": {"estimated_age_range_bp": (100, 2700), "description": "A piece of hard material, usually metal, used as a medium of exchange."},
                "default": {"estimated_age_range_bp": ("N/A", "N/A"), "description": "Unclassified artifact. Requires expert review."}
            }
        return cls._instance

    def identify(self, image_path: str) -> Dict[str, Any]:
        if not self.classifier:
            return {"error": "Image classification model is not available. Please ensure 'transformers' and 'torch' are installed."}
        
        try:
            if image_path.startswith("http"):
                image = Image.open(requests.get(image_path, stream=True, timeout=10).raw)
            else:
                image = Image.open(image_path)
            
            predictions = self.classifier(image)
            top_prediction_label = predictions[0]['label'].lower()
            
            # Simple keyword matching to map model output to our artifact DB
            identified_type = "default"
            if any(k in top_prediction_label for k in ["pot", "vase", "jug"]):
                identified_type = "pottery"
            elif "arrowhead" in top_prediction_label:
                identified_type = "arrowhead"
            elif "coin" in top_prediction_label:
                identified_type = "coin"
            
            info = self.artifact_db[identified_type]
            return {
                "identified_type": identified_type,
                "model_prediction": top_prediction_label,
                "confidence": round(predictions[0]['score'], 2),
                "estimated_age_range_bp": info["estimated_age_range_bp"],
                "description": info["description"]
            }
        except FileNotFoundError:
            return {"error": f"Image file not found at '{image_path}'."}
        except Exception as e:
            logger.error(f"Failed to process image '{image_path}': {e}")
            return {"error": f"Failed to process image: {e}"}

artifact_identifier_instance = ArtifactIdentifier()

class AnalyzeGeophysicalDataTool(BaseTool):
    """Analyzes a simulated grid of geophysical data to find anomalies."""
    def __init__(self, tool_name="analyze_geophysical_data"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes a simulated grid of geophysical data to identify anomalies that may indicate buried features."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "grid_size": {"type": "integer", "description": "The size of the grid to simulate.", "default": 50},
                "num_anomalies_to_simulate": {"type": "integer", "description": "The number of anomalies to inject into the data.", "default": 3}
            },
            "required": []
        }

    def execute(self, grid_size: int = 50, num_anomalies_to_simulate: int = 3, **kwargs: Any) -> str:
        data = generate_geophysical_data(grid_size, num_anomalies_to_simulate)
        # Anomalies are values significantly higher than the mean
        threshold = np.mean(data) + 2 * np.std(data)
        
        anomalies = np.argwhere(data > threshold)
        
        report = {
            "grid_size": grid_size,
            "analysis_threshold": round(threshold, 2),
            "anomalies_found": anomalies.shape[0],
            "anomaly_coordinates": anomalies.tolist()[:10] # Show first 10 for brevity
        }
        return json.dumps(report, indent=2)

class IdentifyArchaeologicalArtifactTool(BaseTool):
    """Identifies an archaeological artifact from an image."""
    def __init__(self, tool_name="identify_archaeological_artifact"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Identifies a potential archaeological artifact from an image file or URL using an image classification model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"image_path": {"type": "string", "description": "The local path or URL to the artifact image."}},
            "required": ["image_path"]
        }

    def execute(self, image_path: str, **kwargs: Any) -> str:
        result = artifact_identifier_instance.identify(image_path)
        return json.dumps(result, indent=2)