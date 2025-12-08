import os
from PIL import Image
import logging
from typing import Any, Dict, Union
from tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class ImageResizerOptimizerTool(BaseTool):
    def __init__(self, tool_name: str = "image_resizer_optimizer_tool"):
        super().__init__(tool_name)

    @property
    def description(self) -> str:
        return "Resizes, optimizes, or converts images."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform: 'resize', 'optimize', or 'convert'."
                },
                "file_path": {
                    "type": "string",
                    "description": "The absolute path to the input image file."
                },
                "output_path": {
                    "type": "string",
                    "description": "The absolute path to save the processed image."
                },
                "width": {
                    "type": "integer",
                    "description": "The new width for the 'resize' action."
                },
                "height": {
                    "type": "integer",
                    "description": "The new height for the 'resize' action."
                },
                "quality": {
                    "type": "integer",
                    "description": "The quality for the 'optimize' action (1-100).",
                    "default": 85
                },
                "output_format": {
                    "type": "string",
                    "description": "The target format for the 'convert' action (e.g., 'PNG', 'JPEG')."
                }
            },
            "required": ["action", "file_path", "output_path"]
        }

    def _check_paths(self, file_path: str, output_path: str = None):
        """
        Checks if input and output paths are valid.
        """
        if not os.path.isabs(file_path):
            raise ValueError(f"Input file_path must be an absolute path: '{file_path}'")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at '{file_path}'")
        if output_path and not os.path.isabs(output_path):
            raise ValueError(f"Output output_path must be an absolute path: '{output_path}'")

    def resize_image(self, file_path: str, width: int, height: int, output_path: str) -> str:
        """
        Resizes an image.
        """
        self._check_paths(file_path, output_path)
        if not all([width, height]):
            raise ValueError("'width' and 'height' are required for resize action.")

        with Image.open(file_path) as img:
            resized_img = img.resize((int(width), int(height)))
            resized_img.save(output_path)
        self.logger.info(f"Resized image to {width}x{height} and saved to '{output_path}'.")
        return f"Image resized to {width}x{height} and saved to '{output_path}'."

    def optimize_image(self, file_path: str, output_path: str, quality: int = 85) -> str:
        """
        Optimizes an image.
        """
        self._check_paths(file_path, output_path)
        
        with Image.open(file_path) as img:
            img.save(output_path, optimize=True, quality=quality)
        self.logger.info(f"Optimized image and saved to '{output_path}' with quality {quality}.")
        return f"Image optimized and saved to '{output_path}' with quality {quality}."

    def convert_image(self, file_path: str, output_path: str, output_format: str) -> str:
        """
        Converts an image to a different format.
        """
        self._check_paths(file_path, output_path)
        if not output_format:
            raise ValueError("'format' is required for convert action.")

        with Image.open(file_path) as img:
            img.save(output_path, format=output_format)
        self.logger.info(f"Converted image to {output_format} and saved to '{output_path}'.")
        return f"Image converted to {output_format} and saved to '{output_path}'."

    def execute(self, action: str, file_path: str, output_path: str, **kwargs: Dict[str, Any]) -> str:
        """
        Executes an image resizing/optimization/conversion action.

        Args:
            action: The action to perform: "resize", "optimize", or "convert".
            file_path: The absolute path to the file or directory to process.
            **kwargs: Additional arguments for specific actions (e.g., width, height, quality, format, output_path).

        Returns:
            A string indicating the result of the operation.
        """
        action = action.lower()
        try:
            if action == "resize":
                return self.resize_image(file_path, kwargs.get("width"), kwargs.get("height"), output_path)
            elif action == "optimize":
                return self.optimize_image(file_path, output_path, kwargs.get("quality", 85))
            elif action == "convert":
                return self.convert_image(file_path, output_path, kwargs.get("output_format"))
            else:
                raise ValueError(f"Invalid action '{action}'. Supported actions are 'resize', 'optimize', or 'convert'.")
        except (ValueError, FileNotFoundError, IOError) as e:
            self.logger.error(e)
            raise e
        except Exception as e:
            self.logger.error(f"An unexpected error occurred: {e}")
            raise e