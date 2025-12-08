import logging
import json
import random
import os
from typing import List, Dict, Any
from tools.base_tool import BaseTool
from PIL import Image, ImageFilter
import requests
import torch

# Deferring heavy imports
try:
    from diffusers import StableDiffusionPipeline
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    logging.warning("diffusers library not found. Text-to-3D concept generation will not be available.")

logger = logging.getLogger(__name__)

class Generate3DModelConceptFromTextTool(BaseTool):
    """Generates a concept image for a 3D model from a text description using a text-to-image model."""
    _pipe = None

    def __init__(self, tool_name="generate_3d_model_concept_from_text"):
        super().__init__(tool_name=tool_name)
        if Generate3DModelConceptFromTextTool._pipe is None and DIFFUSERS_AVAILABLE:
            self._initialize_pipeline()

    def _initialize_pipeline(self):
        if not torch.cuda.is_available():
            logger.warning("CUDA not available. Text-to-image generation will be very slow on CPU.")
            return

        try:
            logger.info("Initializing Stable Diffusion pipeline for 3D concept generation...")
            Generate3DModelConceptFromTextTool._pipe = StableDiffusionPipeline.from_pretrained(
                "runwayml/stable-diffusion-v1-5",
                torch_dtype=torch.float16,
                safety_checker=None # Disabling for this use case
            ).to("cuda")
            logger.info("Stable Diffusion pipeline loaded.")
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion pipeline: {e}")

    @property
    def description(self) -> str:
        return "Generates a concept image for a 3D model from a text description using a text-to-image AI model. This simulates the visual output of a text-to-3D process."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text_description": {"type": "string", "description": "A textual description of the 3D model concept to generate."},
                "output_path": {"type": "string", "description": "The path to save the generated concept image (e.g., '3d_concept.png')."}
            },
            "required": ["text_description", "output_path"]
        }

    def execute(self, text_description: str, output_path: str, **kwargs: Any) -> str:
        if not self._pipe:
            return json.dumps({"error": "Text-to-image model not available. This tool requires a CUDA-enabled GPU and the 'diffusers' library."})

        try:
            prompt = f"3D model concept art of {text_description}, highly detailed, studio lighting, render, octane render"
            image = self._pipe(prompt).images[0]
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            
            return json.dumps({"message": f"3D model concept image generated and saved to '{os.path.abspath(output_path)}'.", "concept_image_path": os.path.abspath(output_path)}, indent=2)
        except Exception as e:
            logger.error(f"3D model concept generation failed: {e}")
            return json.dumps({"error": f"An error occurred during 3D model concept generation: {e}"})

class GenerateTextureFromImageTool(BaseTool):
    """Generates a stylized texture from an input image."""
    def __init__(self, tool_name="generate_texture_from_image"):
        super().__init__(tool_name=tool_name)

    @property
    def description(self) -> str:
        return "Generates a stylized texture from an input image by applying image processing filters, simulating texture generation."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "The path or URL to the input image for texture generation."},
                "output_path": {"type": "string", "description": "The path to save the generated texture image (e.g., 'stylized_texture.png')."},
                "style_effect": {"type": "string", "enum": ["grayscale", "sepia", "emboss", "sharpen"], "default": "grayscale", "description": "The style effect to apply to the texture."}
            },
            "required": ["image_path", "output_path"]
        }

    def execute(self, image_path: str, output_path: str, style_effect: str = "grayscale", **kwargs: Any) -> str:
        try:
            if image_path.startswith("http"):
                image = Image.open(requests.get(image_path, stream=True, timeout=10).raw).convert("RGB")
            else:
                image = Image.open(image_path).convert("RGB")
            
            processed_image = image
            if style_effect == "grayscale":
                processed_image = image.convert("L")
            elif style_effect == "sepia":
                # Simple sepia effect (approximate)
                processed_image = Image.eval(image, lambda x: x * 0.8 if x < 128 else x * 1.2)
                processed_image = processed_image.convert("RGB")
                r, g, b = processed_image.split()
                r = r.point(lambda i: i * 0.393 + i * 0.769 + i * 0.189)
                g = g.point(lambda i: i * 0.349 + i * 0.686 + i * 0.168)
                b = b.point(lambda i: i * 0.272 + i * 0.534 + i * 0.131)
                processed_image = Image.merge("RGB", (r, g, b))
            elif style_effect == "emboss":
                processed_image = image.filter(ImageFilter.EMBOSS)
            elif style_effect == "sharpen":
                processed_image = image.filter(ImageFilter.SHARPEN)
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            processed_image.save(output_path)
            
            return json.dumps({"message": f"Texture generated with '{style_effect}' effect and saved to '{os.path.abspath(output_path)}'.", "texture_image_path": os.path.abspath(output_path)}, indent=2)
        except Exception as e:
            logger.error(f"Texture generation failed: {e}")
            return json.dumps({"error": f"An error occurred during texture generation: {e}"})