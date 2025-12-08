import logging
import json
import numpy as np
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from PIL import Image, ImageFilter
import requests
import torch
import os

# Deferring heavy imports
try:
    from diffusers import StableDiffusionInpaintingPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logging.warning("diffusers library not found. AI inpainting tool will not be available.")

logger = logging.getLogger(__name__)

class AnalyzeArtworkDamageTool(BaseTool):
    """Analyzes an image of an artwork to simulate damage detection."""
    def __init__(self, tool_name="analyze_artwork_damage"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Analyzes an artwork image to simulate the detection of damages like cracks and discoloration using basic image processing."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"image_path": {"type": "string", "description": "The local path or URL to the artwork image."}},
            "required": ["image_path"]
        }

    def execute(self, image_path: str, **kwargs: Any) -> str:
        try:
            if image_path.startswith("http"):
                image = Image.open(requests.get(image_path, stream=True, timeout=10).raw)
            else:
                image = Image.open(image_path)
            
            grayscale_image = image.convert("L")
        except Exception as e:
            return json.dumps({"error": f"Failed to open or process image: {e}"})

        # Simulate crack detection using an edge detection filter
        edges = grayscale_image.filter(ImageFilter.FIND_EDGES)
        edge_pixels = np.array(edges)
        # Calculate a metric for "crack density"
        crack_metric = np.sum(edge_pixels > 50) / (edge_pixels.size)

        # Simulate discoloration by analyzing the standard deviation of the color histogram
        histogram = grayscale_image.histogram()
        discoloration_metric = np.std(histogram)

        damage_report = {
            "image_analyzed": image_path,
            "crack_detection": {
                "crack_density_metric": f"{crack_metric:.4f}",
                "assessment": "Significant cracking patterns detected." if crack_metric > 0.01 else "Minor cracking or texture detected."
            },
            "discoloration_analysis": {
                "color_std_dev": f"{discoloration_metric:.2f}",
                "assessment": "Significant color variation or discoloration detected." if discoloration_metric > 1000 else "Color variation appears normal."
            }
        }
        
        return json.dumps(damage_report, indent=2)

class SuggestRestorationTechniquesTool(BaseTool):
    """Suggests restoration techniques based on a damage analysis report."""
    def __init__(self, tool_name="suggest_restoration_techniques"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Suggests professional restoration techniques based on a damage analysis report."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {"damage_report_json": {"type": "string", "description": "The JSON output from the AnalyzeArtworkDamageTool."}},
            "required": ["damage_report_json"]
        }

    def execute(self, damage_report_json: str, **kwargs: Any) -> str:
        try:
            report = json.loads(damage_report_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid JSON format for the damage report."})

        suggestions = []
        if "Significant cracking" in report.get("crack_detection", {}).get("assessment", ""):
            suggestions.append("For significant cracks, consider structural consolidation by an expert, followed by careful infilling with a stable, reversible material.")
        if "Significant discoloration" in report.get("discoloration_analysis", {}).get("assessment", ""):
            suggestions.append("For significant discoloration, a gentle surface cleaning by a conservator is recommended. This may be followed by varnish removal and inpainting if necessary.")
        
        if not suggestions:
            suggestions.append("Damage appears to be minor. Condition monitoring and ensuring a stable environment (humidity, temperature, light) are recommended.")

        return json.dumps({"restoration_suggestions": suggestions}, indent=2)

class InpaintDamagedArtworkTool(BaseTool):
    """Uses an AI inpainting model to restore a damaged artwork."""
    _pipe = None

    def __init__(self, tool_name="inpaint_damaged_artwork"):
        super().__init__(tool_name=tool_name)
        if InpaintDamagedArtworkTool._pipe is None and DIFFUSERS_AVAILABLE:
            self._initialize_pipeline()

    def _initialize_pipeline(self):
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. AI inpainting will be very slow on CPU.")
            return

        try:
            logger.info("Initializing Stable Diffusion inpainting model...")
            InpaintDamagedArtworkTool._pipe = StableDiffusionInpaintingPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting",
                torch_dtype=torch.float16,
                safety_checker=None # Disabling for this use case
            ).to("cuda")
            logger.info("Inpainting model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion inpainting model: {e}")

    @property
    def description(self) -> str:
        return "Uses a Stable Diffusion inpainting model to 'restore' a damaged artwork. Requires the original image, a mask image identifying the damage, and a descriptive prompt."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "The path or URL to the damaged artwork image."},
                "mask_image_path": {"type": "string", "description": "A path or URL to a black and white mask image. White areas indicate damage to be inpainted."},
                "prompt": {"type": "string", "description": "A detailed description of the content to be generated in the damaged areas (e.g., 'a 19th-century oil painting of a sky with clouds')."},
                "output_path": {"type": "string", "description": "The path to save the restored image."}
            },
            "required": ["image_path", "mask_image_path", "prompt", "output_path"]
        }

    def execute(self, image_path: str, mask_image_path: str, prompt: str, output_path: str, **kwargs: Any) -> str:
        if not InpaintDamagedArtworkTool._pipe:
            return json.dumps({"error": "Inpainting model is not available. This tool requires a CUDA-enabled GPU and the 'diffusers' library."})

        try:
            init_image = Image.open(requests.get(image_path, stream=True, timeout=10).raw if image_path.startswith("http") else image_path).convert("RGB").resize((512, 512))
            mask_image = Image.open(requests.get(mask_image_path, stream=True, timeout=10).raw if mask_image_path.startswith("http") else mask_image_path).convert("RGB").resize((512, 512))
            
            restored_image = InpaintDamagedArtworkTool._pipe(prompt=prompt, image=init_image, mask_image=mask_image).images[0]
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            restored_image.save(output_path)
            
            return json.dumps({"message": f"Restored image successfully generated and saved to '{os.path.abspath(output_path)}'."}, indent=2)
        except Exception as e:
            logger.error(f"Failed to perform inpainting: {e}")
            return json.dumps({"error": f"An error occurred during inpainting: {e}"})