import logging
import os
import random
from typing import Dict, Any
from tools.base_tool import BaseTool
from PIL import Image

logger = logging.getLogger(__name__)

class VirtualTryOnTool(BaseTool):
    """
    A tool to simulate a virtual try-on experience by overlaying an item image onto a user image.
    """
    def __init__(self, tool_name: str = "virtual_try_on_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Simulates virtual try-on by overlaying an item image onto a user's image."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "user_image_path": {"type": "string", "description": "The local file path to the user's image."},
                "item_image_path": {"type": "string", "description": "The local file path to the item's image."},
                "output_image_path": {"type": "string", "description": "The local file path to save the composite image."},
                "opacity": {
                    "type": "number",
                    "description": "Opacity of the item image overlay (0.0 to 1.0).",
                    "default": 0.7
                }
            },
            "required": ["user_image_path", "item_image_path", "output_image_path"]
        }

    def execute(self, user_image_path: str, item_image_path: str, output_image_path: str, opacity: float = 0.7, **kwargs: Any) -> Dict:
        """
        Simulates a virtual try-on by overlaying an item image onto a user image.
        """
        try:
            if not os.path.exists(user_image_path):
                raise FileNotFoundError(f"User image not found at '{user_image_path}'.")
            if not os.path.exists(item_image_path):
                raise FileNotFoundError(f"Item image not found at '{item_image_path}'.")
            
            if not (0.0 <= opacity <= 1.0):
                raise ValueError("Opacity must be between 0.0 and 1.0.")

            logger.info(f"Simulating try-on: overlaying '{item_image_path}' on '{user_image_path}'.")

            # Open images
            user_img = Image.open(user_image_path).convert("RGBA")
            item_img = Image.open(item_image_path).convert("RGBA")

            # Resize item image to fit user image (simple scaling for simulation)
            # In a real scenario, this would involve more sophisticated placement and resizing
            item_img = item_img.resize(user_img.size)

            # Create a transparent overlay for the item
            alpha = item_img.split()[-1]
            alpha = Image.eval(alpha, lambda x: x * opacity)
            item_img.putalpha(alpha)

            # Composite images
            composite_img = Image.alpha_composite(user_img, item_img)

            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
            composite_img.save(output_image_path)

            return {
                "message": f"Virtual try-on simulated successfully. Composite image saved to '{output_image_path}'.",
                "output_image_path": output_image_path
            }

        except Exception as e:
            logger.error(f"An error occurred in VirtualTryOnTool: {e}")
            return {"error": str(e)}