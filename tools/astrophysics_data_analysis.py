import logging
import json
import random
import numpy as np
import requests
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from PIL import Image

# Deferring heavy imports
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers library not found. Celestial object identification will not be available.")

logger = logging.getLogger(__name__)

# Using the publicly available DEMO_KEY for the NASA API.
# For higher rate limits, a personal key would be needed.
NASA_API_KEY = "DEMO_KEY"

class FetchAndAnalyzeAPODTool(BaseTool):
    """Fetches and provides data for the NASA Astronomy Picture of the Day (APOD)."""
    def __init__(self, tool_name="fetch_and_analyze_apod"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Fetches and returns the NASA Astronomy Picture of the Day (APOD) data, including image URL and explanation, for a specified date."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"date": {"type": "string", "description": "The date to fetch the APOD for, in YYYY-MM-DD format."}},
            "required": ["date"]
        }

    def execute(self, date: str, **kwargs: Any) -> str:
        try:
            url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={date}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            # Ensure we only return relevant, serializable data
            filtered_data = {
                "title": data.get("title"),
                "date": data.get("date"),
                "explanation": data.get("explanation"),
                "url": data.get("url"),
                "media_type": data.get("media_type")
            }
            return json.dumps(filtered_data, indent=2)
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch APOD data for date {date}: {e}")
            return json.dumps({"error": f"Failed to fetch APOD data: {e}"})

class IdentifyCelestialObjectsTool(BaseTool):
    """Identifies celestial objects from an image using an AI model."""
    _classifier = None

    def __init__(self, tool_name="identify_celestial_objects"):
        super().__init__(tool_name=tool_name)

    def _get_classifier(self):
        """Lazily loads the image classification model on first use."""
        if self._classifier is None:
            if not TRANSFORMERS_AVAILABLE:
                logger.error("transformers library not found. Celestial object identification will not be available.")
                self._classifier = "unavailable"
            else:
                try:
                    logger.info("Initializing image classification model for astrophysics (google/vit-base-patch16-224)...")
                    self._classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
                    logger.info("Image classification model loaded.")
                except Exception as e:
                    logger.error(f"Failed to load image classification model: {e}")
                    self._classifier = "unavailable"
        
        return self._classifier if self._classifier != "unavailable" else None

    @property
    def description(self) -> str:
        return "Identifies celestial objects from an image URL using a Vision Transformer (ViT) AI model."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"image_url": {"type": "string", "description": "The URL of the astronomical image to analyze."}},
            "required": ["image_url"]
        }

    def execute(self, image_url: str, **kwargs: Any) -> str:
        classifier = self._get_classifier()
        if not classifier:
            return json.dumps({"error": "Image classification model is not available. Please ensure 'transformers' and 'torch' are installed and check logs for errors."})
        
        try:
            image = Image.open(requests.get(image_url, stream=True, timeout=10).raw)
            predictions = classifier(image)
            # The model is general-purpose, so the labels are just suggestions.
            report = {
                "image_url": image_url,
                "model_predictions": [
                    {"label": p["label"], "confidence": round(p["score"], 2)} for p in predictions
                ],
                "summary": f"The model's top prediction for the object in the image is '{predictions[0]['label']}'."
            }
            return json.dumps(report, indent=2)
        except Exception as e:
            logger.error(f"Failed to process image from URL {image_url}: {e}")
            return json.dumps({"error": f"Failed to process image: {e}"})

class SearchForExoplanetTransitsTool(BaseTool):
    """Simulates searching for exoplanet transits in a light curve."""
    def __init__(self, tool_name="search_for_exoplanet_transits"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Simulates the analysis of a stellar light curve (time-series data) to search for the periodic dips caused by exoplanet transits."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "num_data_points": {"type": "integer", "description": "Number of data points to simulate in the light curve.", "default": 1000},
                "inject_transit": {"type": "boolean", "description": "Whether to inject a simulated transit signal into the data.", "default": True}
            },
            "required": []
        }

    def execute(self, num_data_points: int = 1000, inject_transit: bool = True, **kwargs: Any) -> str:
        # Generate a mock light curve with some noise
        time = np.linspace(0, 100, num_data_points)
        flux = np.random.normal(loc=1.0, scale=0.005, size=num_data_points)
        
        if inject_transit:
            # Add a simulated transit signal
            transit_start = random.randint(100, num_data_points - 100)  # nosec B311
            transit_duration = random.randint(20, 50)  # nosec B311
            transit_depth = random.uniform(0.01, 0.04)  # nosec B311
            flux[transit_start : transit_start + transit_duration] -= transit_depth

        # A simple transit detection algorithm: find points significantly below the mean
        mean_flux = np.mean(flux)
        std_flux = np.std(flux)
        # A 3-sigma event is often considered significant
        detection_threshold = mean_flux - 3 * std_flux
        potential_transit_indices = np.where(flux < detection_threshold)[0]
        
        report = {
            "data_points_analyzed": num_data_points,
            "mean_flux": f"{mean_flux:.4f}",
            "flux_std_dev": f"{std_flux:.4f}",
            "detection_threshold": f"{detection_threshold:.4f}",
            "potential_transit_events_detected": len(potential_transit_indices),
            "transit_indices_sample": potential_transit_indices.tolist()[:10]
        }
        return json.dumps(report, indent=2)